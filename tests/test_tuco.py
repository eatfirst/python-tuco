"""FSM Base tests."""

import os
import threading
from datetime import timedelta
from unittest import mock

import pytest
import pytz

from tuco import FSM, properties
from tuco.decorators import on_change, on_error
from tuco.exceptions import TucoAlreadyLockedError, TucoEventNotFoundError, TucoInvalidStateChangeError
from tuco.locks import RedisLock

from tests.example_fsm import ExampleCreditCardFSM, StateHolder


def test_state_changing():
    """Test basic changing."""
    fsm = ExampleCreditCardFSM(StateHolder())
    assert fsm.container_object.current_state == 'new'

    assert fsm.event_allowed('Initialize')
    assert fsm.trigger('Initialize')
    assert fsm.current_state == 'authorisation_pending'

    assert fsm.event_allowed('Authorize')
    assert fsm.trigger('Authorize')
    assert fsm.current_state == 'capture_pending'

    assert fsm.event_allowed('Capture')
    assert fsm.trigger('Capture')
    assert fsm.current_state == 'paid'

    assert fsm.event_allowed('Initialize') is False
    with pytest.raises(TucoEventNotFoundError):
        assert fsm.trigger('Initialize')
    assert fsm.container_object.current_state == 'paid'


def test_command_execution():
    """Test commands."""
    command1, command2 = mock.Mock(), mock.Mock()
    state_holder = StateHolder()

    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'new'
        state_attribute = 'current_state'

        new = properties.State(
            events=[
                properties.Event(
                    'TestEvent',
                    'final_state',
                    commands=[command1, command2])
            ]
        )
        final_state = properties.FinalState()

    fsm = TestFSM(state_holder)
    fsm.trigger('TestEvent')

    command1.assert_called_once_with(state_holder)
    command2.assert_called_once_with(state_holder)
    assert fsm.current_state == 'final_state'


def test_command_with_error():
    """Test event behavior when a command fail."""
    command1 = mock.Mock()
    command2 = mock.Mock(side_effect=RuntimeError)
    command3 = mock.Mock()

    state_holder = StateHolder()

    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'new'
        state_attribute = 'current_state'

        new = properties.State(
            events=[
                properties.Event(
                    'TestEvent',
                    'final_state',
                    commands=[command1, command2, command3])
            ]
        )
        final_state = properties.FinalState()

    fsm = TestFSM(state_holder)
    with pytest.raises(RuntimeError):
        fsm.trigger('TestEvent')

    command1.assert_called_once_with(state_holder)
    command2.assert_called_once_with(state_holder)
    assert command3.call_count == 0
    assert fsm.current_state == 'new'


def test_invalid_error():
    """Test common cases of invalid error configured."""
    with pytest.raises(RuntimeError):
        class TestFSM(FSM):
            """Dumb class."""

            state = properties.State(
                error=properties.Error('invalid_state')
            )

        assert TestFSM

    with pytest.raises(RuntimeError):
        class TestFSM2(FSM):
            """Dumb class."""

            state = properties.State(
                events=[properties.Event('EventName', 'final_state', error=properties.Error('invalid_state'))]
            )
            final_state = properties.FinalState()

        assert TestFSM2


def test_errors():
    """Test errors."""
    event_error_command = mock.Mock()
    state_error_command = mock.Mock()

    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'state'

        state = properties.State(
            error=properties.Error('state_error', commands=[state_error_command]),
            events=[
                properties.Event('TriggerEventError', 'non_reachable',
                                 error=properties.Error('event_error', commands=[event_error_command]),
                                 commands=[lambda x: False]),
                properties.Event('TriggerStateError', 'non_reachable', commands=[lambda x: False])
            ]
        )

        state_error = properties.FinalState()
        event_error = properties.FinalState()
        non_reachable = properties.FinalState()

    fsm = TestFSM(StateHolder())
    assert fsm.current_state == 'state'
    assert fsm.trigger('TriggerEventError') is False
    assert fsm.current_state == 'event_error'
    event_error_command.assert_called_once_with(fsm.container_object)

    fsm = TestFSM(StateHolder())
    assert fsm.current_state == 'state'
    assert fsm.trigger('TriggerStateError') is False
    assert fsm.current_state == 'state_error'
    state_error_command.assert_called_once_with(fsm.container_object)


