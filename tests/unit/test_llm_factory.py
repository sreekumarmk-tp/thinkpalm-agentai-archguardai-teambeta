import pytest
from unittest.mock import patch, MagicMock
from src.utils.llm_factory import get_llm

@patch("langchain_groq.ChatGroq", create=True)
def test_get_llm_groq(mock_chat_groq):
    mock_instance = MagicMock()
    mock_chat_groq.return_value = mock_instance
    
    llm = get_llm("groq/llama3-70b-8192", temperature=0.5)
    
    mock_chat_groq.assert_called_once()
    assert mock_chat_groq.call_args[1]["model_name"] == "llama3-70b-8192"
    assert mock_chat_groq.call_args[1]["temperature"] == 0.5
    assert llm == mock_instance

@patch("src.utils.llm_factory.ChatOpenAI")
def test_get_llm_openrouter(mock_chat_openai):
    mock_instance = MagicMock()
    mock_chat_openai.return_value = mock_instance
    
    llm = get_llm("openrouter/anthropic/claude-3-opus", temperature=0.2)
    
    mock_chat_openai.assert_called_once()
    assert mock_chat_openai.call_args[1]["model"] == "anthropic/claude-3-opus"
    assert mock_chat_openai.call_args[1]["temperature"] == 0.2
    assert llm == mock_instance

@patch("src.utils.llm_factory.DEFAULT_LLM_PROVIDER", "openrouter")
@patch("src.utils.llm_factory.ChatOpenAI")
def test_get_llm_default_fallback(mock_chat_openai):
    mock_instance = MagicMock()
    mock_chat_openai.return_value = mock_instance
    
    llm = get_llm("some-model", temperature=0.0)
    
    mock_chat_openai.assert_called_once()
    assert mock_chat_openai.call_args[1]["model"] == "some-model"
    assert llm == mock_instance
