"""FSM Exceptions."""


class TucoException(Exception):
    """Base FSM Exception."""

    pass


class TucoEventNotFoundError(TucoException):
    """Event not found."""

    pass


class TucoInvalidStateChangeError(TucoException):
    """In case someone try to change to an invalid state."""

    pass


class TucoInvalidStateHolderError(TucoException):
    """In case the state holder do not have all required attributes."""

    pass


class TucoDoNotLockError(TucoException):
    """In case we don't have and ID, means that the model is new."""

    pass


class TucoAlreadyLockedError(TucoException):
    """When an object is already locked."""

    pass


class TucoEmptyFSMError(TucoException):
    """FSM has no state defined."""

    pass
