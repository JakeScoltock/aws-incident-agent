import json
import sys
from unittest.mock import MagicMock, patch

# The adapter lives outside the package root; add its directory to sys.path
ADAPTER_DIR = (
    __file__  # tests/unit/agents/test_investigator_adapter.py
    and __import__("pathlib").Path(__file__).parents[3]
    / "infra/terraform/modules/step_functions/lambda"
)
sys.path.insert(0, str(ADAPTER_DIR))

import investigator_adapter  # noqa: E402

SAMPLE_EVENT = {
    "alarm_name": "incident-agent-dev-duration",
    "alarm_state": "ALARM",
    "alarm_reason": "Threshold crossed",
    "account_id": "123456789012",
    "aws_region": "eu-west-1",
    "triggered_at": "2024-01-01T12:00:00Z",
}

SAMPLE_REPORT = {
    "incident_id": "INC-test-123",
    "lambda_function_name": "incident-agent-demo-api-dev",
    "root_cause_summary": "Lambda timeout due to sleep(28)",
    "evidence": ["Duration p99 = 28.5s"],
    "deployment_correlation": None,
    "affected_files": ["services/demo_api/handler.py"],
    "recommended_action": "Remove time.sleep(28) from handler",
    "confidence": 0.9,
    "created_at": "2024-01-01T12:01:00Z",
}


def _make_stream(payload: dict):
    """Build a minimal EventStream mock returning one payloadChunk."""
    chunk = {"payloadChunk": {"bytes": json.dumps(payload).encode("utf-8")}}
    return iter([chunk])


def test_handler_calls_invoke_and_returns_body():
    mock_client = MagicMock()
    mock_client.invoke_agent_runtime.return_value = {"completion": _make_stream(SAMPLE_REPORT)}

    with (
        patch.object(investigator_adapter, "RUNTIME_ID", "runtime-abc"),
        patch.object(
            investigator_adapter,
            "RUNTIME_ARN",
            "arn:aws:bedrock-agentcore:eu-west-1:123456789012:runtime/runtime-abc",
        ),
        patch.object(
            investigator_adapter, "MONITORED_FUNCTION_NAME", "incident-agent-demo-api-dev"
        ),
        patch("investigator_adapter.boto3") as mock_boto3,
    ):
        mock_boto3.client.return_value = mock_client
        result = investigator_adapter.handler(SAMPLE_EVENT, None)

    assert result == {"body": SAMPLE_REPORT}
    mock_client.invoke_agent_runtime.assert_called_once()
    call_kwargs = mock_client.invoke_agent_runtime.call_args.kwargs
    assert (
        call_kwargs["agentRuntimeArn"]
        == "arn:aws:bedrock-agentcore:eu-west-1:123456789012:runtime/runtime-abc"
    )
    assert len(call_kwargs["runtimeSessionId"]) >= 33
    payload = json.loads(call_kwargs["payload"])
    assert payload["incident_context"]["alarm_name"] == "incident-agent-dev-duration"
    assert payload["incident_context"]["lambda_function_name"] == "incident-agent-demo-api-dev"


def test_handler_returns_placeholder_when_runtime_id_unset():
    with patch.object(investigator_adapter, "RUNTIME_ID", ""):
        result = investigator_adapter.handler(SAMPLE_EVENT, None)
    assert result["body"]["status"] == "placeholder"
    assert result["body"]["confidence"] == 0.0


def test_read_stream_reassembles_chunks():
    part1 = '{"incident_id":'
    part2 = ' "INC-1"}'
    stream = [
        {"payloadChunk": {"bytes": part1.encode()}},
        {"payloadChunk": {"bytes": part2.encode()}},
    ]
    result = investigator_adapter._read_stream(iter(stream))
    assert result == {"incident_id": "INC-1"}


def test_read_stream_ignores_unknown_event_types():
    stream = [
        {"otherEvent": {}},
        {"payloadChunk": {"bytes": b'{"ok": true}'}},
    ]
    result = investigator_adapter._read_stream(iter(stream))
    assert result == {"ok": True}
