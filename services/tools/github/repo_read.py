import base64
import logging

import httpx
from strands import tool

from ._client import GITHUB_API_BASE, github_headers

logger = logging.getLogger(__name__)


@tool
def read_github_file(repo: str, path: str, ref: str = "main") -> dict:
    """Read a file from a GitHub repository.
    repo: owner/repo format. Returns decoded file content and metadata."""
    response = httpx.get(
        f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}",
        headers=github_headers(),
        params={"ref": ref},
    )
    response.raise_for_status()
    data = response.json()
    content = (
        base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        if data.get("content")
        else ""
    )
    logger.info("GitHub file read", extra={"repo": repo, "path": path, "ref": ref})
    return {"path": data["path"], "sha": data["sha"], "size": data["size"], "content": content}


@tool
def list_github_directory(repo: str, path: str = "", ref: str = "main") -> dict:
    """List files and directories in a GitHub repository path.
    repo: owner/repo format."""
    response = httpx.get(
        f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}",
        headers=github_headers(),
        params={"ref": ref},
    )
    response.raise_for_status()
    items = response.json()
    if isinstance(items, dict):
        items = [items]
    logger.info("GitHub directory listed", extra={"repo": repo, "path": path, "ref": ref})
    return {
        "path": path,
        "items": [
            {"name": i["name"], "type": i["type"], "path": i["path"], "sha": i["sha"]}
            for i in items
        ],
    }
