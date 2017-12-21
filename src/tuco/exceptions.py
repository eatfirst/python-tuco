"""FSM Exceptions."""


class TucoException(Exception):
    """Base FSM Exception."""

    pass


class TucoEventNotFound(TucoException):
    """Event not found."""

    pass


class TucoInvalidStateChange(TucoException):
    """In case someone try to change to an invalid state."""

    pass


class TucoInvalidStateHolder(TucoException):
    """In case the state holder do not have all required attributes."""

    pass


class TucoDoNotLock(TucoException):
    """In case we don't have and ID, means that the model is new."""

    pass


class TucoAlreadyLocked(TucoException):
    """When an object is already locked."""

    pass


class TucoEmptyFSM(TucoException):
    """FSM has no state defined."""

    pass
