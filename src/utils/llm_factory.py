import os
from langchain_openai import ChatOpenAI
from src.config.settings import (
    OPENROUTER_API_KEY,
    GROQ_API_KEY,
    DEFAULT_LLM_PROVIDER
)

def get_llm(model_name: str, temperature: float = 0):
    """
    Adapter to returning a LangChain LLM instance for OpenRouter or Groq.
    
    Logic:
    1. If model_name starts with 'groq/', use Groq (model name is what's after 'groq/').
    2. If model_name starts with 'openrouter/', use OpenRouter.
    3. If no prefix, use DEFAULT_LLM_PROVIDER.
    """
    provider = DEFAULT_LLM_PROVIDER
    actual_model = model_name

    if model_name.startswith("groq/"):
        provider = "groq"
        actual_model = model_name.replace("groq/", "", 1)
    elif model_name.startswith("openrouter/"):
        provider = "openrouter"
        actual_model = model_name.replace("openrouter/", "", 1)

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=GROQ_API_KEY,
            model_name=actual_model,
            temperature=temperature
        )
    else:
        # Default to OpenRouter via LangChain's ChatOpenAI
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            model=actual_model,
            temperature=temperature,
        )
