from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from services.shared.models import (
    DeploymentRecord,
    IncidentContext,
    IncidentReport,
    RemediationReport,
    RemediationRequest,
)

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


def _deployment_record() -> DeploymentRecord:
    return DeploymentRecord(
        deployment_id="deploy-123",
        deployed_at=NOW,
        deployed_by="ci-bot",
        commit_sha="abc1234",
        branch="main",
    )


def _incident_report(**overrides) -> IncidentReport:
    defaults = dict(
        incident_id="inc-001",
        lambda_function_name="demo-api",
        root_cause_summary="Timeout regression from sleep(28)",
        evidence=["p99 duration spiked to 28000ms"],
        affected_files=["services/demo_api/handler.py"],
        recommended_action="Remove time.sleep(28) from slow path",
        confidence=0.9,
        created_at=NOW,
    )
    return IncidentReport(**{**defaults, **overrides})


class TestIncidentContext:
    def test_valid(self):
        ctx = IncidentContext(
            alarm_name="LambdaTimeout",
            lambda_function_name="demo-api",
            alarm_timestamp=NOW,
            region="us-east-1",
            account_id="123456789012",
        )
        assert ctx.lambda_function_name == "demo-api"


class TestIncidentReport:
    def test_valid_without_deployment(self):
        report = _incident_report()
        assert report.confidence == 0.9
        assert report.deployment_correlation is None

    def test_valid_with_deployment(self):
        report = _incident_report(deployment_correlation=_deployment_record())
        assert report.deployment_correlation.commit_sha == "abc1234"

    def test_confidence_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _incident_report(confidence=-0.1)

    def test_confidence_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _incident_report(confidence=1.1)

    def test_confidence_boundary_values(self):
        assert _incident_report(confidence=0.0).confidence == 0.0
        assert _incident_report(confidence=1.0).confidence == 1.0


class TestRemediationRequest:
    def test_defaults(self):
        req = RemediationRequest(
            incident_report=_incident_report(),
            github_repo="owner/demo-api",
        )
        assert req.base_branch == "main"

    def test_custom_base_branch(self):
        req = RemediationRequest(
            incident_report=_incident_report(),
            github_repo="owner/demo-api",
            base_branch="develop",
        )
        assert req.base_branch == "develop"


class TestRemediationReport:
    def test_valid(self):
        report = RemediationReport(
            incident_id="inc-001",
            branch_name="fix/inc-001-timeout",
            commit_sha="def5678",
            pr_url="https://github.com/owner/repo/pull/42",
            pr_number=42,
            changes_summary="Remove sleep(28) regression",
            files_modified=["services/demo_api/handler.py"],
            created_at=NOW,
        )
        assert report.pr_number == 42
