from datetime import timedelta

from tuco import FSM, properties


class StateHolder:
    """A simple class to hold current states."""

    def __init__(self):
        """Just initialize with None."""
        self.current_state = None
        self.current_state_date = None
        self.id = 1234


class ExampleCreditCardFSM(FSM):
    """Credit card FSM."""

    initial_state = 'new'
    state_attribute = 'current_state'

    event_error = properties.FinalState()
    state_error = properties.FinalState()

    new = properties.State(
        events=[
            properties.Event(
                'Initialize',
                'authorisation_pending',
                error=properties.Error('event_error')
            )
        ],
        error=properties.Error('state_error')
    )

    authorisation_pending = properties.State(
        events=[
            properties.Event(
                'Authorize',
                'capture_pending',
            )
        ],
    )

    capture_pending = properties.State(
        events=[
            properties.Event('Capture', 'paid'),
        ],
        timeout=properties.Timeout(timedelta(days=7), 'timeout_test')
    )

    timeout_test = properties.FinalState()

    paid = properties.State(
        events=[
            properties.Event('Refund', 'refund_pending'),
        ]
    )

    finished = properties.State(
        events=[
            properties.Event('ChargeBack', 'charged_back'),
            properties.Event('Refund', 'refunded'),
        ]
    )

    refund_pending = properties.State(
        events=[
            properties.Event('Refund', 'refunded'),
        ]
    )

    refunded = properties.FinalState()
    charged_back = properties.FinalState()
