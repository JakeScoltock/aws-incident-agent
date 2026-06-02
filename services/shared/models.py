from datetime import datetime

from pydantic import BaseModel, Field


class IncidentContext(BaseModel):
    alarm_name: str
    lambda_function_name: str
    alarm_timestamp: datetime
    region: str
    account_id: str


class DeploymentRecord(BaseModel):
    deployment_id: str
    deployed_at: datetime
    deployed_by: str
    commit_sha: str
    branch: str


class IncidentReport(BaseModel):
    incident_id: str
    lambda_function_name: str
    root_cause_summary: str
    evidence: list[str]
    deployment_correlation: DeploymentRecord | None = None
    affected_files: list[str]
    recommended_action: str
    confidence: float = Field(ge=0.0, le=1.0)
    created_at: datetime


class RemediationRequest(BaseModel):
    incident_report: IncidentReport
    github_repo: str  # "owner/repo"
    base_branch: str = "main"


class RemediationReport(BaseModel):
    incident_id: str
    branch_name: str
    commit_sha: str
    pr_url: str
    pr_number: int
    changes_summary: str
    files_modified: list[str]
    created_at: datetime
