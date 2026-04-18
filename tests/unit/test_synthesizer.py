import pytest
from unittest.mock import patch, MagicMock
from src.agents.synthesizer import synthesize_report

@patch("src.agents.synthesizer.get_llm")
def test_synthesize_report_success(mock_get_llm):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Final Report Content"
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm
    
    result = synthesize_report(
        "http://repo", "model1", {"Agent1": "Output1"}, "memory", 2, 0.1
    )
    
    assert result == "Final Report Content"
    mock_get_llm.assert_called_once_with(model_name="model1", temperature=0)
    mock_llm.invoke.assert_called_once()
    
    invoke_arg = mock_llm.invoke.call_args[0][0]
    assert "http://repo" in invoke_arg
    assert "## Agent1\nOutput1" in invoke_arg
    assert "memory" in invoke_arg

@patch("src.agents.synthesizer.get_llm")
@patch("src.agents.synthesizer.time.sleep")
def test_synthesize_report_retry(mock_sleep, mock_get_llm):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Final Report Content"
    
    # First invoke fails, second succeeds
    mock_llm.invoke.side_effect = [Exception("Error"), mock_response]
    mock_get_llm.return_value = mock_llm
    
    result = synthesize_report(
        "http://repo", "model1", {"Agent1": "Output1"}, "memory", 2, 0.1
    )
    
    assert result == "Final Report Content"
    assert mock_llm.invoke.call_count == 2
    assert mock_sleep.call_count == 1

@patch("src.agents.synthesizer.get_llm")
@patch("src.agents.synthesizer.time.sleep")
def test_synthesize_report_rate_limit(mock_sleep, mock_get_llm):
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Final Report Content"
    
    # First invoke fails with rate limit, second succeeds
    mock_llm.invoke.side_effect = [Exception("Rate limit exceeded 429"), mock_response]
    mock_get_llm.return_value = mock_llm
    
    result = synthesize_report(
        "http://repo", "model1", {"Agent1": "Output1"}, "memory", 2, 0.1
    )
    
    assert result == "Final Report Content"
    assert mock_llm.invoke.call_count == 2
    assert mock_sleep.call_count == 1

@patch("src.agents.synthesizer.get_llm")
@patch("src.agents.synthesizer.time.sleep")
def test_synthesize_report_failure(mock_sleep, mock_get_llm):
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("Persistent Error")
    mock_get_llm.return_value = mock_llm
    
    with pytest.raises(Exception, match="Persistent Error"):
        synthesize_report(
            "http://repo", "model1", {"Agent1": "Output1"}, "memory", 2, 0.1
        )
    
    assert mock_llm.invoke.call_count == 2
    assert mock_sleep.call_count == 1
