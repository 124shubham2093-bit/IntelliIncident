"""
API endpoint tests for GitHub integration routes (/api/github/*).
Validates HTTP response codes, error translations, payload structures,
and confirms token is never exposed in API responses.
"""

import pytest
from unittest.mock import AsyncMock, patch

from backend.app.schemas.github import (
    GitHubStatusResponse,
    GitHubRateLimit,
    GitHubRepository,
    GitHubCommitSummary,
    GitHubCommitDetail,
    GitHubCommitAuthor,
    GitHubChangedFile,
    GitHubFileContent,
)
from backend.app.services.github_service import (
    GitHubError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubUnavailableError,
)

OWNER = "124shubham2093-bit"
REPO = "IntelliIncident"

def test_api_github_status_operational(client, monkeypatch):
    mock_status = GitHubStatusResponse(
        configured=True,
        authenticated=False,
        reachable=True,
        owner=OWNER,
        repo=REPO,
        default_branch="main",
        api_url="https://api.github.com",
        rate_limit=GitHubRateLimit(limit=60, remaining=55, reset_at=1700000000, used=5),
        message="GitHub integration operational",
    )

    with patch("backend.app.api.routes.github.github_service.get_status", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_status
        response = client.get("/api/github/status")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is True
    assert data["authenticated"] is False
    assert data["reachable"] is True
    assert data["owner"] == OWNER
    assert data["repo"] == REPO
    assert data["rate_limit"]["remaining"] == 55
    # Token security check
    assert "token" not in data
    assert "GITHUB_TOKEN" not in response.text

def test_api_github_status_unconfigured(client):
    mock_status = GitHubStatusResponse(
        configured=False,
        authenticated=False,
        reachable=False,
        owner="",
        repo="",
        default_branch="main",
        api_url="https://api.github.com",
        message="GitHub repository owner or name not configured.",
    )

    with patch("backend.app.api.routes.github.github_service.get_status", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_status
        response = client.get("/api/github/status")

    assert response.status_code == 200
    data = response.json()
    assert data["configured"] is False
    assert data["reachable"] is False

def test_api_github_token_never_exposed(client):
    # Even if authenticated=True, token string itself is NEVER in response
    mock_status = GitHubStatusResponse(
        configured=True,
        authenticated=True,
        reachable=True,
        owner=OWNER,
        repo=REPO,
        default_branch="main",
        api_url="https://api.github.com",
        message="Operational",
    )

    secret = "ghp_super_secret_test_token_9876543210"
    with patch("backend.app.api.routes.github.github_service.get_status", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_status
        response = client.get("/api/github/status")

    assert response.status_code == 200
    assert secret not in response.text
    assert "token" not in response.json()

def test_api_github_repo_success(client):
    mock_repo = GitHubRepository(
        full_name=f"{OWNER}/{REPO}",
        owner=OWNER,
        name=REPO,
        description="Intelligent Incident platform",
        default_branch="main",
        is_private=False,
        html_url=f"https://github.com/{OWNER}/{REPO}",
        stars_count=25,
        forks_count=4,
        open_issues_count=2,
    )

    with patch("backend.app.api.routes.github.github_service.get_repository", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_repo
        response = client.get("/api/github/repo")

    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == f"{OWNER}/{REPO}"
    assert data["owner"] == OWNER
    assert data["name"] == REPO
    assert data["stars_count"] == 25
    assert data["is_private"] is False

def test_api_github_repo_401_auth_error(client):
    with patch("backend.app.api.routes.github.github_service.get_repository", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = GitHubAuthError("Bad credentials")
        response = client.get("/api/github/repo")

    assert response.status_code == 401
    assert "Bad credentials" in response.json()["detail"]

def test_api_github_repo_403_rate_limit(client):
    with patch("backend.app.api.routes.github.github_service.get_repository", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = GitHubRateLimitError("Rate limit exceeded")
        response = client.get("/api/github/repo")

    assert response.status_code == 403
    assert "Rate limit exceeded" in response.json()["detail"]

def test_api_github_repo_404_not_found(client):
    with patch("backend.app.api.routes.github.github_service.get_repository", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = GitHubNotFoundError("Repository not found")
        response = client.get("/api/github/repo")

    assert response.status_code == 404
    assert "Repository not found" in response.json()["detail"]

def test_api_github_repo_503_unavailable(client):
    with patch("backend.app.api.routes.github.github_service.get_repository", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = GitHubUnavailableError("Connection refused")
        response = client.get("/api/github/repo")

    assert response.status_code == 503
    assert "Connection refused" in response.json()["detail"]

def test_api_github_commits_list(client):
    mock_commits = [
        GitHubCommitSummary(
            sha="b0d8abc254b972ec1977672623834ae12bdaf2d0",
            short_sha="b0d8abc",
            message="feat: incident intelligence pipeline",
            author=GitHubCommitAuthor(
                name="Shubham Bisht",
                email="bishtshubham906@gmail.com",
                date="2026-09-27T09:44:55Z",
                username="124shubham2093-bit",
            ),
            committed_at="2026-09-27T09:44:55Z",
            html_url=f"https://github.com/{OWNER}/{REPO}/commit/b0d8abc",
        )
    ]

    with patch("backend.app.api.routes.github.github_service.get_commits", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_commits
        response = client.get("/api/github/commits?limit=5")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["sha"] == "b0d8abc254b972ec1977672623834ae12bdaf2d0"
    assert data[0]["short_sha"] == "b0d8abc"
    assert data[0]["author"]["name"] == "Shubham Bisht"

def test_api_github_commit_detail(client):
    mock_detail = GitHubCommitDetail(
        sha="b0d8abc254b972ec1977672623834ae12bdaf2d0",
        short_sha="b0d8abc",
        message="feat: pipeline update",
        author=GitHubCommitAuthor(name="Shubham Bisht"),
        committed_at="2026-09-27T09:44:55Z",
        html_url=f"https://github.com/{OWNER}/{REPO}/commit/b0d8abc",
        stats={"total": 5, "additions": 3, "deletions": 2},
        files=[
            GitHubChangedFile(
                filename="backend/app/main.py",
                status="modified",
                additions=3,
                deletions=2,
                changes=5,
                patch="@@ -1,3 +1,4 @@",
            )
        ],
    )

    with patch("backend.app.api.routes.github.github_service.get_commit", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_detail
        response = client.get("/api/github/commits/b0d8abc")

    assert response.status_code == 200
    data = response.json()
    assert data["sha"] == "b0d8abc254b972ec1977672623834ae12bdaf2d0"
    assert data["stats"]["total"] == 5
    assert len(data["files"]) == 1
    assert data["files"][0]["filename"] == "backend/app/main.py"

def test_api_github_file_content(client):
    mock_file = GitHubFileContent(
        path="backend/app/main.py",
        name="main.py",
        size=1500,
        sha="fedcba654321",
        encoding="base64",
        decoded_content="print('IntelliIncident Main')",
        is_binary=False,
    )

    with patch("backend.app.api.routes.github.github_service.get_file", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_file
        response = client.get("/api/github/files/backend/app/main.py?ref=main")

    assert response.status_code == 200
    data = response.json()
    assert data["path"] == "backend/app/main.py"
    assert data["name"] == "main.py"
    assert data["is_binary"] is False
    assert data["decoded_content"] == "print('IntelliIncident Main')"
