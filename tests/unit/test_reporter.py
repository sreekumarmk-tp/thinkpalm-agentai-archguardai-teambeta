import pytest
from unittest.mock import patch, MagicMock
from src.graphs.reporter import create_reporter_graph

def test_create_reporter_graph():
    # Since it just returns a workflow.compile(), we just verify it exists
    graph = create_reporter_graph()
    assert graph is not None
    # Depending on langgraph, it should have an invoke or astream method if compiled
    assert hasattr(graph, 'invoke') or hasattr(graph, 'stream')
