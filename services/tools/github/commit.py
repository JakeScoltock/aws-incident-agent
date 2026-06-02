import base64
import logging

import httpx
from strands import tool

from ._client import GITHUB_API_BASE, github_headers

logger = logging.getLogger(__name__)


@tool
def commit_file_to_github(repo: str, branch: str, path: str, content: str, message: str) -> dict:
    """Commit a file change to a GitHub branch.
    repo: owner/repo format. content: raw file text (not base64-encoded).
    Creates the file if it does not exist; updates it otherwise."""
    headers = github_headers()

    existing_sha: str | None = None
    existing = httpx.get(
        f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}",
        headers=headers,
        params={"ref": branch},
    )
    if existing.status_code == 200:
        existing_sha = existing.json().get("sha")
    elif existing.status_code != 404:
        existing.raise_for_status()

    payload: dict = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    if existing_sha:
        payload["sha"] = existing_sha

    response = httpx.put(
        f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    data = response.json()
    logger.info("GitHub file committed", extra={"repo": repo, "path": path, "branch": branch})
    return {
        "path": path,
        "sha": data["content"]["sha"],
        "commit_sha": data["commit"]["sha"],
        "commit_url": data["commit"]["html_url"],
    }
