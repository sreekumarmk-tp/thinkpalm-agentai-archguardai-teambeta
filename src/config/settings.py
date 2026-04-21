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
GROQ_MODELS_API = "https://api.groq.com/openai/v1/models"
MAX_MEMORY_RUNS = 3
MAX_MEMORY_REPORT_CHARS = 1200

# Path for the SQLite cross-session memory database.
# Defaults to a hidden file in the project root; override via env var.
from pathlib import Path as _Path
MEMORY_DB_PATH = _Path(
    os.getenv("ARCHGUARD_MEMORY_DB", str(_Path(__file__).resolve().parents[2] / ".archguard_memory.db"))
)

MAX_ATTEMPTS_PER_MODEL = int(os.getenv("MAX_ATTEMPTS_PER_MODEL", 1))
BASE_BACKOFF_SECONDS = int(os.getenv("BASE_BACKOFF_SECONDS", 3))
RUN_SPECIALISTS_IN_PARALLEL = os.getenv("RUN_SPECIALISTS_IN_PARALLEL", "false").lower() == "true"

GROQ_MODELS = [m.strip() for m in os.getenv(
    "GROQ_FREE_MODELS",
    "llama-3.1-8b-instant,llama-3.3-70b-versatile,meta-llama/llama-4-scout-17b-16e-instruct,qwen/qwen3-32b,moonshotai/kimi-k2-instruct,openai/gpt-oss-120b,openai/gpt-oss-20b,allam-2-7b"
).split(",") if m.strip()]

GROQ_ARCHITECT_DESIGN = os.getenv("GROQ_ARCHITECT_DESIGN", GROQ_MODELS)
GROQ_SECURITY_QUALITY = os.getenv("GROQ_SECURITY_QUALITY", GROQ_MODELS)
GROQ_PERFORMANCE_TESTING = os.getenv("GROQ_PERFORMANCE_TESTING", GROQ_MODELS)
GROQ_REPORT_SYNTHESIZER = os.getenv("GROQ_REPORT_SYNTHESIZER", GROQ_MODELS)

OPENROUTER_MODELS = [m.strip() for m in os.getenv(
    "OPENROUTER_FREE_MODELS",
    "openai/gpt-oss-120b:free,google/gemma-3-27b-it:free,meta-llama/llama-3.3-70b-instruct:free,qwen/qwen3.6-plus:free"
).split(",") if m.strip()]

OPENROUTER_ARCHITECT_DESIGN = os.getenv("OPENROUTER_ARCHITECT_DESIGN", OPENROUTER_MODELS)
OPENROUTER_SECURITY_QUALITY = os.getenv("OPENROUTER_SECURITY_QUALITY", OPENROUTER_MODELS)
OPENROUTER_PERFORMANCE_TESTING = os.getenv("OPENROUTER_PERFORMANCE_TESTING", OPENROUTER_MODELS)
OPENROUTER_REPORT_SYNTHESIZER = os.getenv("OPENROUTER_REPORT_SYNTHESIZER", OPENROUTER_MODELS)

ACTIVE_AGENT_IDS = [
    "architect_design",
    "security_quality",
    "performance_testing",
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
