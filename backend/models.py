from datetime import datetime
from pydantic import BaseModel, Field

class GitHubActionsEvent(BaseModel):
    workflow: str
    run_id: str
    repository: str
    branch: str
    status: str
    conclusion: str | None = None
    triggered_by: str
    duration_ms: int = Field(ge=0)
    started_at: datetime
    finished_at: datetime

class JenkinsEvent(BaseModel):
    job_name: str
    build_number: int
    status: str
    duration_ms: int = Field(ge=0)
    git_branch: str | None = None
    git_commit: str | None = None
    triggered_by: str | None = None
    started_at: datetime
    finished_at: datetime
