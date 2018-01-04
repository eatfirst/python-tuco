from threading import RLock
from typing import Dict  # noqa

from tuco.exceptions import TucoAlreadyLockedError, TucoDoNotLockError

from .base import BaseLock


class MemoryLock(BaseLock):
    """Simple memory lock implementation."""

    global_lock = RLock()
    locks = {}  # type: Dict[str, str]

    def lock(self) -> bool:
        """Lock an object."""
        try:
            hash_key = self.hash_key
        except TucoDoNotLockError:
            return True

        with self.global_lock:
            if hash_key in self.locks:
                raise TucoAlreadyLockedError()
            self.locks[hash_key] = 'locked'
            return True

    def unlock(self) -> bool:
        """Unlock an object."""
        try:
            hash_key = self.hash_key
        except TucoDoNotLockError:
            return True

        with self.global_lock:
            try:
                del self.locks[hash_key]
            except KeyError:
                pass
            return True
