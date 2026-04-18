import pytest
from src.schemas.models import AgentSpec, AnalysisResult, FinalReport, RunConfig

def test_agent_spec():
    spec = AgentSpec(id="agent1", title="Agent One", objective="Test objective")
    assert spec.id == "agent1"
    assert spec.title == "Agent One"
    assert spec.objective == "Test objective"

def test_analysis_result():
    res = AnalysisResult(agent_title="Agent", model_used="model-1", content="content")
    assert res.agent_title == "Agent"
    assert res.model_used == "model-1"
    assert res.content == "content"

def test_final_report():
    report = FinalReport(
        repository_url="http://r", 
        run_id="run-1", 
        generated_at_utc="time", 
        report_markdown="md", 
        specialist_outputs={"a": "b"}, 
        models_used={"c": "d"}
    )
    assert report.repository_url == "http://r"
    assert report.run_id == "run-1"
    assert report.report_markdown == "md"
    assert report.specialist_outputs["a"] == "b"
    assert report.models_used["c"] == "d"

def test_run_config():
    config = RunConfig(preset="Reliable", parallel_enabled=True, parallel_workers=3, retry_attempts=2, backoff_seconds=1.5)
    assert config.preset == "Reliable"
    assert config.parallel_enabled == True
    assert config.parallel_workers == 3
    assert config.retry_attempts == 2
    assert config.backoff_seconds == 1.5
