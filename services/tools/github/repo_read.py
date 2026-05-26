import logging

logger = logging.getLogger(__name__)


def read_github_file(repo: str, path: str, ref: str = "main") -> dict:
    """Read a file from a GitHub repository."""
    raise NotImplementedError("Implement in Phase 3")


def list_github_directory(repo: str, path: str = "", ref: str = "main") -> dict:
    """List files in a GitHub repository directory."""
    raise NotImplementedError("Implement in Phase 3")
