"""Locks implementation."""
__all__ = ('MemoryLock', 'RedisLock')

from .memory import MemoryLock
from .redis import RedisLock
