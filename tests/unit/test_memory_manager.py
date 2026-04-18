import pytest
from unittest.mock import patch, MagicMock
from src.memory.manager import initialize_memory, build_memory_context, record_analysis_memory
import streamlit as st

@pytest.fixture
def mock_streamlit_session_state():
    with patch("src.memory.manager.st") as mock_st:
        mock_st.session_state = MagicMock()
        mock_st.session_state.__contains__.side_effect = lambda key: False
        yield mock_st

def test_initialize_memory(mock_streamlit_session_state):
    initialize_memory()
    assert mock_streamlit_session_state.session_state.analysis_memory == []

def test_initialize_memory_already_initialized():
    class MockSessionState:
        def __init__(self):
            self.analysis_memory = [{"test": "data"}]
        def __contains__(self, key):
            return key == "analysis_memory"
    
    with patch("src.memory.manager.st") as mock_st:
        session = MockSessionState()
        mock_st.session_state = session
        initialize_memory()
        assert session.analysis_memory == [{"test": "data"}]

def test_build_memory_context_empty():
    result = build_memory_context([])
    assert result == "No previous analysis memory available."

@patch("src.memory.manager.MAX_MEMORY_RUNS", 2)
def test_build_memory_context_with_data():
    memory_runs = [
        {"run_id": "1", "repo_url": "url1", "generated_at_utc": "time1", "report_excerpt": "excerpt1"},
        {"run_id": "2", "repo_url": "url2", "generated_at_utc": "time2", "report_excerpt": "excerpt2"},
        {"run_id": "3", "repo_url": "url3", "generated_at_utc": "time3", "report_excerpt": "excerpt3"},
    ]
    result = build_memory_context(memory_runs)
    assert "Previous analysis memory:" in result
    assert "Run ID: 1" not in result  # Should be sliced by MAX_MEMORY_RUNS
    assert "Run ID: 2" in result
    assert "Run ID: 3" in result
    assert "excerpt3" in result

@patch("src.memory.manager.MAX_MEMORY_RUNS", 2)
@patch("src.memory.manager.MAX_MEMORY_REPORT_CHARS", 10)
def test_record_analysis_memory():
    class MockSessionState:
        def __init__(self):
            self.analysis_memory = []
        def __contains__(self, key):
            return key == "analysis_memory"
    
    with patch("src.memory.manager.st") as mock_st:
        session = MockSessionState()
        mock_st.session_state = session
        
        record_analysis_memory("1", "repo1", "time1", "This is a very long report text")
        
        assert len(session.analysis_memory) == 1
        entry = session.analysis_memory[0]
        assert entry["run_id"] == "1"
        assert entry["report_excerpt"] == "This is a "  # Sliced due to MAX_MEMORY_REPORT_CHARS
        
        record_analysis_memory("2", "repo2", "time2", "report2")
        record_analysis_memory("3", "repo3", "time3", "report3")
        
        assert len(session.analysis_memory) == 2
        assert session.analysis_memory[0]["run_id"] == "2"
        assert session.analysis_memory[1]["run_id"] == "3"
