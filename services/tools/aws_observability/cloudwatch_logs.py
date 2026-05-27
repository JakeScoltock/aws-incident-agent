import logging
import time
from datetime import datetime

import boto3
from strands import tool

from services.shared.config import settings

logger = logging.getLogger(__name__)

_POLL_INTERVAL = 1
_MAX_WAIT_SECONDS = 60


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@tool
def query_lambda_logs(
    function_name: str,
    query: str,
    start_time: str,
    end_time: str,
    limit: int = 100,
) -> dict:
    """Run a CloudWatch Logs Insights query against a Lambda log group.
    query: CloudWatch Logs Insights query string, e.g. 'fields @timestamp, @message | limit 20'
    start_time/end_time: ISO 8601 strings"""
    client = boto3.client("logs", region_name=settings.aws_region)
    log_group = f"/aws/lambda/{function_name}"
    start_ts = int(_parse_iso(start_time).timestamp())
    end_ts = int(_parse_iso(end_time).timestamp())

    start_response = client.start_query(
        logGroupName=log_group,
        startTime=start_ts,
        endTime=end_ts,
        queryString=query,
        limit=limit,
    )
    query_id = start_response["queryId"]

    elapsed = 0
    result: dict = {}
    try:
        while elapsed < _MAX_WAIT_SECONDS:
            result = client.get_query_results(queryId=query_id)
            status = result["status"]
            if status in ("Complete", "Failed", "Cancelled", "Timeout"):
                break
            time.sleep(_POLL_INTERVAL)
            elapsed += _POLL_INTERVAL
        else:
            client.stop_query(queryId=query_id)
            result = {"status": "AgentTimeout", "results": [], "statistics": {}}
    except Exception:
        client.stop_query(queryId=query_id)
        raise

    rows = [{field["field"]: field["value"] for field in row} for row in result.get("results", [])]
    logger.info(
        "CloudWatch Logs Insights query complete",
        extra={"function": function_name, "status": result.get("status"), "rows": len(rows)},
    )
    return {
        "log_group": log_group,
        "status": result.get("status"),
        "results": rows,
        "statistics": result.get("statistics", {}),
    }
