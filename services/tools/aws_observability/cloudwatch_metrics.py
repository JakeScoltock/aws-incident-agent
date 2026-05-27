import logging
from datetime import datetime

import boto3
from strands import tool

from services.shared.config import settings

logger = logging.getLogger(__name__)


def _parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


@tool
def get_lambda_metrics(
    function_name: str,
    metric_name: str,
    start_time: str,
    end_time: str,
    period_seconds: int = 300,
) -> dict:
    """Query CloudWatch metrics for a Lambda function.
    metric_name: Duration | Errors | Throttles | Invocations
    start_time/end_time: ISO 8601 strings"""
    client = boto3.client("cloudwatch", region_name=settings.aws_region)
    response = client.get_metric_statistics(
        Namespace="AWS/Lambda",
        MetricName=metric_name,
        Dimensions=[{"Name": "FunctionName", "Value": function_name}],
        StartTime=_parse_iso(start_time),
        EndTime=_parse_iso(end_time),
        Period=period_seconds,
        Statistics=["Average", "Maximum", "Sum", "SampleCount"],
    )
    datapoints = sorted(
        [
            {
                "timestamp": dp["Timestamp"].isoformat(),
                "average": dp.get("Average"),
                "maximum": dp.get("Maximum"),
                "sum": dp.get("Sum"),
                "sample_count": dp.get("SampleCount"),
                "unit": dp.get("Unit"),
            }
            for dp in response["Datapoints"]
        ],
        key=lambda x: x["timestamp"],
    )
    logger.info(
        "CloudWatch metrics retrieved",
        extra={"function": function_name, "metric": metric_name, "count": len(datapoints)},
    )
    return {"metric_name": metric_name, "function_name": function_name, "datapoints": datapoints}
