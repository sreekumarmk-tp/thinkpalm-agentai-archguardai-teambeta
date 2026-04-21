"""
Memory manager for ArchGuard AI.

Provides a two-layer memory strategy:
  1. **SQLite persistence** (cross-session) – analysis runs are stored in a
     local database managed by :class:`~src.memory.store.SQLiteMemoryStore`.
  2. **Streamlit session_state cache** (in-session) – fast, in-process list
     used during a running Streamlit session.

On every ``initialize_memory`` call the Streamlit cache is seeded from SQLite,
so history from previous sessions is immediately available.  New runs written
via ``record_analysis_memory`` are persisted to both layers atomically.

The public interface is identical to the original manager, so callers in
``app.py`` and tests require no changes beyond the updated imports.
"""

from typing import Dict, List

import streamlit as st

from src.config.settings import MAX_MEMORY_RUNS, MAX_MEMORY_REPORT_CHARS, MEMORY_DB_PATH
from src.memory.store import SQLiteMemoryStore

# Module-level singleton – shared for the lifetime of the Python process.
_store = SQLiteMemoryStore(MEMORY_DB_PATH)


def initialize_memory() -> None:
    """Seed Streamlit session_state from the SQLite store.

    If ``analysis_memory`` is already present in the session (e.g. the user
    clicked "Analyse" and is still on the same page), this is a no-op so that
    in-session additions are not overwritten by a stale DB read.
    """
    if "analysis_memory" not in st.session_state:
        st.session_state.analysis_memory = _store.load(MAX_MEMORY_RUNS)


def build_memory_context(memory_runs: List[Dict[str, str]]) -> str:
    """Format *memory_runs* into a plain-text context block for LLM prompts.

    Args:
        memory_runs: List of run dicts, each containing ``run_id``,
                     ``repo_url``, ``generated_at_utc``, and
                     ``report_excerpt``.

    Returns:
        A human-readable string summary of the most-recent runs, or a
        sentinel string when no history exists.
    """
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


def record_analysis_memory(
    run_id: str,
    repo_url: str,
    generated_at_utc: str,
    final_report: str,
) -> None:
    """Persist a completed analysis run to both SQLite and session_state.

    Args:
        run_id: Unique identifier for this analysis run.
        repo_url: The GitHub repository URL that was analysed.
        generated_at_utc: ISO-8601 UTC timestamp of report generation.
        final_report: Full Markdown report text; truncated before storage.
    """
    initialize_memory()
    entry: Dict[str, str] = {
        "run_id": run_id,
        "repo_url": repo_url,
        "generated_at_utc": generated_at_utc,
        "report_excerpt": final_report[:MAX_MEMORY_REPORT_CHARS],
    }

    # 1. Persist to SQLite (cross-session durability).
    _store.append(entry)
    _store.prune(keep=MAX_MEMORY_RUNS)

    # 2. Update in-session cache to keep current session in sync.
    st.session_state.analysis_memory.append(entry)
    st.session_state.analysis_memory = st.session_state.analysis_memory[-MAX_MEMORY_RUNS:]
