import logging

import httpx
from strands import tool

from ._client import GITHUB_API_BASE, github_headers

logger = logging.getLogger(__name__)


@tool
def create_github_pull_request(
    repo: str, head_branch: str, base_branch: str, title: str, body: str
) -> dict:
    """Open a GitHub Pull Request. Does not merge.
    repo: owner/repo format. head_branch: branch with changes. base_branch: target branch."""
    response = httpx.post(
        f"{GITHUB_API_BASE}/repos/{repo}/pulls",
        headers=github_headers(),
        json={"title": title, "body": body, "head": head_branch, "base": base_branch},
    )
    response.raise_for_status()
    data = response.json()
    logger.info("GitHub PR created", extra={"repo": repo, "pr": data["number"]})
    return {
        "pr_number": data["number"],
        "pr_url": data["html_url"],
        "title": data["title"],
        "state": data["state"],
        "branch": head_branch,
    }
