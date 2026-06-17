"""Demo API Lambda — handles /health, /slow, and default routes."""

import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Maximum time (seconds) the slow path is permitted to simulate work.
# Previously this was set to 28 s (a deliberate regression that triggered the
# Lambda duration alarm INC-incident-agent-dev-lambda-duration-1750189004).
# The value is now capped at 1 s so the function stays well within its timeout.
SLOW_PATH_SLEEP_SECONDS = 1  # fix: removed 28-second blocking sleep regression


def lambda_handler(event: dict, context: object) -> dict:
    path = event.get("rawPath", "/")
    logger.info("Request received", extra={"path": path})

    if path == "/health":
        return _response(200, {"status": "ok"})

    if path == "/slow":
        # Guard: never sleep longer than the configured cap.
        import time  # imported here to keep the top-level import surface minimal

        capped = min(SLOW_PATH_SLEEP_SECONDS, 1)
        logger.info(
            "Entering slow path",
            extra={"sleep_seconds": capped},
        )
        time.sleep(capped)
        return _response(200, {"message": "done (slow path, capped)"})

    return _response(200, {"message": "hello from demo-api"})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
