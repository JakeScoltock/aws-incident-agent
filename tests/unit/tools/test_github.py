import base64

import pytest

from services.tools.github.branch import create_github_branch
from services.tools.github.commit import commit_file_to_github
from services.tools.github.pull_request import create_github_pull_request
from services.tools.github.repo_read import list_github_directory, read_github_file

API = "https://api.github.com"


@pytest.fixture(autouse=True)
def github_token(monkeypatch):
    monkeypatch.setattr("services.shared.config.settings.github_token", "ghp_test_token")


# ---------------------------------------------------------------------------
# read_github_file
# ---------------------------------------------------------------------------


def test_read_github_file(httpx_mock):
    raw = "import time\ntime.sleep(28)\n"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/contents/handler.py?ref=main",
        json={
            "path": "handler.py",
            "sha": "file-sha-abc",
            "size": len(raw),
            "content": base64.b64encode(raw.encode()).decode(),
            "encoding": "base64",
        },
    )

    result = read_github_file("owner/repo", "handler.py")

    assert result["path"] == "handler.py"
    assert result["sha"] == "file-sha-abc"
    assert result["content"] == raw


def test_read_github_file_custom_ref(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/contents/README.md?ref=feat/fix",
        json={
            "path": "README.md",
            "sha": "sha-x",
            "size": 10,
            "content": base64.b64encode(b"# hello").decode(),
            "encoding": "base64",
        },
    )

    result = read_github_file("owner/repo", "README.md", ref="feat/fix")

    assert result["content"] == "# hello"


def test_read_github_file_binary_uses_replacement_chars(httpx_mock):
    binary_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\xff\xfe"
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/contents/icon.png?ref=main",
        json={
            "path": "icon.png",
            "sha": "bin-sha",
            "size": len(binary_bytes),
            "content": base64.b64encode(binary_bytes).decode(),
            "encoding": "base64",
        },
    )

    result = read_github_file("owner/repo", "icon.png")

    assert result["sha"] == "bin-sha"
    assert isinstance(result["content"], str)


# ---------------------------------------------------------------------------
# list_github_directory
# ---------------------------------------------------------------------------


def test_list_github_directory(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/contents/?ref=main",
        json=[
            {"name": "handler.py", "type": "file", "path": "handler.py", "sha": "s1"},
            {"name": "requirements.txt", "type": "file", "path": "requirements.txt", "sha": "s2"},
        ],
    )

    result = list_github_directory("owner/repo")

    assert result["path"] == ""
    assert len(result["items"]) == 2
    assert result["items"][0]["name"] == "handler.py"
    assert result["items"][0]["type"] == "file"


# ---------------------------------------------------------------------------
# create_github_branch
# ---------------------------------------------------------------------------


def test_create_github_branch(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/git/ref/heads/main",
        json={"ref": "refs/heads/main", "object": {"sha": "base-sha-123"}},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/owner/repo/git/refs",
        json={"ref": "refs/heads/fix/timeout", "object": {"sha": "base-sha-123"}},
    )

    result = create_github_branch("owner/repo", "fix/timeout", from_ref="main")

    assert result["branch"] == "fix/timeout"
    assert result["sha"] == "base-sha-123"
    assert result["ref"] == "refs/heads/fix/timeout"


# ---------------------------------------------------------------------------
# commit_file_to_github — new file (404 on GET)
# ---------------------------------------------------------------------------


def test_commit_new_file(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/contents/handler.py?ref=fix/timeout",
        status_code=404,
        json={"message": "Not Found"},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/repos/owner/repo/contents/handler.py",
        json={
            "content": {"sha": "new-sha", "path": "handler.py"},
            "commit": {
                "sha": "commit-sha-xyz",
                "html_url": "https://github.com/owner/repo/commit/commit-sha-xyz",
            },
        },
    )

    result = commit_file_to_github(
        "owner/repo", "fix/timeout", "handler.py", "import time\n# fixed\n", "Fix timeout"
    )

    assert result["sha"] == "new-sha"
    assert result["commit_sha"] == "commit-sha-xyz"
    assert result["path"] == "handler.py"


def test_commit_existing_file(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/contents/handler.py?ref=fix/timeout",
        json={"sha": "existing-sha", "path": "handler.py", "content": ""},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/repos/owner/repo/contents/handler.py",
        json={
            "content": {"sha": "updated-sha", "path": "handler.py"},
            "commit": {
                "sha": "commit-updated",
                "html_url": "https://github.com/owner/repo/commit/commit-updated",
            },
        },
    )

    result = commit_file_to_github(
        "owner/repo", "fix/timeout", "handler.py", "# updated\n", "Update handler"
    )

    assert result["sha"] == "updated-sha"
    assert result["commit_sha"] == "commit-updated"


def test_commit_raises_on_non_404_get_error(httpx_mock):
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/repos/owner/repo/contents/handler.py?ref=fix/timeout",
        status_code=403,
        json={"message": "Forbidden"},
    )

    import httpx as _httpx

    with pytest.raises(_httpx.HTTPStatusError):
        commit_file_to_github("owner/repo", "fix/timeout", "handler.py", "content", "message")


# ---------------------------------------------------------------------------
# create_github_pull_request
# ---------------------------------------------------------------------------


def test_create_github_pull_request(httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/repos/owner/repo/pulls",
        json={
            "number": 42,
            "html_url": "https://github.com/owner/repo/pull/42",
            "title": "Fix Lambda timeout regression",
            "state": "open",
        },
    )

    result = create_github_pull_request(
        "owner/repo",
        head_branch="fix/timeout",
        base_branch="main",
        title="Fix Lambda timeout regression",
        body="Removes the deliberate time.sleep(28) introduced in deploy-1.",
    )

    assert result["pr_number"] == 42
    assert result["pr_url"] == "https://github.com/owner/repo/pull/42"
    assert result["state"] == "open"
    assert result["branch"] == "fix/timeout"
