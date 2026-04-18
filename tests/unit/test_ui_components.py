import pytest
import json
from unittest.mock import patch, MagicMock
from src.ui.components import build_json_export, render_sidebar, render_export_downloads

def test_build_json_export():
    json_str = build_json_export(
        repo_url="http://x",
        run_id="123",
        generated_at_utc="time",
        active_preset="fast",
        run_in_parallel=True,
        max_parallel_workers=2,
        max_attempts_per_model=1,
        base_backoff_seconds=1,
        selected_models={"agent": "model1"},
        synthesizer_model="model2",
        specialist_results={"agent": "res"},
        final_report="final md",
    )
    data = json.loads(json_str)
    assert data["repository"] == "http://x"
    assert data["run_metadata"]["run_id"] == "123"
    assert data["run_configuration"]["parallel_workers"] == 2
    assert data["models"]["specialists"]["agent"] == "model1"
    assert data["final_report_markdown"] == "final md"

@patch("src.ui.components.st")
def test_render_sidebar_default(mock_st):
    class MockSessionState(dict):
        def __getattr__(self, key):
            if key in self:
                return self[key]
            raise AttributeError(key)
        def __setattr__(self, key, value):
            self[key] = value
    
    session = MockSessionState()
    mock_st.session_state = session
    
    # Setup mock returns
    mock_st.sidebar.__enter__ = MagicMock()
    mock_st.sidebar.__exit__ = MagicMock()
    # mock_st.columns
    mock_col1 = MagicMock()
    mock_col2 = MagicMock()
    mock_st.columns.return_value = [mock_col1, mock_col2]
    # Button mock returns False so it doesn't trigger reruns
    mock_col1.button.return_value = False
    mock_col2.button.return_value = False
    
    mock_st.radio.return_value = "Groq"
    mock_st.checkbox.side_effect = [True, True] # auto_pick, parallel
    mock_st.slider.side_effect = [3, 2, 4] # parallel, retry, backoff
    
    result = render_sidebar()
    assert session.parallel_workers == 3
    assert session.retry_attempts == 2
    assert session.backoff_seconds == 4
    
    assert result["llm_provider"] == "Groq"
    assert result["auto_pick_models"] == True
    assert result["run_in_parallel"] == True
    assert result["max_parallel_workers"] == 3
    assert result["max_attempts_per_model"] == 2
    assert result["base_backoff_seconds"] == 4
    assert result["active_preset"] == "Custom"

@patch("src.ui.components.st")
@patch("src.ui.components.export_to_docx")
@patch("src.ui.components.export_to_pdf")
@patch("builtins.open")
def test_render_export_downloads(mock_open, mock_to_pdf, mock_to_docx, mock_st):
    # Setup open mock for reading binary data
    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file
    
    # Mock columns
    col1 = MagicMock()
    col2 = MagicMock()
    mock_st.columns.return_value = [col1, col2]
    
    render_export_downloads("report", "123")
    
    mock_to_docx.assert_called_once_with("report", "/tmp/report_123.docx")
    mock_to_pdf.assert_called_once_with("report", "/tmp/report_123.pdf")
    assert mock_st.download_button.call_count == 2
