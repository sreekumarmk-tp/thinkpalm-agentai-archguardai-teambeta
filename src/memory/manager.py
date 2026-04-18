from typing import List, Dict
import streamlit as st
from src.config.settings import MAX_MEMORY_RUNS, MAX_MEMORY_REPORT_CHARS

def initialize_memory() -> None:
    if "analysis_memory" not in st.session_state:
        st.session_state.analysis_memory = []

def build_memory_context(memory_runs: List[Dict[str, str]]) -> str:
    if not memory_runs:
        return "No previous analysis memory available."

    blocks = []
    for run in memory_runs[-MAX_MEMORY_RUNS:]:
        snippet = run.get("report_excerpt", "").strip()
        blocks.append(
            f"- Run ID: {run.get('run_id', 'unknown')}\n"
            f"  Repository: {run.get('repo_url', 'unknown')}\n"
            f"  Generated At (UTC): {run.get('generated_at_utc', 'unknown')}\n"
            f"  Report Excerpt:\n{snippet}"
        )
    return "Previous analysis memory:\n" + "\n".join(blocks)

def record_analysis_memory(run_id: str, repo_url: str, generated_at_utc: str, final_report: str) -> None:
    initialize_memory()
    entry = {
        "run_id": run_id,
        "repo_url": repo_url,
        "generated_at_utc": generated_at_utc,
        "report_excerpt": final_report[:MAX_MEMORY_REPORT_CHARS],
    }
    st.session_state.analysis_memory.append(entry)
    st.session_state.analysis_memory = st.session_state.analysis_memory[-MAX_MEMORY_RUNS:]
