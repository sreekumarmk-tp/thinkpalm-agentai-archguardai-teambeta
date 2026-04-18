import re
import time
from typing import Dict
from src.utils.llm_factory import get_llm

def synthesize_report(
    repo_url: str,
    model_name: str,
    specialist_outputs: Dict[str, str],
    memory_context: str,
    max_attempts_per_model: int,
    base_backoff_seconds: float,
) -> str:
    # Use the LLM factory adapter
    llm = get_llm(model_name=model_name, temperature=0)
    
    synthesis_instructions = (
        f"Create a final detailed architecture and engineering report for {repo_url}.\n"
        "Use specialist findings provided below.\n"
        "Output sections:\n"
        "1) Executive Summary\n"
        "2) Overall Risk Posture and Health Score\n"
        "3) Detailed section for each specialist (including Testing & QA and Directory Structure)\n"
        "4) Top 10 prioritized fixes\n"
        "5) 30/60/90 day implementation roadmap\n"
        "6) Visualization Section:\n"
        "   - **Architecture Diagram**: High-level structural view of components and their relationships.\n"
        "   - **Functional Flow Diagram**: Sequential or logical flow of a primary business/technical process.\n"
        "   - **IMPORTANT**: Provide exactly these two diagrams using Mermaid syntax. Encapsulate each in a separate '```mermaid' code block.\n"
        "7) Conclusion\n\n"
        f"Use this memory context from previous runs when relevant:\n{memory_context}\n\n"
        "Be specific, practical and evidence-based. Keep the response in clean markdown."
    )

    merged = []
    for agent_name, content in specialist_outputs.items():
        merged.append(f"## {agent_name}\n{content}")
    final_input = synthesis_instructions + "\n\n" + "\n\n".join(merged)

    def _extract_rate_limit_reset_seconds(exc_str: str) -> float:
        match = re.search(r"X-RateLimit-Reset['\"]\\s*:\\s*['\"](\\d+)", exc_str)
        if not match:
            return 0.0
        reset_ms = float(match.group(1))
        reset_seconds = (reset_ms / 1000.0) - time.time()
        return max(0.0, reset_seconds)

    def _is_rate_limited(exc_str: str) -> bool:
        return ("Rate limit exceeded" in exc_str) or bool(re.search(r"Error code:\\s*429\\b", exc_str))

    last_exc: Exception | None = None
    for attempt in range(1, max_attempts_per_model + 1):
        try:
            response = llm.invoke(final_input)
            return response.content
        except Exception as exc:
            last_exc = exc
            exc_str = str(exc)
            if _is_rate_limited(exc_str):
                reset_wait_seconds = _extract_rate_limit_reset_seconds(exc_str)
                sleep_seconds = (reset_wait_seconds + base_backoff_seconds) if reset_wait_seconds > 0 else (
                    base_backoff_seconds * (2 ** (attempt - 1))
                )
                time.sleep(sleep_seconds)
            elif attempt < max_attempts_per_model:
                time.sleep(base_backoff_seconds * (2 ** (attempt - 1)))
            else:
                break

    raise last_exc if last_exc else RuntimeError("Synthesis failed without an exception.")
