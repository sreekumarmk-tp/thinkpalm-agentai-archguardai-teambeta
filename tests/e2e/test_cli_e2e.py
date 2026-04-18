import pytest
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

from src.cli import main, load_memory, save_memory, build_memory_context

@pytest.fixture
def clean_memory_file(tmp_path):
    mem_file = tmp_path / ".agent_memory_cli.json"
    yield mem_file

def test_load_save_memory(clean_memory_file):
    runs = [{"run_id": "123", "repo_url": "http://x", "generated_at_utc": "time", "report_excerpt": "rep"}]
    save_memory(clean_memory_file, runs)
    loaded = load_memory(clean_memory_file)
    assert loaded == runs

def test_build_memory_context():
    runs = [{"run_id": "123", "repo_url": "http://x", "generated_at_utc": "time", "report_excerpt": "rep"}]
    ctx = build_memory_context(runs)
    assert "Previous analysis memory" in ctx
    assert "123" in ctx

@patch('src.cli.parse_github_repo')
@patch('src.cli.fetch_available_free_models')
@patch('src.cli.run_specialist_agent_with_retries')
@patch('src.cli.synthesize_report')
def test_cli_main_success(
    mock_synthesize_report,
    mock_run_specialist,
    mock_fetch_models,
    mock_parse_github,
    tmp_path,
    monkeypatch
):
    # Set required environment variables
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-12345")
    
    # Mocking outputs
    mock_fetch_models.return_value = {"model1"}
    mock_run_specialist.return_value = ("Specialist Output", "model1")
    mock_synthesize_report.return_value = "# Final Report\nMarkdown content"
    
    output_prefix = str(tmp_path / "test_report")
    memory_file = str(tmp_path / "mem.json")
    
    # Mock sys.argv
    test_args = ["cli.py", "--repo-url", "https://github.com/user/repo", "--output-prefix", output_prefix, "--memory-file", memory_file]
    
    with patch.object(sys, 'argv', test_args):
        # main() returns an integer exit code rather than raising SystemExit
        exit_code = main()
        assert exit_code == 0
        
    # Check outputs created
    md_path = Path(f"{output_prefix}.md")
    json_path = Path(f"{output_prefix}.json")
    
    assert md_path.exists()
    assert "# Final Report" in md_path.read_text("utf-8")
    
    assert json_path.exists()
    data = json.loads(json_path.read_text("utf-8"))
    assert data["repository"] == "https://github.com/user/repo"
    assert "Specialist Output" in str(data["specialist_outputs"])
    
    assert Path(memory_file).exists()
    memory_data = json.loads(Path(memory_file).read_text("utf-8"))
    assert len(memory_data) == 1
    assert memory_data[0]["repo_url"] == "https://github.com/user/repo"
