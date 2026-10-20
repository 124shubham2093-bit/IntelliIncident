"""
Unit tests for GitHubService.
All GitHub network requests are strictly mocked with httpx.MockTransport.
No real network calls are ever made.
"""

import base64
import pytest
import httpx

from backend.app.services.github_service import (
    GitHubService,
    GitHubError,
    GitHubConfigError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubNotFoundError,
    GitHubUnavailableError,
)

OWNER = "124shubham2093-bit"
REPO = "IntelliIncident"

@pytest.mark.anyio
async def test_service_init_defaults():
    service = GitHubService(owner=OWNER, repo=REPO)
    assert service.owner == OWNER
    assert service.repo == REPO
    assert service.default_branch == "main"
    assert service.api_url == "https://api.github.com"
    assert service.timeout == 3.0

@pytest.mark.anyio
async def test_service_unconfigured_status():
    service = GitHubService(owner="", repo="")
    status = await service.get_status()
    assert status.configured is False
    assert status.reachable is False
    assert "not configured" in status.message

@pytest.mark.anyio
async def test_get_status_operational():
    def handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={"default_branch": "main", "name": REPO},
            headers={"x-ratelimit-limit": "60", "x-ratelimit-remaining": "55", "x-ratelimit-reset": "1700000000"}
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        status = await service.get_status()

    assert status.configured is True
    assert status.reachable is True
    assert status.rate_limit is not None
    assert status.rate_limit.limit == 60
    assert status.rate_limit.remaining == 55
    assert "operational" in status.message.lower()

