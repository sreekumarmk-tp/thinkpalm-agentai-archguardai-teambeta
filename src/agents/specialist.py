import re
import time
from typing import Dict, List, Tuple
from langchain_core.tools import Tool
from langchain.agents import create_agent
from src.utils.llm_factory import get_llm
from src.tools.github import fetch_repo_structure, read_github_file

def build_agent_prompt(agent_title: str, objective: str, repo_url: str, memory_context: str) -> str:
    return (
        f"You are the '{agent_title}' specialist for repository review.\n"
        f"Repository URL: {repo_url}\n\n"
        "Use tools first:\n"
        "1) Call list_repo_files.\n"
        "2) Pick only relevant files and call read_specific_file for evidence.\n"
        "3) Provide output in markdown using this exact structure:\n\n"
        "### Score\n"
        "Give an integer score from 0-100.\n\n"
        "### Findings\n"
        "- Severity-tagged findings (Critical/High/Medium/Low)\n"
        "- Include direct file evidence in each point\n\n"
        "### Recommendations\n"
        "- Prioritized actions with effort (Low/Medium/High) and impact\n\n"
        "### Quick Wins\n"
        "- 3 immediate fixes\n\n"
        "**CRITICAL**: Do NOT generate any Mermaid diagrams or visual maps. Focus strictly on text-based analysis. Diagrams will be handled by the Synthesizer.\n\n"
        f"Memory context from earlier runs:\n{memory_context}\n\n"
        f"Objective: {objective}\n"
    )

def run_specialist_agent(
    repo_url: str,
    agent_spec: Dict[str, str],
    model_name: str,
    memory_context: str,
) -> str:
    # Use the LLM factory adapter
    llm = get_llm(model_name=model_name, temperature=0)
    
    tools = [
        Tool(
            name="list_repo_files",
            func=lambda _: fetch_repo_structure(repo_url),
            description="Get repository file tree.",
        ),
        Tool(
            name="read_specific_file",
            func=lambda file_path: read_github_file(repo_url, file_path),
            description="Read file content. Input: exact relative file path.",
        ),
    ]
    agent_executor = create_agent(model=llm, tools=tools)
    task = {
        "messages": [
            (
                "user",
                build_agent_prompt(
                    agent_spec["title"],
                    agent_spec["objective"],
                    repo_url,
                    memory_context,
                ),
            )
        ]
    }
    result = agent_executor.invoke(task)
    return result["messages"][-1].content

def run_specialist_agent_with_retries(
    repo_url: str,
    agent_spec: Dict[str, str],
    model_candidates: List[str],
    max_attempts_per_model: int,
    base_backoff_seconds: float,
    memory_context: str,
) -> Tuple[str, str]:
    def _extract_rate_limit_reset_seconds(exc_str: str) -> float:
        match = re.search(r"X-RateLimit-Reset['\"]\\s*:\\s*['\"](\\d+)", exc_str)
        if not match:
            return 0.0
        reset_ms = float(match.group(1))
        reset_seconds = (reset_ms / 1000.0) - time.time()
        return max(0.0, reset_seconds)

    def _is_rate_limited(exc_str: str) -> bool:
        return ("Rate limit exceeded" in exc_str) or bool(re.search(r"Error code:\\s*429\\b", exc_str))

    errors: List[str] = []
    for model_name in model_candidates:
        for attempt in range(1, max_attempts_per_model + 1):
            try:
                content = run_specialist_agent(repo_url, agent_spec, model_name, memory_context)
                return content, model_name
            except Exception as exc:
                exc_str = str(exc)
                errors.append(f"{model_name} attempt {attempt}: {exc_str}")

                if _is_rate_limited(exc_str):
                    reset_wait_seconds = _extract_rate_limit_reset_seconds(exc_str)
                    sleep_seconds = (reset_wait_seconds + base_backoff_seconds) if reset_wait_seconds > 0 else (
                        base_backoff_seconds * (2 ** (attempt - 1))
                    )
                    time.sleep(sleep_seconds)
                    break

                if attempt < max_attempts_per_model:
                    sleep_seconds = base_backoff_seconds * (2 ** (attempt - 1))
                    time.sleep(sleep_seconds)
    error_details = "\n".join(errors[:8])
    raise Exception(
        "Agent execution failed after retries across fallback models.\n"
        f"Recent errors:\n{error_details}"
    )