def test_invalid_state_changes():
    """Test cases when the current state is being change to an invalid one."""
    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'state1'

        state1 = properties.State(
            events=[properties.Event('ChangeState', target_state='state2')]
        )

        state2 = properties.FinalState()

    fsm = TestFSM(StateHolder())
    assert fsm.current_state == 'state1'

    fsm.current_state = 'state2'
    with pytest.raises(TucoInvalidStateChangeError):
        fsm.current_state = 'state1'

    assert fsm.current_state == 'state2'

    class TestFSM2(FSM):
        """Dumb class."""

        initial_state = 'state1'

        state1 = properties.State(
            events=[properties.Event('ChangeState', target_state='state2')]
        )

        state2 = properties.State(events=[properties.Event('ChangeState', target_state='state3')])
        state3 = properties.FinalState()

    fsm2 = TestFSM2(StateHolder())
    assert fsm2.current_state == 'state1'

    fsm2.current_state = 'state2'
    with pytest.raises(TucoInvalidStateChangeError):
        fsm2.current_state = 'state1'

    assert fsm2.current_state == 'state2'


def test_timeout():
    """Test timeout behaviors."""
    command = mock.Mock()

    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'new'

        new = properties.State(events=[properties.Event('state1', 'state1')])

        state1 = properties.State(timeout=properties.Timeout(timedelta(days=7), 'timeout', commands=[command]))

        timeout = properties.FinalState()

        @property
        def current_state_date(self):
            """Database always send time zone aware dates but not in tests."""
            return getattr(self.container_object, self.date_attribute).replace(tzinfo=pytz.UTC)

    fsm = TestFSM(StateHolder())
    fsm.trigger('state1')
    assert fsm.trigger_timeout() is False
    assert fsm.current_state == 'state1'
    assert command.call_count == 0

    fsm.container_object.current_state_date -= timedelta(days=7)
    assert fsm.trigger_timeout() is True
    assert fsm.current_state == 'timeout'
    command.assert_called_once_with(fsm.container_object)


def test_list_timeouts():
    """Test the ability to list all configured timeouts on state machine. Useful to query expired objects."""
    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'new'

        new = properties.State(events=[properties.Event('state1', 'state1')])

        state1 = properties.State(timeout=properties.Timeout(timedelta(days=6), 'timeout'))
        state2 = properties.State(timeout=properties.Timeout(timedelta(days=5), 'timeout'))

        timeout = properties.FinalState()

    timeouts = list(TestFSM.get_all_timeouts())
    assert len(timeouts) == 2


def test_on_enter():
    """Test on enter event."""
    command = mock.Mock()

    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'state1'

        state1 = properties.State(on_enter=[command])

    fsm = TestFSM(StateHolder())
    assert fsm.current_state == 'state1'
    command.assert_called_once_with(fsm.container_object)


def test_on_change():
    """Test on change."""
    command = mock.Mock()

    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'state1'

        @on_change
        def hacky_change_call(self, *args, **kwargs):
            """Hacky way to check on change calls."""
            command(self, *args, **kwargs)

        state1 = properties.State(events=[properties.Event('Change', 'final_state')])
        final_state = properties.FinalState()

    fsm = TestFSM(StateHolder())
    assert command.call_count == 0

    command.reset_mock()

    assert fsm.trigger('Change')

    assert command.call_count == 1
    (arg1, arg2, arg3) = command.call_args[0]  # pylint: disable=unsubscriptable-object
    assert arg1 == fsm
    assert arg2.current_state == 'state1'
    assert arg3.current_state == 'final_state'


