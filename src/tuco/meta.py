"""Meta class to validate FSM implementations on parsing time."""
import collections

from tuco.properties import BaseState, Event, FinalState


class FSMBase(type):
    """Metaclass to generate all FSM models."""

    def __new__(mcs, name, bases, attributes):
        """Make sure that we don't have broken state machines and hide some stuff from users."""
        super_new = super(FSMBase, mcs).__new__
        module = attributes.pop('__module__', None)
        new_class = super_new(mcs, name, bases, {'__module__': module})
        for name, value in attributes.items():
            if isinstance(value, BaseState):
                mcs._create_state(new_class, name, value)
            else:
                setattr(new_class, name, value)
                if callable(value):
                    for event_name in ('_on_change_event', '_on_error_event'):
                        if getattr(value, event_name, False):
                            setattr(new_class, event_name, value)

        mcs._validate_timeouts(new_class)
        mcs._validate_errors(new_class)
        mcs._validate_events(new_class)
        return new_class

    @staticmethod
    def _create_state(new_class, name, value) -> None:
        """Create a state hidden in new class."""
        if new_class._states is None:
            new_class._states = {}

        states = new_class._states
        if name in states:
            raise RuntimeError('Duplicated states are not allowed {!r} {!r}'.format(new_class, name))

        states[name] = value

    @staticmethod
    def _validate_timeouts(new_class) -> None:
        """Validate all timeouts."""
        states = new_class._states
        if states is None:
            return
        for name, state in states.items():
            if isinstance(state, FinalState):
                continue
            if state.timeout and state.timeout.target_state not in states:
                raise RuntimeError('Invalid timeout target state, {!r} not found in {!r}.'.format(
                    state.timeout.target_state, new_class))
            if name == new_class.initial_state and state.timeout:
                raise RuntimeError('Initial state cannot have a timeout {!r} {!r}.'.format(new_class, state))

    @staticmethod
    def _validate_events(new_class) -> None:
        """Make a pre-validation on events to fail fast."""
        states = new_class._states
        if states is None:
            return
        for parent_state_name, parent_state in states.items():
            if isinstance(parent_state, FinalState):
                continue

            counter = collections.Counter([event.event_name for event in parent_state.events])
            duplicated_events = [(element, amount) for element, amount in counter.items() if amount > 1]
            if duplicated_events:
                raise RuntimeError('Duplicated events found in state {} {!r} {}'.format(parent_state_name, parent_state,
                                                                                        duplicated_events))

            for event in parent_state.events:
                FSMBase._validate_event(event, parent_state_name, parent_state, new_class)

    @staticmethod
    def _validate_event(event, parent_state_name, parent_state, new_class) -> None:
        """Validate an event."""
        if not isinstance(event, Event):
            raise RuntimeError('Invalid event class when parsing state {} in {!r}'.format(
                parent_state_name, new_class))

        if event.target_state not in getattr(new_class, '_states', {}):
            raise RuntimeError('Target state not found {} in {!r} ({})'.format(
                event.target_state, parent_state, parent_state_name))

    @staticmethod
    def _validate_errors(new_class) -> None:
        """Walk through states and events to check if events are not going to dead ends."""
        states = new_class._states
        if states is None:
            return
        for _, state in states.items():
            if isinstance(state, FinalState):
                continue

            if state.error:
                FSMBase._validate_error(new_class, state.error)

            for event in state.events:
                if event.error:
                    FSMBase._validate_error(new_class, event.error)

    @staticmethod
    def _validate_error(new_class, error) -> None:
        """Check if a declared error is properly configured."""
        states = new_class._states
        if not states or error.target_state not in states:
            raise RuntimeError('Could not find target state {} inside {!r}'.format(error.target_state, new_class))
