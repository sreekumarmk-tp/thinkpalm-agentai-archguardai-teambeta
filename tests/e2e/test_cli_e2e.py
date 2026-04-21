import json
import os
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from src.memory.manager import build_memory_context


def test_build_memory_context():
    runs = [
        {
            "run_id": "123",
            "repo_url": "http://x",
            "generated_at_utc": "time",
            "report_excerpt": "rep",
        }
    ]
    ctx = build_memory_context(runs)
    assert "Previous analysis memory" in ctx
    assert "123" in ctx


@patch("src.cli.parse_github_repo")
@patch("src.cli.fetch_available_openrouter_models")
@patch("src.cli.fetch_available_groq_models")
@patch("src.cli.SpecialistFactory.run_agent_with_retries")
@patch("src.cli.synthesize_report")
def test_cli_main_success(
    mock_synthesize_report,
    mock_run_specialist,
    mock_fetch_groq,
    mock_fetch_or,
    mock_parse_github,
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-12345")

    mock_fetch_or.return_value = {"model1:free"}
    mock_fetch_groq.return_value = {"llama3-8b-8192"}
    mock_run_specialist.return_value = ("Specialist Output", "model1")
    mock_synthesize_report.return_value = "# Final Report\nMarkdown content"

    output_prefix = str(tmp_path / "test_report")
    memory_db = str(tmp_path / "mem.db")

    test_args = [
        "cli.py",
        "--repo-url",
        "https://github.com/user/repo",
        "--output-prefix",
        output_prefix,
        "--memory-db",
        memory_db,
        "--provider",
        "openrouter",
        "--sequential",
    ]

    from src.cli import main

    with patch.object(sys, "argv", test_args):
        exit_code = main()
        assert exit_code == 0

    md_path = Path(f"{output_prefix}.md")
    json_path = Path(f"{output_prefix}.json")
    docx_path = Path(f"{output_prefix}.docx")

    assert md_path.exists()
    assert "# Final Report" in md_path.read_text("utf-8")

    assert json_path.exists()
    data = json.loads(json_path.read_text("utf-8"))
    assert data["repository"] == "https://github.com/user/repo"
    assert "Specialist Output" in str(data["specialist_outputs"])
    assert data["run_configuration"]["llm_provider"] == "openrouter"
    assert data["run_configuration"]["parallel_enabled"] is False
    assert "run_metadata" in data

    assert docx_path.exists()
    assert docx_path.read_bytes()[:2] == b"PK"

    assert Path(memory_db).exists()
    conn = sqlite3.connect(memory_db)
    try:
        row = conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()
        assert row[0] == 1
    finally:
        conn.close()
