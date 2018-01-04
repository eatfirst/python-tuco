"""Basic lock interface."""
from tuco.exceptions import TucoDoNotLockError


class BaseLock:
    """Common lock functions."""

    def __init__(self, fsm, id_field):
        """Hold the fsm and it's id field."""
        self.fsm = fsm
        self.id_field = id_field

    @property
    def hash_key(self) -> str:
        """Generate a hash key to be used when locking an object."""
        primary_key = getattr(self.fsm.container_object, self.id_field, None)
        if primary_key:
            return 'fsm_{}_pk_{}'.format(self.fsm.__class__.__name__, primary_key)

        raise TucoDoNotLockError()

    def lock(self) -> bool:
        """Implement lock."""
        raise NotImplementedError()

    def unlock(self) -> bool:
        """Implement unlock."""
        raise NotImplementedError()
