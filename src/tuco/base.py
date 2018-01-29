"""Base classes to be used in FSM."""
import copy
from datetime import datetime
from typing import Dict, Iterator, List, Tuple, Type  # noqa

import pytz

from tuco.exceptions import (TucoAlreadyLockedError, TucoEventNotFoundError, TucoInvalidStateChangeError,
                             TucoInvalidStateHolderError)
from tuco.locks import MemoryLock
from tuco.locks.base import BaseLock  # noqa
from tuco.meta import FSMBase
from tuco.properties import Event, FinalState, State, Timeout

__all__ = ('FSM', )

mockable_utcnow = datetime.utcnow  # Easier to write tests


class FSM(metaclass=FSMBase):
    """Class that handle event transitions.

    Your state machines should extend from this.
    """

    #: The default initial state is "new" but can be overridden
    initial_state = 'new'
    state_attribute = 'current_state'
    date_attribute = 'current_state_date'
    id_field = 'id'

    fatal_state = 'fatal_error'

    lock_class = MemoryLock  # type: Type[BaseLock]
    _states = None  # type: Dict[str, State]

    def __init__(self, container_object) -> None:
        """Initialize the container object with the initial state."""
        self.container_object = container_object
        for field in (self.state_attribute, self.date_attribute, self.id_field):
            if not hasattr(container_object, field):
                raise TucoInvalidStateHolderError('Required field {!r} not found inside {!r}.'.format(
                    field, container_object))
        if self.current_state is None:
            self.current_state = self.initial_state

        self.lock = self.lock_class(self, self.id_field)

    def __enter__(self) -> 'FSM':
        """Lock the state machine."""
        self.lock.lock()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """If TucoAlreadyLockedError did not throw, unlock the machine."""
        if exc_type and issubclass(exc_type, TucoAlreadyLockedError):
            return

        self.lock.unlock()

    def __repr__(self) -> str:
        """Basic representation."""
        return '<{} - current_state {!r} with holder {} - ID {!r}>'.format(
            self.__class__.__name__, self.current_state, self.container_object.__class__.__name__,
            getattr(self.container_object, self.id_field))

    @property
    def current_time(self) -> datetime:
        """Return utcnow and should be extended if you care about time zone or something else."""
        return mockable_utcnow()

    @property
    def current_state_date(self) -> datetime:
        """Return current date stored in object."""
        return getattr(self.container_object, self.date_attribute)

    @property
    def current_state(self) -> str:
        """Return the current state stored in object."""
        return getattr(self.container_object, self.state_attribute)

    @current_state.setter
    def current_state(self, new_state) -> None:
        """Set a state on container object."""
        call_on_change = bool(self.current_state)
        old_state = copy.copy(self.container_object)
        if new_state != self.fatal_state:
            if not self.state_allowed(new_state):
                raise TucoInvalidStateChangeError('Old state {!r}, new state {!r}.'.format(self.current_state,
                                                                                           new_state))

            setattr(self.container_object, self.state_attribute, new_state)
            setattr(self.container_object, self.date_attribute, self.current_time)
            for command in self.current_state_instance.on_enter:
                command(self.container_object)
        else:
            setattr(self.container_object, self.state_attribute, new_state)
            setattr(self.container_object, self.date_attribute, self.current_time)

        if call_on_change:
            self._call_on_change(old_state, self.container_object)

    def state_allowed(self, state_name) -> bool:
        """Check if the transition to the new state is allowed."""
        if self.current_state is None and state_name == self.initial_state:
            return True

        if isinstance(self.current_state_instance, FinalState):
            return False

        if self.current_state_instance.timeout and self.current_state_instance.timeout.target_state == state_name:
            return True

        if any([event for event in self.possible_events if event.target_state == state_name]):
            return True

        current_state = self.current_state_instance
        if current_state.error and current_state.error.target_state == state_name:
            return True

        for event in current_state.events:
            if event.error and event.error.target_state == state_name:
                return True

        return False

    @property
    def current_state_instance(self) -> State:
        """Return the current `State` instance."""
        return self._states[self.current_state]

    @property
    def possible_events(self) -> List[Event]:
        """Return all possible events for the current state."""
        return self.possible_events_from_state(self.current_state)

    @classmethod
    def possible_events_from_state(cls, state_name) -> List[Event]:
        """Return all possible events from a specific state.

        :param state_name: State to check
        """
        state = cls._states[state_name]
        return getattr(state, 'events', [])

    def _get_event(self, event_name) -> Event:
        """Get an event inside current state based on it's name."""
        for event in self.possible_events:
            if event.event_name == event_name:
                return event

        raise TucoEventNotFoundError('Event {!r} not found in {!r} on current state {!r}'.format(
            event_name, [event.event_name for event in self.possible_events], self.current_state))

    def event_allowed(self, event_name) -> bool:
        """Check if is possible to run an event.

        :param event_name: Event to check.
        """
        try:
            self._get_event(event_name)
        except TucoEventNotFoundError:
            return False

        return True

    def _trigger_error(self, event) -> None:
        """Search for an error handler inside event, and then inside state."""
        if event.error:
            error = event.error
        else:
            error = self._states[self.current_state].error
            if not error:
                return

        for command in error.commands:
            command(self.container_object)

        self.current_state = error.target_state

    def trigger(self, event_name, *args, **kwargs) -> bool:
        """Trigger an event and call its commands with specified arguments..

        :param event_name: Event to execute.
        """
        event = self._get_event(event_name)
        for command in event.commands:
            try:
                return_value = command(self.container_object, *args, **kwargs)
            except Exception as e:
                self._call_on_error(e, event.target_state)
                raise

            if not return_value:
                self._trigger_error(event)
                return False

        self.current_state = event.target_state

        return True

    def trigger_timeout(self) -> bool:
        """Trigger timeout if it's possible."""
        timeout = self.current_state_instance.timeout

        if not timeout:
            return False

        if datetime.utcnow().replace(tzinfo=pytz.UTC) < (self.current_state_date + timeout.timedelta):
            return False

        for command in timeout.commands:
            try:
                command(self.container_object)
            except Exception as e:
                self._call_on_error(e, timeout.target_state)
                raise

        self.current_state = timeout.target_state
        return True

    @classmethod
    def get_all_states(cls) -> Dict[str, State]:
        """List all states for this state machine."""
        return cls._states

    @classmethod
    def get_all_timeouts(cls) -> Iterator[Tuple[str, Timeout]]:
        """List all configured timeouts for this state machine."""
        for state_name, state in cls._states.items():
            if isinstance(state, FinalState) or not state.timeout:
                continue
            yield (state_name, state.timeout)

    @classmethod
    def get_all_finals(cls) -> Iterator[FinalState]:
        """List all configured final states for this state machine."""
        for state_name, state in cls._states.items():
            if isinstance(state, FinalState):
                yield state_name

    def _call_on_change(self, old_state, new_state) -> None:
        """If on_change function exists, call it.

        :param old_state: A shallow copy of the holder object.
        :param new_state: The changed version of the object holder.
        """
        function = getattr(self, '_on_change_event', None)
        if function:
            function(old_state, new_state)

    def _call_on_error(self, exception, new_state) -> None:
        """If on_error function exists, call it."""
        function = getattr(self, '_on_error_event', None)
        if function:
            function(self.current_state, new_state, exception)

    @classmethod
    def generate_graph(cls, file_format='svg') -> str:
        """Generate a SVG graph."""
        from .graph_builder import generate_from_class
        return generate_from_class(cls, file_format)
