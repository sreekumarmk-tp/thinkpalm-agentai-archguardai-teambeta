from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class AgentSpec(BaseModel):
    id: str
    title: str
    objective: str

class AnalysisResult(BaseModel):
    agent_title: str
    model_used: str
    content: str

class FinalReport(BaseModel):
    repository_url: str
    run_id: str
    generated_at_utc: str
    report_markdown: str
    specialist_outputs: Dict[str, str]
    models_used: Dict[str, str]

class RunConfig(BaseModel):
    preset: str
    parallel_enabled: bool
    parallel_workers: int
    retry_attempts: int
    backoff_seconds: float
