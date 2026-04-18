import requests
from typing import Set, Dict, List
from src.config.settings import (
    OPENROUTER_MODELS_API,
    GITHUB_TIMEOUT,
    FREE_MODEL_PREFERENCES,
    OPENROUTER_ANY_FREE_SENTINEL,
    GROQ_MODELS,
    OPENROUTER_MODELS
)

def fetch_available_free_models() -> Set[str]:
    try:
        res = requests.get(OPENROUTER_MODELS_API, timeout=GITHUB_TIMEOUT)
        res.raise_for_status()
        data = res.json().get("data", [])
        free_models = set()
        for model in data:
            model_id = model.get("id", "")
            if model_id.endswith(":free"):
                free_models.add(model_id)
        return free_models
    except Exception:
        return set()

def select_model_for_agent(agent_id: str, available_free_models: Set[str], provider: str = "OpenRouter") -> str:
    provider_key = provider.lower()
    pref_dict = FREE_MODEL_PREFERENCES.get(agent_id, FREE_MODEL_PREFERENCES["report_synthesizer"])
    preferred = pref_dict.get(provider_key, pref_dict.get("openrouter", []))

    if provider_key == "groq":
        # For Groq, just return the first preferred model with prefix
        return f"groq/{preferred[0]}" if preferred else f"groq/{GROQ_MODELS[0]}"
    
    if available_free_models:
        for model_name in preferred:
            if model_name in available_free_models:
                return model_name
        return sorted(available_free_models)[0]
    return preferred[0] if preferred else ""

def get_model_candidates_for_agent(agent_id: str, available_free_models: Set[str], manual_model: str) -> List[str]:
    # Determine provider-agnostic ID or use manual model prefix
    provider = "openrouter"
    if manual_model.startswith("groq/"):
        provider = "groq"
    
    pref_dict = FREE_MODEL_PREFERENCES.get(agent_id, FREE_MODEL_PREFERENCES["report_synthesizer"])
    preferred = pref_dict.get(provider, [])

    if provider == "groq":
        candidates = [f"groq/{m}" for m in preferred]
        # Supplement with other Groq models if not in preferred
        for m in GROQ_MODELS:
            if f"groq/{m}" not in candidates:
                candidates.append(f"groq/{m}")
        if manual_model and manual_model not in candidates:
            candidates.insert(0, manual_model)
        return candidates

    if manual_model == OPENROUTER_ANY_FREE_SENTINEL:
        manual_model = ""
    
    if available_free_models:
        prioritized = [m for m in preferred if m in available_free_models]
        remaining = [m for m in sorted(available_free_models) if m not in prioritized]
        candidates = prioritized + remaining
    else:
        # Fallback to OPENROUTER_MODELS
        candidates = [m if m.startswith("openrouter/") else f"openrouter/{m}" for m in OPENROUTER_MODELS]

    if manual_model and manual_model not in candidates:
        candidates.insert(0, manual_model)
    return candidates
