"""
SQLite-backed cross-session memory store for ArchGuard AI.

All analysis runs are persisted in a local SQLite database so that
history survives Streamlit reruns, browser refreshes, and completely
new sessions.  The public interface intentionally mirrors the in-memory
list-of-dicts schema used throughout the codebase, so callers stay
unchanged.
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, List

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------
_DDL = """
CREATE TABLE IF NOT EXISTS analysis_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          TEXT    NOT NULL UNIQUE,
    repo_url        TEXT    NOT NULL,
    generated_at_utc TEXT   NOT NULL,
    report_excerpt  TEXT    NOT NULL DEFAULT '',
    created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_analysis_runs_created
    ON analysis_runs (created_at DESC);
"""


class SQLiteMemoryStore:
    """Thread-safe, file-backed memory store using stdlib sqlite3.

    Args:
        db_path: Filesystem path for the SQLite database file.
                 The parent directory is created automatically.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a connection with WAL mode for better concurrency."""
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create tables and indexes on first use."""
        try:
            with self._connect() as conn:
                conn.executescript(_DDL)
        except Exception as exc:
            logger.error("Failed to initialise SQLite schema: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, entry: Dict[str, str]) -> None:
        """Persist a single analysis-run entry.

        Args:
            entry: Dict with keys ``run_id``, ``repo_url``,
                   ``generated_at_utc``, and ``report_excerpt``.
        """
        sql = """
            INSERT OR IGNORE INTO analysis_runs
                (run_id, repo_url, generated_at_utc, report_excerpt)
            VALUES (?, ?, ?, ?)
        """
        try:
            with self._connect() as conn:
                conn.execute(
                    sql,
                    (
                        entry["run_id"],
                        entry["repo_url"],
                        entry["generated_at_utc"],
                        entry.get("report_excerpt", ""),
                    ),
                )
        except Exception as exc:
            logger.error("Failed to persist analysis run %s: %s", entry.get("run_id"), exc)
            raise

    def load(self, limit: int) -> List[Dict[str, str]]:
        """Return the *limit* most-recent runs as a list of dicts.

        Args:
            limit: Maximum number of rows to return (newest first,
                   then reversed so callers receive oldest → newest).

        Returns:
            List of dicts with keys matching the in-memory schema.
        """
        sql = """
            SELECT run_id, repo_url, generated_at_utc, report_excerpt
            FROM analysis_runs
            ORDER BY id DESC
            LIMIT ?
        """
        try:
            with self._connect() as conn:
                rows = conn.execute(sql, (limit,)).fetchall()
            # Reverse so index 0 is oldest, matching the in-memory convention
            return [dict(r) for r in reversed(rows)]
        except Exception as exc:
            logger.error("Failed to load analysis memory: %s", exc)
            return []

    def prune(self, keep: int) -> None:
        """Delete older runs, retaining the *keep* most recent ones.

        Args:
            keep: Number of most-recent rows to retain.
        """
        sql = """
            DELETE FROM analysis_runs
            WHERE id NOT IN (
                SELECT id FROM analysis_runs
                ORDER BY id DESC
                LIMIT ?
            )
        """
        try:
            with self._connect() as conn:
                conn.execute(sql, (keep,))
        except Exception as exc:
            logger.error("Failed to prune analysis memory: %s", exc)
