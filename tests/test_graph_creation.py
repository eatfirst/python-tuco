import os
import sys

import pytest
from tests.example_fsm import ExampleCreditCardFSM


@pytest.mark.skipif(sys.version_info < (3, 6), reason='requires python 3.6 because it maintains class fields ordering')
def test_svg():
    """Test SVG generation.

    It will only run with python 3.6+ because it maintains class fields ordering and any change in that can generate
    the svg in a different order.
    """
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'sample-fsm.svg')) as f:
        assert ExampleCreditCardFSM.generate_graph('svg') == f.read()
