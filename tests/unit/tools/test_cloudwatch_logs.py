from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import boto3
import pytest

from services.tools.aws_observability.cloudwatch_logs import query_lambda_logs


@pytest.fixture
def logs_client(mock_aws_ctx):
    client = boto3.client("logs", region_name="eu-west-1")
    client.create_log_group(logGroupName="/aws/lambda/my-function")
    client.create_log_stream(
        logGroupName="/aws/lambda/my-function", logStreamName="2024/01/01/[$LATEST]abc"
    )
    return client


def test_query_lambda_logs_structure(logs_client):
    now = datetime.now(tz=UTC)

    result = query_lambda_logs(
        function_name="my-function",
        query="fields @timestamp, @message | limit 10",
        start_time=(now - timedelta(hours=1)).isoformat(),
        end_time=now.isoformat(),
    )

    assert result["log_group"] == "/aws/lambda/my-function"
    assert result["status"] in ("Complete", "Failed", "Cancelled", "Timeout")
    assert isinstance(result["results"], list)
    assert isinstance(result["statistics"], dict)


def test_query_lambda_logs_with_events(logs_client):
    now = datetime.now(tz=UTC)
    logs_client.put_log_events(
        logGroupName="/aws/lambda/my-function",
        logStreamName="2024/01/01/[$LATEST]abc",
        logEvents=[
            {
                "timestamp": int((now - timedelta(minutes=5)).timestamp() * 1000),
                "message": "REPORT RequestId: abc Duration: 28000 ms",
            },
            {
                "timestamp": int((now - timedelta(minutes=4)).timestamp() * 1000),
                "message": "Task timed out after 28.00 seconds",
            },
        ],
    )

    result = query_lambda_logs(
        function_name="my-function",
        query="fields @timestamp, @message | filter @message like /timed out/",
        start_time=(now - timedelta(hours=1)).isoformat(),
        end_time=now.isoformat(),
    )

    assert result["log_group"] == "/aws/lambda/my-function"
    assert isinstance(result["results"], list)


def test_query_lambda_logs_iso_z_suffix(logs_client):
    result = query_lambda_logs(
        function_name="my-function",
        query="fields @timestamp | limit 1",
        start_time="2024-01-01T00:00:00Z",
        end_time="2024-01-01T01:00:00Z",
    )

    assert result["log_group"] == "/aws/lambda/my-function"


def test_query_lambda_logs_timeout_returns_agent_timeout_status(mock_aws_ctx):
    """When poll loop exhausts _MAX_WAIT_SECONDS the query is cancelled and
    status 'AgentTimeout' is returned instead of a misleading 'Running'."""
    client = boto3.client("logs", region_name="eu-west-1")
    client.create_log_group(logGroupName="/aws/lambda/slow-function")

    always_running = {"status": "Running", "results": [], "statistics": {}}

    with patch("services.tools.aws_observability.cloudwatch_logs.boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        mock_client.start_query.return_value = {"queryId": "q-123"}
        mock_client.get_query_results.return_value = always_running

        with patch("services.tools.aws_observability.cloudwatch_logs._MAX_WAIT_SECONDS", 0):
            now = datetime.now(tz=UTC)
            result = query_lambda_logs(
                function_name="slow-function",
                query="fields @message",
                start_time=(now - timedelta(hours=1)).isoformat(),
                end_time=now.isoformat(),
            )

    assert result["status"] == "AgentTimeout"
    assert result["results"] == []
    mock_client.stop_query.assert_called_once_with(queryId="q-123")
