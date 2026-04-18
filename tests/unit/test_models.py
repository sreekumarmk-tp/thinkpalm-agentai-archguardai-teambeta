import pytest
from unittest.mock import patch, MagicMock
from src.utils.models import fetch_available_free_models, select_model_for_agent, get_model_candidates_for_agent
from src.config.settings import OPENROUTER_ANY_FREE_SENTINEL

@patch("src.utils.models.requests.get")
def test_fetch_available_free_models_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"id": "model1:free"},
            {"id": "model2:free"},
            {"id": "model3"}
        ]
    }
    mock_get.return_value = mock_response
    
    models = fetch_available_free_models()
    assert "model1:free" in models
    assert "model2:free" in models
    assert "model3" not in models
    assert len(models) == 2

@patch("src.utils.models.requests.get")
def test_fetch_available_free_models_error(mock_get):
    mock_get.side_effect = Exception("API error")
    models = fetch_available_free_models()
    assert isinstance(models, set)
    assert len(models) == 0

def test_select_model_for_agent_groq():
    model = select_model_for_agent("report_synthesizer", set(), provider="Groq")
    assert model.startswith("groq/")

def test_select_model_for_agent_openrouter_with_free_models():
    available = {"google/gemini-2.5-pro:free", "anthropic/claude-3-haiku:free"}
    
    with patch.dict("src.utils.models.FREE_MODEL_PREFERENCES", {"agent1": {"openrouter": ["google/gemini-2.5-pro:free"]}}):
        model = select_model_for_agent("agent1", available, provider="OpenRouter")
        assert model == "google/gemini-2.5-pro:free"

def test_select_model_for_agent_openrouter_fallback():
    available = {"some/other-model:free"}
    
    with patch.dict("src.utils.models.FREE_MODEL_PREFERENCES", {"agent1": {"openrouter": ["preferred/model:free"]}}):
        model = select_model_for_agent("agent1", available, provider="OpenRouter")
        assert model == "some/other-model:free"

def test_get_model_candidates_for_agent_groq():
    candidates = get_model_candidates_for_agent("agent", set(), "groq/llama3-8b-8192")
    assert all(c.startswith("groq/") for c in candidates)
    assert candidates[0] == "groq/llama3-8b-8192"

def test_get_model_candidates_for_agent_openrouter_any_free():
    available = {"google/gemini-2.5-pro:free", "anthropic/claude-3-haiku:free"}
    
    with patch.dict("src.utils.models.FREE_MODEL_PREFERENCES", {"agent1": {"openrouter": ["google/gemini-2.5-pro:free"]}}):
        candidates = get_model_candidates_for_agent("agent1", available, OPENROUTER_ANY_FREE_SENTINEL)
        
        assert candidates[0] == "google/gemini-2.5-pro:free"
        assert len(candidates) == 2

def test_get_model_candidates_for_agent_openrouter_fallback():
    candidates = get_model_candidates_for_agent("agent1", set(), "openrouter/custom-model")
    assert "openrouter/custom-model" == candidates[0]
