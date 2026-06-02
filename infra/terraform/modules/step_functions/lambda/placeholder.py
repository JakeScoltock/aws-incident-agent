"""Placeholder adapter Lambda — replaced by the AgentCore runtime in Phase 4."""

import logging

logger = logging.getLogger(__name__)


def handler(event: dict, context) -> dict:
    logger.info("adapter invoked", extra={"event": event})
    return {"body": {"status": "placeholder", "confidence": 0.0, "summary": "", "pr_url": ""}}
