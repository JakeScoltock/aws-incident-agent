"""Lambda adapter: bridges Step Functions → AgentCore investigator runtime."""

import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger(__name__)

RUNTIME_ARN = os.environ.get("AGENTCORE_RUNTIME_ARN", "")
RUNTIME_ID = os.environ.get("AGENTCORE_RUNTIME_ID", "")  # kept for placeholder check
MONITORED_FUNCTION_NAME = os.environ.get("MONITORED_FUNCTION_NAME", "")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")


def handler(event: dict, context) -> dict:
    if not RUNTIME_ID:
        logger.warning("AGENTCORE_RUNTIME_ID not set, returning placeholder")
        return {"body": {"status": "placeholder", "confidence": 0.0, "summary": "", "pr_url": ""}}

    payload = {
        "incident_context": {
            "alarm_name": event["alarm_name"],
            "lambda_function_name": MONITORED_FUNCTION_NAME,
            "alarm_timestamp": event["triggered_at"],
            "region": event["aws_region"],
            "account_id": event["account_id"],
        }
    }

    session_id = f"inv-{uuid.uuid4().hex}"  # must be 33+ chars
    logger.info(
        "invoking investigator runtime",
        extra={"session_id": session_id, "runtime_arn": RUNTIME_ARN},
    )

    client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)
    response = client.invoke_agent_runtime(
        agentRuntimeArn=RUNTIME_ARN,
        runtimeSessionId=session_id,
        payload=json.dumps(payload).encode("utf-8"),
    )

    result = json.loads(response["response"].read())
    logger.info("investigation complete", extra={"confidence": result.get("confidence")})
    return {"body": result}
