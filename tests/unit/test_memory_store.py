"""Unit tests for src.memory.store.SQLiteMemoryStore."""

import pytest
from pathlib import Path
from src.memory.store import SQLiteMemoryStore


@pytest.fixture()
def store(tmp_path: Path) -> SQLiteMemoryStore:
    """Return a fresh in-tmp-dir SQLiteMemoryStore for each test."""
    return SQLiteMemoryStore(tmp_path / "test_memory.db")


def _make_entry(n: int) -> dict:
    return {
        "run_id": f"run-{n:04d}",
        "repo_url": f"https://github.com/owner/repo-{n}",
        "generated_at_utc": f"2026-04-{n:02d}T00:00:00+00:00",
        "report_excerpt": f"Excerpt for run {n}",
    }


class TestSQLiteMemoryStoreInit:
    def test_creates_db_file(self, tmp_path: Path) -> None:
        db_path = tmp_path / "sub" / "memory.db"
        SQLiteMemoryStore(db_path)
        assert db_path.exists(), "DB file should be created on init"

    def test_idempotent_reinit(self, tmp_path: Path) -> None:
        """Constructing store twice on same path must not raise."""
        db_path = tmp_path / "memory.db"
        SQLiteMemoryStore(db_path)
        SQLiteMemoryStore(db_path)  # should not raise


class TestSQLiteMemoryStoreAppendAndLoad:
    def test_load_empty_store(self, store: SQLiteMemoryStore) -> None:
        assert store.load(10) == []

    def test_append_and_load_single(self, store: SQLiteMemoryStore) -> None:
        entry = _make_entry(1)
        store.append(entry)
        rows = store.load(10)
        assert len(rows) == 1
        assert rows[0]["run_id"] == "run-0001"
        assert rows[0]["repo_url"] == entry["repo_url"]
        assert rows[0]["report_excerpt"] == entry["report_excerpt"]

    def test_append_multiple_preserves_order(self, store: SQLiteMemoryStore) -> None:
        for i in range(1, 6):
            store.append(_make_entry(i))
        rows = store.load(10)
        assert len(rows) == 5
        # Should be oldest → newest
        assert rows[0]["run_id"] == "run-0001"
        assert rows[4]["run_id"] == "run-0005"

    def test_load_respects_limit(self, store: SQLiteMemoryStore) -> None:
        for i in range(1, 11):
            store.append(_make_entry(i))
        rows = store.load(3)
        assert len(rows) == 3
        # With limit=3, the 3 most-recent rows are returned (oldest-first)
        assert rows[0]["run_id"] == "run-0008"
        assert rows[2]["run_id"] == "run-0010"

    def test_duplicate_run_id_is_ignored(self, store: SQLiteMemoryStore) -> None:
        entry = _make_entry(1)
        store.append(entry)
        store.append(entry)  # duplicate — should be silently ignored
        assert len(store.load(10)) == 1

    def test_missing_report_excerpt_defaults_to_empty(self, store: SQLiteMemoryStore) -> None:
        entry = {
            "run_id": "no-excerpt",
            "repo_url": "https://github.com/a/b",
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
        }
        store.append(entry)
        rows = store.load(10)
        assert rows[0]["report_excerpt"] == ""


class TestSQLiteMemoryStorePrune:
    def test_prune_keeps_n_most_recent(self, store: SQLiteMemoryStore) -> None:
        for i in range(1, 8):
            store.append(_make_entry(i))
        store.prune(keep=3)
        rows = store.load(10)
        assert len(rows) == 3
        run_ids = [r["run_id"] for r in rows]
        assert "run-0007" in run_ids
        assert "run-0001" not in run_ids

    def test_prune_noop_when_under_limit(self, store: SQLiteMemoryStore) -> None:
        for i in range(1, 4):
            store.append(_make_entry(i))
        store.prune(keep=5)
        assert len(store.load(10)) == 3

    def test_prune_to_zero(self, store: SQLiteMemoryStore) -> None:
        for i in range(1, 4):
            store.append(_make_entry(i))
        store.prune(keep=0)
        assert store.load(10) == []


class TestSQLiteMemoryStorePersistence:
    def test_data_survives_reinstantiation(self, tmp_path: Path) -> None:
        """Key cross-session test: data written by one store instance must be
        readable by a fresh instance pointing to the same DB file."""
        db_path = tmp_path / "memory.db"
        store_a = SQLiteMemoryStore(db_path)
        store_a.append(_make_entry(1))
        store_a.append(_make_entry(2))

        # Simulate a new process / Streamlit session
        store_b = SQLiteMemoryStore(db_path)
        rows = store_b.load(10)
        assert len(rows) == 2
        assert rows[0]["run_id"] == "run-0001"
        assert rows[1]["run_id"] == "run-0002"
