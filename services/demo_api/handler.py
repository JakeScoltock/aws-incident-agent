"""Demo API Lambda — intentionally sleeps 28s to trigger the timeout alarm."""

import json
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SLOW_PATH_SLEEP_SECONDS = 28  # deliberate regression introduced in this "bad deploy"


def lambda_handler(event: dict, context: object) -> dict:
    path = event.get("rawPath", "/")
    logger.info("Request received", extra={"path": path})

    if path == "/health":
        return _response(200, {"status": "ok"})

    if path == "/slow":
        logger.warning("Entering slow path", extra={"sleep_seconds": SLOW_PATH_SLEEP_SECONDS})
        time.sleep(SLOW_PATH_SLEEP_SECONDS)
        return _response(200, {"message": "done (but slow)"})

    return _response(200, {"message": "hello from demo-api"})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
