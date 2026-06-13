#!/usr/bin/env python3
"""Create or update an AgentCore Runtime. Called by Terraform null_resource local-exec.

Environment variables (set by Terraform):
    RUNTIME_NAME   AgentCore runtime name (e.g. incident_agent_investigator_dev)
    IMAGE_URI      Full ECR image URI including tag
    ROLE_ARN       IAM execution role ARN
    AWS_REGION     AWS region
"""

import os
import time

import boto3

RUNTIME_NAME = os.environ["RUNTIME_NAME"]
IMAGE_URI = os.environ["IMAGE_URI"]
ROLE_ARN = os.environ["ROLE_ARN"]
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")

ARTIFACT = {"containerConfiguration": {"containerUri": IMAGE_URI}}
NETWORK_CONFIG = {"networkMode": "PUBLIC"}
PROTOCOL_CONFIG = {"serverProtocol": "HTTP"}


def _wait_ready(client, runtime_id: str, max_wait: int = 180) -> None:
    deadline = time.time() + max_wait
    while time.time() < deadline:
        resp = client.get_agent_runtime(agentRuntimeId=runtime_id)
        status = resp["agentRuntimeStatus"]
        print(f"  status: {status}", flush=True)
        if status == "READY":
            return
        if "FAILED" in status:
            raise SystemExit(f"Runtime entered failed state: {status}")
        time.sleep(5)
    raise SystemExit(f"Timed out waiting for runtime {runtime_id} to be READY")


def main() -> None:
    client = boto3.client("bedrock-agentcore-control", region_name=AWS_REGION)

    print(f"Managing runtime: {RUNTIME_NAME}", flush=True)
    print(f"  image: {IMAGE_URI}", flush=True)

    existing = [
        r
        for r in client.list_agent_runtimes()["agentRuntimes"]
        if r["agentRuntimeName"] == RUNTIME_NAME
    ]

    if existing:
        runtime_id = existing[0]["agentRuntimeId"]
        print(f"  found {runtime_id} — updating", flush=True)
        client.update_agent_runtime(
            agentRuntimeId=runtime_id,
            agentRuntimeArtifact=ARTIFACT,
            roleArn=ROLE_ARN,
            networkConfiguration=NETWORK_CONFIG,
            protocolConfiguration=PROTOCOL_CONFIG,
        )
    else:
        print("  not found — creating", flush=True)
        resp = client.create_agent_runtime(
            agentRuntimeName=RUNTIME_NAME,
            agentRuntimeArtifact=ARTIFACT,
            roleArn=ROLE_ARN,
            networkConfiguration=NETWORK_CONFIG,
            protocolConfiguration=PROTOCOL_CONFIG,
        )
        runtime_id = resp["agentRuntimeId"]
        print(f"  created: {resp['agentRuntimeArn']}", flush=True)

    _wait_ready(client, runtime_id)
    print("  READY", flush=True)


if __name__ == "__main__":
    main()
