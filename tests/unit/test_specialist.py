import pytest
from unittest.mock import patch, MagicMock
from src.agents.specialist import build_agent_prompt, run_specialist_agent, run_specialist_agent_with_retries

def test_build_agent_prompt():
    prompt = build_agent_prompt("Test Title", "Test Objective", "http://github.com/test", "No memory")
    assert "Test Title" in prompt
    assert "Test Objective" in prompt
    assert "http://github.com/test" in prompt
    assert "No memory" in prompt
    assert "### Score" in prompt
    assert "Diagrams will be handled by the Synthesizer" in prompt

@patch("src.agents.specialist.get_llm")
@patch("src.agents.specialist.create_agent")
def test_run_specialist_agent(mock_create_agent, mock_get_llm):
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm
    
    mock_executor = MagicMock()
    mock_executor_result = {"messages": [MagicMock(content="Agent output")]}
    mock_executor.invoke.return_value = mock_executor_result
    mock_create_agent.return_value = mock_executor
    
    result = run_specialist_agent(
        "http://repo", {"title": "title", "objective": "obj"}, "model-1", "memory"
    )
    
    assert result == "Agent output"
    mock_get_llm.assert_called_once_with(model_name="model-1", temperature=0)
    mock_create_agent.assert_called_once()
    mock_executor.invoke.assert_called_once()

@patch("src.agents.specialist.run_specialist_agent")
@patch("src.agents.specialist.time.sleep")
def test_run_specialist_agent_with_retries_success(mock_sleep, mock_run_agent):
    mock_run_agent.return_value = "Agent success output"
    
    content, model_name = run_specialist_agent_with_retries(
        "http://repo", {"title": "title", "objective": "obj"}, ["model1", "model2"], 2, 0.1, "memory"
    )
    
    assert content == "Agent success output"
    assert model_name == "model1"
    mock_run_agent.assert_called_once()
    mock_sleep.assert_not_called()

@patch("src.agents.specialist.run_specialist_agent")
@patch("src.agents.specialist.time.sleep")
def test_run_specialist_agent_with_retries_fallback_model(mock_sleep, mock_run_agent):
    # First model fails twice, second model succeeds logic
    mock_run_agent.side_effect = [Exception("Failed model 1 attempt 1"), Exception("Failed model 1 attempt 2"), "Agent success output"]
    
    content, model_name = run_specialist_agent_with_retries(
        "http://repo", {"title": "title", "objective": "obj"}, ["model1", "model2"], 2, 0.1, "memory"
    )
    
    assert content == "Agent success output"
    assert model_name == "model2"
    assert mock_run_agent.call_count == 3
    assert mock_sleep.call_count == 1

@patch("src.agents.specialist.run_specialist_agent")
@patch("src.agents.specialist.time.sleep")
def test_run_specialist_agent_with_retries_rate_limited(mock_sleep, mock_run_agent):
    mock_run_agent.side_effect = [Exception("Rate limit exceeded 429"), Exception("Failed"), "Agent success output"]
    
    content, model_name = run_specialist_agent_with_retries(
        "http://repo", {"title": "title", "objective": "obj"}, ["model1", "model2"], 2, 0.1, "memory"
    )
    
    assert content == "Agent success output"
    assert model_name == "model2"
    assert mock_run_agent.call_count == 3
    assert mock_sleep.call_count == 2
