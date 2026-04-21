"""
Updated unit tests for src.memory.manager.

The manager has a two-layer architecture:
  - SQLite persistence  (handled by a SQLiteMemoryStore module-level singleton)
  - Streamlit session_state cache (in-process, per-session)

Streamlit is not installed in the test environment, so we stub it in
sys.modules BEFORE any src.memory import occurs.  All SQLiteMemoryStore
interactions are verified via a MagicMock injected over the singleton.
"""

import sys
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Stub streamlit before any src.memory import so the module-level
# `import streamlit as st` in manager.py does not raise ImportError.
# ---------------------------------------------------------------------------
_st_stub = MagicMock()
sys.modules.setdefault("streamlit", _st_stub)

# Now it is safe to import the manager module
import importlib
import src.memory.manager as _manager_mod  # noqa: E402  (after sys.modules patch)
from src.memory.manager import (  # noqa: E402
    initialize_memory,
    build_memory_context,
    record_analysis_memory,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session(existing: Optional[List[Dict]] = None):
    """Return a lightweight object that behaves like st.session_state."""

    class _Session:
        def __init__(self):
            self.analysis_memory = existing if existing is not None else []

        def __contains__(self, key):
            return hasattr(self, key)

    return _Session()


# ---------------------------------------------------------------------------
# initialize_memory
# ---------------------------------------------------------------------------

class TestInitializeMemory:
    def test_seeds_cache_from_sqlite_when_empty(self) -> None:
        """When analysis_memory is absent from session_state, load it from DB."""
        db_rows = [
            {"run_id": "abc", "repo_url": "u", "generated_at_utc": "t", "report_excerpt": "e"}
        ]
        mock_store = MagicMock()
        mock_store.load.return_value = db_rows

        mock_session = MagicMock()
        mock_session.__contains__ = MagicMock(return_value=False)

        with patch.object(_manager_mod, "_store", mock_store):
            with patch.object(_manager_mod, "st") as mock_st:
                mock_st.session_state = mock_session
                initialize_memory()

        mock_store.load.assert_called_once()
        assert mock_session.analysis_memory == db_rows

    def test_does_not_overwrite_existing_session(self) -> None:
        """If analysis_memory is already in session_state leave it untouched."""
        mock_session = MagicMock()
        mock_session.__contains__ = MagicMock(return_value=True)
        mock_store = MagicMock()

        with patch.object(_manager_mod, "_store", mock_store):
            with patch.object(_manager_mod, "st") as mock_st:
                mock_st.session_state = mock_session
                initialize_memory()

        mock_store.load.assert_not_called()


# ---------------------------------------------------------------------------
# build_memory_context
# ---------------------------------------------------------------------------

class TestBuildMemoryContext:
    def test_empty_returns_sentinel(self) -> None:
        assert build_memory_context([]) == "No previous analysis memory available."

    @patch.object(_manager_mod, "MAX_MEMORY_RUNS", 2)
    def test_formats_all_fields(self) -> None:
        runs = [
            {"run_id": "r1", "repo_url": "url1", "generated_at_utc": "t1", "report_excerpt": "ex1"},
            {"run_id": "r2", "repo_url": "url2", "generated_at_utc": "t2", "report_excerpt": "ex2"},
        ]
        ctx = build_memory_context(runs)
        assert "Previous analysis memory:" in ctx
        assert "Run ID: r1" in ctx
        assert "url2" in ctx
        assert "ex2" in ctx

    @patch.object(_manager_mod, "MAX_MEMORY_RUNS", 2)
    def test_respects_max_memory_runs_slice(self) -> None:
        runs = [
            {"run_id": "r1", "repo_url": "u1", "generated_at_utc": "t1", "report_excerpt": "e1"},
            {"run_id": "r2", "repo_url": "u2", "generated_at_utc": "t2", "report_excerpt": "e2"},
            {"run_id": "r3", "repo_url": "u3", "generated_at_utc": "t3", "report_excerpt": "e3"},
        ]
        ctx = build_memory_context(runs)
        assert "Run ID: r1" not in ctx   # oldest, sliced out by MAX_MEMORY_RUNS=2
        assert "Run ID: r2" in ctx
        assert "Run ID: r3" in ctx


# ---------------------------------------------------------------------------
# record_analysis_memory
# ---------------------------------------------------------------------------

class TestRecordAnalysisMemory:
    @patch.object(_manager_mod, "MAX_MEMORY_RUNS", 3)
    @patch.object(_manager_mod, "MAX_MEMORY_REPORT_CHARS", 10)
    def test_writes_to_sqlite_and_session(self) -> None:
        mock_store = MagicMock()
        session = _make_session()

        with patch.object(_manager_mod, "_store", mock_store):
            with patch.object(_manager_mod, "st") as mock_st:
                mock_st.session_state = session
                record_analysis_memory(
                    "run1", "https://github.com/a/b", "2026-01-01T00:00Z", "A long report text"
                )

        # --- SQLite layer ---
        mock_store.append.assert_called_once()
        stored = mock_store.append.call_args[0][0]
        assert stored["run_id"] == "run1"
        assert stored["report_excerpt"] == "A long rep"  # "A long report text"[:10] == "A long rep"
        mock_store.prune.assert_called_once_with(keep=3)

        # --- Session-state cache layer ---
        assert len(session.analysis_memory) == 1
        assert session.analysis_memory[0]["run_id"] == "run1"

    @patch.object(_manager_mod, "MAX_MEMORY_RUNS", 2)
    @patch.object(_manager_mod, "MAX_MEMORY_REPORT_CHARS", 100)
    def test_session_cache_capped_at_max_memory_runs(self) -> None:
        mock_store = MagicMock()
        session = _make_session()

        with patch.object(_manager_mod, "_store", mock_store):
            with patch.object(_manager_mod, "st") as mock_st:
                mock_st.session_state = session
                for i in range(1, 5):  # 4 entries, but cache cap is MAX_MEMORY_RUNS=2
                    record_analysis_memory(
                        "r{}".format(i), "url{}".format(i),
                        "t{}".format(i), "report {}".format(i)
                    )

        # In-session cache must stay at MAX_MEMORY_RUNS=2
        assert len(session.analysis_memory) == 2
        assert session.analysis_memory[0]["run_id"] == "r3"
        assert session.analysis_memory[1]["run_id"] == "r4"
