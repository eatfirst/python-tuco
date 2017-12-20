import os
import tempfile
from typing import Type

from graphviz import Digraph

from tuco import FSM
from tuco.properties import FinalState


def generate_from_class(cls: Type[FSM], file_format) -> str:
    """Generate a SVG graph from a tuco fsm class."""
    comment = cls.__doc__ or ''
    # Replace line endings for multi line comments.
    comment = comment.replace('\n', '\n//')

    dot = Digraph(comment=comment, format=file_format, graph_attr={'overlap': 'false'})

    iterate_states(dot, cls._states.items())
    return render_graph(dot, file_format)


def iterate_states(dot, states) -> None:
    """Iterate over all states sent and add nodes to a graphviz instance."""
    for state_name, state in states:
        if isinstance(state, FinalState):
            dot.node(state_name, _attributes={'shape': 'box', 'fillcolor': 'silver', 'style': 'filled'})
            continue
        else:
            dot.node(state_name)

        if state.error:
            add_error_node(dot, state_name, state.error.target_state)

        if state.timeout:
            dot.node(state.timeout.target_state)
            dot.edge(state_name, state.timeout.target_state, label='Timeout',
                     _attributes={'color': 'silver', 'fontcolor': 'silver'})

        iterate_events(dot, state_name, state.events)


def iterate_events(dot, parent_state_name, events) -> None:
    """Iterate over all events of a state and add notes to a graphviz instance."""
    for event in events:
        dot.node(event.target_state)
        dot.edge(parent_state_name, event.target_state, label='Event: {}'.format(event.event_name),
                 _attributes={'color': 'green', 'fontcolor': 'green'})

        if event.error:
            add_error_node(dot, parent_state_name, event.error.target_state)


def add_error_node(dot, parent_state_name, target_state) -> None:
    """Render an error node to a graphviz instance."""
    dot.node(target_state)
    dot.edge(parent_state_name, target_state, label='Error', _attributes={'color': 'red', 'fontcolor': 'red'})


def render_graph(dot, file_format) -> str:
    """Render graph in a file and return its content."""
    temp_file = tempfile.NamedTemporaryFile(prefix='tuco', delete=False)
    temp_file.close()
    filename = temp_file.name
    graph_file = '{}.{}'.format(filename, file_format)

    try:
        dot.render(os.path.basename(filename), os.path.dirname(filename))
        return open(graph_file).read()
    finally:
        for name in (filename, graph_file):
            try:
                os.unlink(name)
            except OSError:
                pass
