from typing import Optional  # noqa

from tuco.exceptions import TucoAlreadyLockedError, TucoDoNotLockError

from .base import BaseLock


class RedisLock(BaseLock):
    """Redis lock.

    This class should be extended and provided with timeout and a redis connection pool as there is no way to know
    where the user stores this data, it can be inside some config or a flask app for example.
    """

    def __init__(self, lock_timeout, redis_connection, *args, **kwargs) -> None:
        """Start the lock with default timeout."""
        super().__init__(*args, **kwargs)
        from redis.lock import LuaLock  # noqa
        self._lock = None  # type: Optional[LuaLock]
        self.lock_timeout = lock_timeout
        self.redis_connection = redis_connection

    def lock(self) -> bool:
        """Lock an object."""
        try:
            hash_key = self.hash_key
        except TucoDoNotLockError:
            return True

        self._lock = self.redis_connection.lock(hash_key, timeout=self.lock_timeout)

        if not self._lock.acquire(False):
            raise TucoAlreadyLockedError()
        return True

    def unlock(self) -> bool:
        """Unlock an object."""
        from redis.exceptions import LockError
        if self._lock is None:
            return True
        try:
            self._lock.release()
        except LockError:
            pass

        return True
