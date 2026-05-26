import logging

logger = logging.getLogger(__name__)


def get_lambda_metrics(
    function_name: str,
    metric_name: str,
    start_time: str,
    end_time: str,
    period_seconds: int = 300,
) -> dict:
    """Query CloudWatch metrics for a Lambda function.

    metric_name: Duration | Errors | Throttles | Invocations
    start_time/end_time: ISO 8601 strings
    """
    raise NotImplementedError("Implement in Phase 3")
