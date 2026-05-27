from datetime import UTC, datetime, timedelta

import boto3
import pytest

from services.tools.aws_observability.deployment_history import get_deployment_history


@pytest.fixture
def dynamodb_table(mock_aws_ctx):
    dynamodb = boto3.resource("dynamodb", region_name="eu-west-1")
    table = dynamodb.create_table(
        TableName="incident-agent-deployment-history",
        KeySchema=[
            {"AttributeName": "function_name", "KeyType": "HASH"},
            {"AttributeName": "deployed_at", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "function_name", "AttributeType": "S"},
            {"AttributeName": "deployed_at", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    return table


def _make_record(function_name: str, hours_ago: float, deploy_id: str) -> dict:
    ts = (datetime.now(tz=UTC) - timedelta(hours=hours_ago)).isoformat()
    return {
        "function_name": function_name,
        "deployed_at": ts,
        "deployment_id": deploy_id,
        "deployed_by": "github-actions",
        "commit_sha": f"sha_{deploy_id}",
        "branch": "main",
    }


def test_get_deployment_history_returns_records(dynamodb_table):
    dynamodb_table.put_item(Item=_make_record("my-function", hours_ago=2, deploy_id="deploy-1"))
    dynamodb_table.put_item(Item=_make_record("my-function", hours_ago=4, deploy_id="deploy-2"))

    result = get_deployment_history("my-function", lookback_hours=24)

    assert result["function_name"] == "my-function"
    assert len(result["deployments"]) == 2
    deploy_ids = {d["deployment_id"] for d in result["deployments"]}
    assert deploy_ids == {"deploy-1", "deploy-2"}


def test_get_deployment_history_empty(dynamodb_table):
    result = get_deployment_history("no-deployments", lookback_hours=24)

    assert result["function_name"] == "no-deployments"
    assert result["deployments"] == []


def test_get_deployment_history_respects_lookback(dynamodb_table):
    dynamodb_table.put_item(Item=_make_record("my-function", hours_ago=2, deploy_id="recent"))
    dynamodb_table.put_item(Item=_make_record("my-function", hours_ago=30, deploy_id="old"))

    result = get_deployment_history("my-function", lookback_hours=24)

    assert len(result["deployments"]) == 1
    assert result["deployments"][0]["deployment_id"] == "recent"


def test_get_deployment_history_different_function(dynamodb_table):
    dynamodb_table.put_item(Item=_make_record("fn-a", hours_ago=1, deploy_id="a-deploy"))
    dynamodb_table.put_item(Item=_make_record("fn-b", hours_ago=1, deploy_id="b-deploy"))

    result = get_deployment_history("fn-a", lookback_hours=24)

    assert len(result["deployments"]) == 1
    assert result["deployments"][0]["deployment_id"] == "a-deploy"