@pytest.mark.anyio
async def test_get_status_auth_error_401():
    def handler(request: httpx.Request):
        return httpx.Response(401, json={"message": "Bad credentials"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, token="invalid_token", client=client)
        status = await service.get_status()

    assert status.configured is True
    assert status.authenticated is False
    assert status.reachable is True
    assert "authentication failed" in status.message.lower()

@pytest.mark.anyio
async def test_get_status_rate_limit_403():
    def handler(request: httpx.Request):
        return httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-limit": "60", "x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700001234"}
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        status = await service.get_status()

    assert status.configured is True
    assert status.reachable is True
    assert "rate limit" in status.message.lower()

@pytest.mark.anyio
async def test_get_status_unreachable_network_error():
    def handler(request: httpx.Request):
        raise httpx.ConnectError("DNS resolution failed")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        status = await service.get_status()

    assert status.configured is True
    assert status.reachable is False
    assert "unreachable" in status.message.lower()

@pytest.mark.anyio
async def test_get_repository_success():
    def handler(request: httpx.Request):
        assert request.url.path == f"/repos/{OWNER}/{REPO}"
        return httpx.Response(
            200,
            json={
                "full_name": f"{OWNER}/{REPO}",
                "name": REPO,
                "description": "Incident intelligence system",
                "default_branch": "main",
                "private": False,
                "html_url": f"https://github.com/{OWNER}/{REPO}",
                "stargazers_count": 12,
                "forks_count": 3,
                "open_issues_count": 1,
                "owner": {"login": OWNER},
            }
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        repo_data = await service.get_repository()

    assert repo_data.full_name == f"{OWNER}/{REPO}"
    assert repo_data.name == REPO
    assert repo_data.owner == OWNER
    assert repo_data.is_private is False
    assert repo_data.stars_count == 12
    assert repo_data.forks_count == 3
    assert repo_data.open_issues_count == 1
    assert repo_data.html_url == f"https://github.com/{OWNER}/{REPO}"

@pytest.mark.anyio
async def test_get_commits_normalization():
    def handler(request: httpx.Request):
        assert request.url.path == f"/repos/{OWNER}/{REPO}/commits"
        assert request.url.params.get("per_page") == "2"
        return httpx.Response(
            200,
            json=[
                {
                    "sha": "b0d8abc254b972ec1977672623834ae12bdaf2d0",
                    "commit": {
                        "message": "feat: complete real-data incident pipeline",
                        "author": {
                            "name": "Shubham Bisht",
                            "email": "bishtshubham906@gmail.com",
                            "date": "2026-09-27T09:44:55Z",
                        },
                    },
                    "html_url": f"https://github.com/{OWNER}/{REPO}/commit/b0d8abc254b972ec1977672623834ae12bdaf2d0",
                    "author": {
                        "login": "124shubham2093-bit",
                        "avatar_url": "https://avatars.githubusercontent.com/u/1",
                    },
                }
            ]
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        commits = await service.get_commits(limit=2)

    assert len(commits) == 1
    c = commits[0]
    assert c.sha == "b0d8abc254b972ec1977672623834ae12bdaf2d0"
    assert c.short_sha == "b0d8abc"
    assert c.message == "feat: complete real-data incident pipeline"
    assert c.author.name == "Shubham Bisht"
    assert c.author.email == "bishtshubham906@gmail.com"
    assert c.author.username == "124shubham2093-bit"
    assert c.committed_at == "2026-09-27T09:44:55Z"

@pytest.mark.anyio
async def test_get_commit_detail_and_changed_files():
    def handler(request: httpx.Request):
        assert request.url.path == f"/repos/{OWNER}/{REPO}/commits/b0d8abc"
        return httpx.Response(
            200,
            json={
                "sha": "b0d8abc254b972ec1977672623834ae12bdaf2d0",
                "commit": {
                    "message": "feat: complete real-data incident pipeline",
                    "author": {
                        "name": "Shubham Bisht",
                        "email": "bishtshubham906@gmail.com",
                        "date": "2026-09-27T09:44:55Z",
                    },
                },
                "html_url": f"https://github.com/{OWNER}/{REPO}/commit/b0d8abc",
                "author": {"login": "124shubham2093-bit"},
                "stats": {"total": 15, "additions": 10, "deletions": 5},
                "files": [
                    {
                        "filename": "backend/app/main.py",
                        "status": "modified",
                        "additions": 10,
                        "deletions": 5,
                        "changes": 15,
                        "blob_url": "https://github.com/blob/main.py",
                        "raw_url": "https://github.com/raw/main.py",
                        "patch": "@@ -1,5 +1,10 @@",
                    }
                ],
            }
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        detail = await service.get_commit("b0d8abc")

    assert detail.sha == "b0d8abc254b972ec1977672623834ae12bdaf2d0"
    assert detail.short_sha == "b0d8abc"
    assert detail.stats["total"] == 15
    assert detail.stats["additions"] == 10
    assert detail.stats["deletions"] == 5
    assert len(detail.files) == 1
    f = detail.files[0]
    assert f.filename == "backend/app/main.py"
    assert f.status == "modified"
    assert f.additions == 10
    assert f.deletions == 5
    assert f.changes == 15
    assert f.patch == "@@ -1,5 +1,10 @@"

@pytest.mark.anyio
async def test_get_file_decoded_text():
    encoded = base64.b64encode(b"print('IntelliIncident')\n").decode("utf-8")

    def handler(request: httpx.Request):
        assert request.url.path == f"/repos/{OWNER}/{REPO}/contents/backend/app/main.py"
        return httpx.Response(
            200,
            json={
                "name": "main.py",
                "path": "backend/app/main.py",
                "sha": "abcdef123456",
                "size": 25,
                "encoding": "base64",
                "content": encoded,
                "html_url": f"https://github.com/{OWNER}/{REPO}/blob/main/backend/app/main.py",
            }
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        file_obj = await service.get_file("backend/app/main.py")

    assert file_obj.name == "main.py"
    assert file_obj.path == "backend/app/main.py"
    assert file_obj.size == 25
    assert file_obj.is_binary is False
    assert "print('IntelliIncident')" in file_obj.decoded_content

@pytest.mark.anyio
async def test_get_file_binary():
    # Non-UTF8 byte stream
    binary_bytes = b"\x80\x81\x82\x83\xff\xfe"
    encoded = base64.b64encode(binary_bytes).decode("utf-8")

    def handler(request: httpx.Request):
        return httpx.Response(
            200,
            json={
                "name": "model.joblib",
                "path": "backend/models/model.joblib",
                "sha": "123456",
                "size": 6,
                "encoding": "base64",
                "content": encoded,
            }
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        file_obj = await service.get_file("backend/models/model.joblib")

    assert file_obj.is_binary is True
    assert file_obj.decoded_content is None

@pytest.mark.anyio
async def test_get_file_directory_raises_error():
    def handler(request: httpx.Request):
        return httpx.Response(200, json=[{"name": "file1.py"}, {"name": "file2.py"}])

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        with pytest.raises(GitHubError, match="is a directory"):
            await service.get_file("backend/app")

@pytest.mark.anyio
async def test_401_unauthorized_raises_github_auth_error():
    def handler(request: httpx.Request):
        return httpx.Response(401, json={"message": "Bad credentials"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        with pytest.raises(GitHubAuthError):
            await service.get_repository()

@pytest.mark.anyio
async def test_403_rate_limit_raises_github_rate_limit_error():
    def handler(request: httpx.Request):
        return httpx.Response(
            403,
            json={"message": "API rate limit exceeded"},
            headers={"x-ratelimit-limit": "60", "x-ratelimit-remaining": "0", "x-ratelimit-reset": "1700000000"}
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        with pytest.raises(GitHubRateLimitError, match="rate limit exceeded"):
            await service.get_repository()

@pytest.mark.anyio
async def test_404_not_found_raises_github_not_found_error():
    def handler(request: httpx.Request):
        return httpx.Response(404, json={"message": "Not Found"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        with pytest.raises(GitHubNotFoundError):
            await service.get_commit("nonexistent_sha")

@pytest.mark.anyio
async def test_timeout_raises_github_unavailable_error():
    def handler(request: httpx.Request):
        raise httpx.TimeoutException("Connection timed out after 3.0s")

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        service = GitHubService(owner=OWNER, repo=REPO, client=client)
        with pytest.raises(GitHubUnavailableError, match="timed out"):
            await service.get_repository()

@pytest.mark.anyio
async def test_token_header_security():
    # 1. No token -> no Authorization header
    service_no_token = GitHubService(owner=OWNER, repo=REPO, token=None)
    headers_no_token = service_no_token._get_headers()
    assert "Authorization" not in headers_no_token

    # 2. Token present -> Authorization: Bearer <token>
    service_with_token = GitHubService(owner=OWNER, repo=REPO, token="ghp_test_secret_token_12345")
    headers_with_token = service_with_token._get_headers()
    assert headers_with_token.get("Authorization") == "Bearer ghp_test_secret_token_12345"
