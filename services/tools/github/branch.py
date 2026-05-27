import logging

import httpx
from strands import tool

from ._client import GITHUB_API_BASE, github_headers

logger = logging.getLogger(__name__)


@tool
def create_github_branch(repo: str, branch_name: str, from_ref: str = "main") -> dict:
    """Create a new branch in a GitHub repository.
    repo: owner/repo format. from_ref: branch or commit SHA to branch from."""
    headers = github_headers()

    ref_response = httpx.get(
        f"{GITHUB_API_BASE}/repos/{repo}/git/ref/heads/{from_ref}",
        headers=headers,
    )
    ref_response.raise_for_status()
    sha = ref_response.json()["object"]["sha"]

    create_response = httpx.post(
        f"{GITHUB_API_BASE}/repos/{repo}/git/refs",
        headers=headers,
        json={"ref": f"refs/heads/{branch_name}", "sha": sha},
    )
    create_response.raise_for_status()
    data = create_response.json()
    logger.info("GitHub branch created", extra={"repo": repo, "branch": branch_name, "sha": sha})
    return {"branch": branch_name, "sha": data["object"]["sha"], "ref": data["ref"]}
