import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from strands import tool

from services.shared.config import settings

logger = logging.getLogger(__name__)


def _convert_decimals(obj: object) -> object:
    match obj:
        case list():
            return [_convert_decimals(i) for i in obj]
        case dict():
            return {k: _convert_decimals(v) for k, v in obj.items()}
        case Decimal():
            return int(obj) if obj % 1 == 0 else float(obj)
        case _:
            return obj


@tool
def get_deployment_history(function_name: str, lookback_hours: int = 24) -> dict:
    """Retrieve recent deployment records for a Lambda from DynamoDB.
    Returns records sorted newest-first within the lookback window."""
    dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
    table = dynamodb.Table(settings.deployment_history_table)
    cutoff = (datetime.now(tz=UTC) - timedelta(hours=lookback_hours)).isoformat()

    response = table.query(
        KeyConditionExpression=Key("function_name").eq(function_name)
        & Key("deployed_at").gte(cutoff),
        ScanIndexForward=False,
    )
    records = _convert_decimals(response.get("Items", []))
    logger.info(
        "Deployment history retrieved",
        extra={"function": function_name, "count": len(records)},
    )
    return {"function_name": function_name, "deployments": records}
