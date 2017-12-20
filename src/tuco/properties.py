"""FSM Descriptors."""
from typing import Callable, List, Optional

TucoCallback = Callable[[object], bool]


class BaseState:
    """Base state."""

    pass


class State(BaseState):
    """Describe the flow of a state."""

    def __init__(self, events: Optional[List['Event']]=None, error: Optional['Error']=None,
                 timeout: Optional['Timeout']=None, on_enter: Optional[List[TucoCallback]]=None) -> None:
        """Initialize default values."""
        self.events = events or []  # type: List[Event]
        self.error = error
        self.timeout = timeout
        self.on_enter = on_enter or []  # type: List[TucoCallback]


class FinalState(BaseState):
    """Dumb class to mark final states."""

    def __init__(self, on_enter: Optional[List[TucoCallback]]=None) -> None:
        """Initialize default values."""
        self.timeout = None
        self.on_enter = on_enter or []  # type: List[TucoCallback]


class Event:
    """Describe an event."""

    def __init__(self, event_name, target_state, commands=None, error=None) -> None:
        """Initialize default values."""
        self.event_name = event_name
        self.target_state = target_state
        self.commands = commands or []
        self.error = error

    def __repr__(self) -> str:
        """Basic representation."""
        return '<FSM Event {!r} with target state {!r}>'.format(self.event_name, self.target_state)


class Error:
    """Error handling."""

    def __init__(self, target_state, commands=None) -> None:
        """Initialize default values."""
        self.target_state = target_state
        self.commands = commands or []


class Timeout:
    """Timeout class."""

    def __init__(self, timedelta, target_state, commands=None) -> None:
        """Initialize default values."""
        self.timedelta = timedelta
        self.target_state = target_state
        self.commands = commands or []