def test_on_error():
    """Test on error."""
    command = mock.Mock()
    throw_exception = mock.Mock(side_effect=NotADirectoryError)

    class TestFSM(FSM):
        """Dumb class."""

        initial_state = 'state1'

        @on_error
        def hacky_error_call(self, *args, **kwargs):
            """Hacky way to check on error calls."""
            command(self, *args, **kwargs)

        state1 = properties.State(events=[properties.Event('Change', 'final_state', commands=[throw_exception])])
        final_state = properties.FinalState()

    fsm = TestFSM(StateHolder())
    with pytest.raises(NotADirectoryError):
        fsm.trigger('Change')
    assert command.call_count == 1
    assert len(command.call_args[0]) == 4  # pylint: disable=unsubscriptable-object
    (self, old_state, new_state, exception) = command.call_args[0]  # pylint: disable=unsubscriptable-object
    assert self == fsm
    assert old_state == 'state1'
    assert new_state == 'final_state'
    assert isinstance(exception, NotADirectoryError)


def test_locking():
    """Testing locking system."""
    hold_triggered = threading.Event()
    shutdown = threading.Event()

    class TestFSM(FSM):
        """Dumb class."""

        # pylint: disable=no-self-use
        def hold(self):
            """Hold the state machine."""
            hold_triggered.set()
            shutdown.wait()

        new = properties.State(events=[properties.Event('Hold', 'final_state', commands=[hold])])
        final_state = properties.FinalState()

    def lock_it_all():
        """Lock the state machine to test it."""
        with TestFSM(StateHolder()) as fsm:
            fsm.trigger('Hold')

    worker = threading.Thread(target=lock_it_all, daemon=True)
    worker.start()

    # Hold until the machine is really locked.
    hold_triggered.wait(timeout=1)

    with pytest.raises(TucoAlreadyLockedError):
        with TestFSM(StateHolder()):
            pass

    shutdown.set()
    worker.join()


def test_locking_without_id():
    """Make sure that items without id won't get locked."""
    hold_triggered = threading.Event()
    shutdown = threading.Event()

    class TestFSM(FSM):
        """Dumb class."""

        # pylint: disable=no-self-use
        def hold(self):
            """Hold the state machine."""
            hold_triggered.set()
            shutdown.wait()

        new = properties.State(events=[
            properties.Event('Hold', 'final_state', commands=[hold]),
            properties.Event('Finish', 'final_state')
        ])
        final_state = properties.FinalState()

    state_holder = StateHolder()
    state_holder.id = None

    def lock_it_all():
        """Lock the state machine to test it."""
        with TestFSM(state_holder) as fsm:
            fsm.trigger('Hold')

    worker = threading.Thread(target=lock_it_all, daemon=True)
    worker.start()

    # Hold until the machine is really locked.
    hold_triggered.wait()

    with TestFSM(state_holder) as fsm:
        fsm.trigger('Finish')
        assert fsm.current_state == 'final_state'

    shutdown.set()
    worker.join()


def test_redis_locking(dont_run_in_appveyor):
    """Testing redis locking system."""
    assert dont_run_in_appveyor  # After we install redis in appveyor we can remove this
    hold_triggered = threading.Event()
    shutdown = threading.Event()

    class ConfiguredRedisLock(RedisLock):
        def __init__(self, *args, **kwargs):
            import redis
            os.environ.setdefault('REDIS_SERVER', '127.0.0.1')
            super().__init__(10, redis.StrictRedis(os.environ['REDIS_SERVER']), *args, **kwargs)

    class TestFSM(FSM):
        """Dumb class."""

        lock_class = ConfiguredRedisLock

        new = properties.FinalState()

    def lock_it_all():
        """Lock the state machine to test it."""
        with TestFSM(StateHolder()):
            hold_triggered.set()
            shutdown.wait()

    worker = threading.Thread(target=lock_it_all, daemon=True)
    worker.start()

    # Hold until the machine is really locked.
    hold_triggered.wait(timeout=1.5)  # It it timeout it means that the thread broke somehow

    with pytest.raises(TucoAlreadyLockedError):
        with TestFSM(StateHolder()):
            pass

    shutdown.set()
    worker.join()


def test_fatal_error():
    """Test if we can change current state to fatal state."""
    fsm = ExampleCreditCardFSM(StateHolder())
    assert fsm.current_state == 'new'
    fsm.current_state = fsm.fatal_state
    assert fsm.current_state == fsm.fatal_state
