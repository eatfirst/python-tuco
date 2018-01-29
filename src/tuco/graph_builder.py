import os
import tempfile
from typing import List, Optional, Type

from tuco import FSM
from tuco.exceptions import TucoEmptyFSMError
from tuco.properties import Error, Event, FinalState, State, Timeout


class GraphBuilder:
    """Parse state machine's states and events to generate graphs."""

    TIMEOUT_ATTRIBUTES = {'color': 'lightgray', 'fontcolor': 'lightgray'}
    FINAL_STATE_ATTRIBUTES = {'shape': 'box', 'fillcolor': 'lightgray', 'style': 'filled'}
    EVENT_ATTRIBUTES = {'color': 'green', 'fontcolor': 'green'}
    ERROR_ATTRIBUTES = {'color': 'red', 'fontcolor': 'red'}

    def __init__(self, fsm_class: Type[FSM], file_format) -> None:
        try:
            from graphviz import Digraph
        except ImportError as e:
            raise RuntimeError('Graphviz could not be found, make sure you installed tuco with '
                               'optional graph support.') from e
        states = fsm_class.get_all_states()
        if not states:
            raise TucoEmptyFSMError()

        self.fsm_class = fsm_class
        self.states = states.items()
        self.file_format = file_format

        comment = self.fsm_class.__doc__ or ''
        # Replace line endings for multi line comments.
        comment = comment.replace('\n', '\n//')

        self.dot = Digraph(comment=comment, format=file_format, graph_attr={'overlap': 'false'})

    @classmethod
    def generate_from_class(cls, fsm_class: Type[FSM], file_format) -> str:
        """Generate a SVG graph from a tuco fsm class."""
        generation = cls(fsm_class, file_format)
        generation.iterate_states()
        return generation.render_graph()

    def iterate_states(self) -> None:
        """Iterate over all states sent and add nodes to graphviz."""
        for state_name, state in self.states:
            if isinstance(state, FinalState):
                self.add_final_state_node(state_name)
            else:
                self.add_node(state, state_name)

    def iterate_events(self, parent_state_name: str, events: List[Event]) -> None:
        """Iterate over all events of a state and add nodes to graphviz."""
        for event in events:
            self.dot.node(event.target_state)
            self.dot.edge(parent_state_name, event.target_state, label='Event: {}'.format(event.event_name),
                          _attributes=self.EVENT_ATTRIBUTES)

            self.add_error_node(parent_state_name, event.error)

    def add_node(self, state: State, state_name: str) -> None:
        """Add a node with its events and timeouts."""
        self.dot.node(state_name)

        self.add_error_node(state_name, state.error)
        self.add_timeout_node(state_name, state.timeout)

        self.iterate_events(state_name, state.events)

    def add_final_state_node(self, state_name: str) -> None:
        """Add a final node."""
        self.dot.node(state_name, _attributes=self.FINAL_STATE_ATTRIBUTES)

    def add_error_node(self, parent_state_name: str, error: Optional[Error]) -> None:
        """Render an error node if present."""
        if not error:
            return

        target_state = error.target_state
        self.dot.node(target_state)
        self.dot.edge(parent_state_name, target_state, label='Error', _attributes=self.ERROR_ATTRIBUTES)

    def add_timeout_node(self, parent_state_name: str, timeout: Optional[Timeout]) -> None:
        """Render a timeout node if present."""
        if not timeout:
            return
        self.dot.node(timeout.target_state)
        self.dot.edge(parent_state_name, timeout.target_state, label='Timeout', _attributes=self.TIMEOUT_ATTRIBUTES)

    def render_graph(self) -> str:
        """Render graph in a file and return its content."""
        temp_file = tempfile.NamedTemporaryFile(prefix='tuco', delete=False)
        temp_file.close()
        filename = temp_file.name
        graph_file = '{}.{}'.format(filename, self.file_format)

        try:
            self.dot.render(os.path.basename(filename), os.path.dirname(filename))
            return open(graph_file).read()
        finally:
            for name in (filename, graph_file):
                try:
                    os.unlink(name)
                except OSError:
                    pass


generate_from_class = GraphBuilder.generate_from_class
