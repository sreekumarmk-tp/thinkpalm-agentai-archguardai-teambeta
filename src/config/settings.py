import os
from typing import Dict, List
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "groq").lower()

GITHUB_TIMEOUT = 20
MAX_FILE_LIST = 400
MAX_FILE_CONTENT_CHARS = 12000
OPENROUTER_MODELS_API = "https://openrouter.ai/api/v1/models"
MAX_MEMORY_RUNS = 3
MAX_MEMORY_REPORT_CHARS = 1200
OPENROUTER_ANY_FREE_SENTINEL = "openrouter/free"

GROQ_MODELS = [m.strip() for m in os.getenv("GROQ_FREE_MODELS", "llama-3.3-70b-versatile,meta-llama/llama-4-scout-17b-16e-instruct,llama-3.1-8b-instant,meta-llama/llama-prompt-guard-2-86m,meta-llama/llama-prompt-guard-2-22m,qwen/qwen3-32b,mixtral-8x7b-32768,gemma2-9b-it,openai/gpt-oss-120b,openai/gpt-oss-20b,openai/gpt-oss-safeguard-20b").split(",") if m.strip()]

GROQ_ARCHITECT_DESIGN = os.getenv("GROQ_ARCHITECT_DESIGN", GROQ_MODELS)
GROQ_SECURITY_QUALITY = os.getenv("GROQ_SECURITY_QUALITY", GROQ_MODELS)
GROQ_PERFORMANCE_TESTING = os.getenv("GROQ_PERFORMANCE_TESTING", GROQ_MODELS)
GROQ_REPORT_SYNTHESIZER = os.getenv("GROQ_REPORT_SYNTHESIZER", GROQ_MODELS)

OPENROUTER_MODELS = [m.strip() for m in os.getenv("OPENROUTER_FREE_MODELS", "arcee-ai/trinity-large-preview:free,liquid/lfm-2.5-1.2b-thinking:free,meta-llama/llama-3.3-70b-instruct:free,z-ai/glm-4.5-air:free,nvidia/nemotron-3-nano-30b-a3b:free,nvidia/nemotron-nano-9b-v2:free,nvidia/nemotron-nano-12b-v2-vl:free,google/gemma-4-31b-it:free,google/gemma-4-26b-a4b-it:free,google/gemma-3-27b-it:free,google/gemma-3-4b-it:free,google/gemma-3-12b-it:free,google/gemma-3n-e2b-it:free,google/gemma-3n-e4b-it:free,qwen/qwen3-coder:free,qwen/qwen3-next-80b-a3b-instruct:free,openai/gpt-oss-120b:free,openai/gpt-oss-20b:free,liquid/lfm-2.5-1.2b-instruct:free,meta-llama/llama-3.3-70b-instruct:free,meta-llama/llama-3.2-3b-instruct:free,nousresearch/hermes-3-llama-3.1-405b:free").split(",") if m.strip()]

OPENROUTER_ARCHITECT_DESIGN = os.getenv("OPENROUTER_ARCHITECT_DESIGN", OPENROUTER_MODELS)
OPENROUTER_SECURITY_QUALITY = os.getenv("OPENROUTER_SECURITY_QUALITY", OPENROUTER_MODELS)
OPENROUTER_PERFORMANCE_TESTING = os.getenv("OPENROUTER_PERFORMANCE_TESTING", OPENROUTER_MODELS)
OPENROUTER_REPORT_SYNTHESIZER = os.getenv("OPENROUTER_REPORT_SYNTHESIZER", OPENROUTER_MODELS)

AGENT_DEFINITIONS: List[Dict[str, str]] = [
    {
        "id": "architect_design",
        "title": "Architecture, Design & Maintainability",
        "objective": (
            "Detect programming languages, frameworks, versions, and directory organization. "
            "Evaluate adherence to SOLID, DRY, and KISS principles. Review design pattern consistency, "
            "module boundaries, nesting, and technical debt. Recommend optimal modern alternatives."
        ),
    },
    {
        "id": "security_quality",
        "title": "Security, Quality & Standards",
        "objective": (
            "Identify security risks, secret exposure, auth/session weaknesses, and PII concerns. "
            "Review static typing quality, coding standards consistency, input validation, "
            "and exception handling strategy."
        ),
    },
    {
        "id": "performance_testing",
        "title": "Performance, Efficiency & QA",
        "objective": (
            "Review data structure optimality, complexity risks, compute/memory bottlenecks, and I/O behavior. "
            "Evaluate testing maturity (unit, integration, E2E), coverage gaps, and CI/CD quality integration."
        ),
    },
]

FREE_MODEL_PREFERENCES: Dict[str, Dict[str, List[str]]] = {
    "architect_design": {
        "groq": GROQ_ARCHITECT_DESIGN,
        "openrouter": OPENROUTER_ARCHITECT_DESIGN
    },
    "security_quality": {
        "groq": GROQ_SECURITY_QUALITY,
        "openrouter": OPENROUTER_SECURITY_QUALITY
    },
    "performance_testing": {
        "groq": GROQ_PERFORMANCE_TESTING,
        "openrouter": OPENROUTER_PERFORMANCE_TESTING
    },
    "report_synthesizer": {
        "groq": GROQ_REPORT_SYNTHESIZER,
        "openrouter": OPENROUTER_REPORT_SYNTHESIZER
    },
}

def update_preferences_from_env():
    for agent_id in FREE_MODEL_PREFERENCES.keys():
        # Load Groq preferences
        groq_key = f"GROQ_{agent_id.upper()}"
        groq_val = os.getenv(groq_key)
        if groq_val:
            models = [m.strip() for m in groq_val.split(",") if m.strip()]
            if models:
                FREE_MODEL_PREFERENCES[agent_id]["groq"] = models
        
        # Load OpenRouter preferences
        or_key = f"OPENROUTER_{agent_id.upper()}"
        or_val = os.getenv(or_key)
        if or_val:
            models = [m.strip() for m in or_val.split(",") if m.strip()]
            if models:
                FREE_MODEL_PREFERENCES[agent_id]["openrouter"] = models

update_preferences_from_env()
