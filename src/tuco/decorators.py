"""FSM Decorators."""
from functools import wraps


def on_change(original_function):
    """Register on change event on the state machine."""
    @wraps(original_function)
    def decorated(*args, **kwargs):
        """Just run the event."""
        return original_function(*args, **kwargs)

    setattr(decorated, '_on_change_event', True)
    return decorated


def on_error(original_function):
    """Register on error event on the state machine."""
    @wraps(original_function)
    def decorated(*args, **kwargs):
        """Just run the event."""
        return original_function(*args, **kwargs)

    setattr(decorated, '_on_error_event', True)
    return decorated
