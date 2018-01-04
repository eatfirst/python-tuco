import os
from xml.etree.ElementTree import fromstring

import pytest

from tuco import FSM
from tuco.exceptions import TucoEmptyFSMError

from tests.example_fsm import ExampleCreditCardFSM


def test_svg():
    """Test SVG generation.


    It is hard to test SVGs generated from different graphviz version so we just do a parsing and assert number of
    elements.
    """
    with open(os.path.join(os.path.dirname(__file__), 'fixtures', 'sample-fsm.svg')) as f:
        generated_graph = fromstring(ExampleCreditCardFSM.generate_graph('svg'))
        saved_graph = fromstring(f.read())
        assert len(list(generated_graph[0])) == len(list(saved_graph[0]))


def test_empty_fsm():
    """Test a case where FSM has no state and tries to generate a graph."""
    new_class = type('EmptyFSM', (FSM,), {})  # type: FSM
    with pytest.raises(TucoEmptyFSMError):
        new_class.generate_graph()
