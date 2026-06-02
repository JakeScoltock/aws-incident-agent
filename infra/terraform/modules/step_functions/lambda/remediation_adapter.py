"""Lambda adapter: bridges Step Functions → AgentCore remediation runtime."""

import json
import logging
import os
import uuid

import boto3

logger = logging.getLogger(__name__)

RUNTIME_ID = os.environ.get("AGENTCORE_RUNTIME_ID", "")
GITHUB_REPO_SSM_NAME = os.environ.get("GITHUB_REPO_SSM_NAME", "")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")


def handler(event: dict, context) -> dict:
    if not RUNTIME_ID:
        logger.warning("AGENTCORE_RUNTIME_ID not set, returning placeholder")
        return {"body": {"status": "placeholder", "confidence": 0.0, "summary": "", "pr_url": ""}}

    github_repo = _get_github_repo()
    incident_report = event["investigation"]["body"]

    payload = {
        "incident_report": incident_report,
        "github_repo": github_repo,
        "base_branch": "main",
    }

    session_id = f"rem-{uuid.uuid4().hex[:16]}"
    logger.info(
        "invoking remediation runtime",
        extra={"session_id": session_id, "runtime_id": RUNTIME_ID},
    )

    client = boto3.client("bedrock-agentruntime", region_name=AWS_REGION)
    response = client.invoke_agent_runtime(
        agentRuntimeId=RUNTIME_ID,
        runtimeSessionId=session_id,
        payload=json.dumps(payload).encode("utf-8"),
    )

    result = _read_stream(response["completion"])
    logger.info("remediation complete", extra={"pr_url": result.get("pr_url")})
    return {"body": result}


def _get_github_repo() -> str:
    ssm = boto3.client("ssm", region_name=AWS_REGION)
    response = ssm.get_parameter(Name=GITHUB_REPO_SSM_NAME)
    return response["Parameter"]["Value"]


def _read_stream(stream) -> dict:
    chunks = []
    for event in stream:
        if "payloadChunk" in event:
            chunks.append(event["payloadChunk"]["bytes"].decode("utf-8"))
    return json.loads("".join(chunks))
