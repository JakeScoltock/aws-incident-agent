import logging

logger = logging.getLogger(__name__)


def create_github_pull_request(
    repo: str, head_branch: str, base_branch: str, title: str, body: str
) -> dict:
    """Open a GitHub Pull Request. Does not merge."""
    raise NotImplementedError("Implement in Phase 3")
