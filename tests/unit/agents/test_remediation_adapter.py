import json
import sys
from unittest.mock import MagicMock, patch

ADAPTER_DIR = (
    __file__
    and __import__("pathlib").Path(__file__).parents[3]
    / "infra/terraform/modules/step_functions/lambda"
)
sys.path.insert(0, str(ADAPTER_DIR))

import remediation_adapter  # noqa: E402

SAMPLE_INCIDENT_REPORT = {
    "incident_id": "INC-test-123",
    "lambda_function_name": "incident-agent-demo-api-dev",
    "root_cause_summary": "Lambda timeout due to sleep(28)",
    "evidence": ["Duration p99 = 28.5s"],
    "deployment_correlation": None,
    "affected_files": ["services/demo_api/handler.py"],
    "recommended_action": "Remove time.sleep(28)",
    "confidence": 0.9,
    "created_at": "2024-01-01T12:01:00Z",
}

SAMPLE_EVENT = {
    "alarm_name": "incident-agent-dev-duration",
    "account_id": "123456789012",
    "aws_region": "eu-west-1",
    "triggered_at": "2024-01-01T12:00:00Z",
    "investigation": {"body": SAMPLE_INCIDENT_REPORT},
}

SAMPLE_REMEDIATION = {
    "incident_id": "INC-test-123",
    "branch_name": "fix/incident-INC-test-123",
    "commit_sha": "abc123",
    "pr_url": "https://github.com/owner/repo/pull/42",
    "pr_number": 42,
    "changes_summary": "Removed time.sleep(28) from demo handler",
    "files_modified": ["services/demo_api/handler.py"],
    "created_at": "2024-01-01T12:05:00Z",
}


def _make_stream(payload: dict):
    chunk = {"payloadChunk": {"bytes": json.dumps(payload).encode("utf-8")}}
    return iter([chunk])


def test_handler_fetches_repo_and_invokes_runtime():
    mock_ssm = MagicMock()
    mock_ssm.get_parameter.return_value = {"Parameter": {"Value": "owner/repo"}}

    mock_runtime = MagicMock()
    mock_runtime.invoke_agent_runtime.return_value = {
        "completion": _make_stream(SAMPLE_REMEDIATION)
    }

    def make_client(service, **kwargs):
        return mock_ssm if service == "ssm" else mock_runtime

    with (
        patch.object(remediation_adapter, "RUNTIME_ID", "runtime-xyz"),
        patch.object(
            remediation_adapter, "GITHUB_REPO_SSM_NAME", "/incident-agent/dev/github-repo"
        ),  # noqa: E501
        patch("remediation_adapter.boto3") as mock_boto3,
    ):
        mock_boto3.client.side_effect = make_client
        result = remediation_adapter.handler(SAMPLE_EVENT, None)

    assert result == {"body": SAMPLE_REMEDIATION}
    mock_ssm.get_parameter.assert_called_once_with(Name="/incident-agent/dev/github-repo")

    call_kwargs = mock_runtime.invoke_agent_runtime.call_args.kwargs
    assert call_kwargs["agentRuntimeId"] == "runtime-xyz"
    payload = json.loads(call_kwargs["payload"])
    assert payload["github_repo"] == "owner/repo"
    assert payload["incident_report"]["incident_id"] == "INC-test-123"


def test_handler_returns_placeholder_when_runtime_id_unset():
    with patch.object(remediation_adapter, "RUNTIME_ID", ""):
        result = remediation_adapter.handler(SAMPLE_EVENT, None)
    assert result["body"]["status"] == "placeholder"
    assert result["body"]["confidence"] == 0.0
