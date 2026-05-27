from datetime import UTC, datetime, timedelta

import boto3
import pytest

from services.tools.aws_observability.cloudwatch_metrics import get_lambda_metrics


@pytest.fixture
def cw_client(mock_aws_ctx):
    return boto3.client("cloudwatch", region_name="eu-west-1")


def test_get_lambda_metrics_returns_datapoints(cw_client):
    now = datetime.now(tz=UTC)
    cw_client.put_metric_data(
        Namespace="AWS/Lambda",
        MetricData=[
            {
                "MetricName": "Duration",
                "Dimensions": [{"Name": "FunctionName", "Value": "my-function"}],
                "Timestamp": now - timedelta(minutes=5),
                "Value": 28000.0,
                "Unit": "Milliseconds",
            }
        ],
    )

    result = get_lambda_metrics(
        function_name="my-function",
        metric_name="Duration",
        start_time=(now - timedelta(hours=1)).isoformat(),
        end_time=now.isoformat(),
        period_seconds=3600,
    )

    assert result["metric_name"] == "Duration"
    assert result["function_name"] == "my-function"
    assert isinstance(result["datapoints"], list)
    assert len(result["datapoints"]) == 1
    dp = result["datapoints"][0]
    assert "timestamp" in dp
    assert dp["maximum"] == 28000.0


def test_get_lambda_metrics_empty(cw_client):
    now = datetime.now(tz=UTC)

    result = get_lambda_metrics(
        function_name="no-data-function",
        metric_name="Duration",
        start_time=(now - timedelta(hours=1)).isoformat(),
        end_time=now.isoformat(),
    )

    assert result["datapoints"] == []


def test_get_lambda_metrics_datapoints_sorted(cw_client):
    now = datetime.now(tz=UTC)
    for minutes_ago in (30, 10, 20):
        cw_client.put_metric_data(
            Namespace="AWS/Lambda",
            MetricData=[
                {
                    "MetricName": "Errors",
                    "Dimensions": [{"Name": "FunctionName", "Value": "my-function"}],
                    "Timestamp": now - timedelta(minutes=minutes_ago),
                    "Value": float(minutes_ago),
                    "Unit": "Count",
                }
            ],
        )

    result = get_lambda_metrics(
        function_name="my-function",
        metric_name="Errors",
        start_time=(now - timedelta(hours=1)).isoformat(),
        end_time=now.isoformat(),
        period_seconds=600,
    )

    timestamps = [dp["timestamp"] for dp in result["datapoints"]]
    assert timestamps == sorted(timestamps)
