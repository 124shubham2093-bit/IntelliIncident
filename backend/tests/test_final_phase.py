'''
Tests for Phase 4 Final Implementation:
1. GitHub connection verification (repo/branch validation)
2. Application-scoped GitHub status endpoint
3. Real runtime telemetry error ingestion via X-API-Key
4. Deployment commit tracking and resolution priority
5. Stack trace parsing (Python + JS/TS) and path normalization
6. End-to-end GitHub source file lookup & context extraction
7. Graceful GitHub failure fallback (no crashes, no false matches)
'''

import pytest
from unittest.mock import patch, AsyncMock
from backend.app.services.stack_trace_parser import parse_stack_trace, normalize_file_path
from backend.app.schemas.github import (
    GitHubApplicationVerification,
    GitHubFileContent,
    GitHubCommitDetail,
    GitHubCommitAuthor,
)
from backend.app.services.github_service import GitHubService


# ==========================================
# 1. Stack Trace Parser Tests
# ==========================================

def test_stack_trace_parser_python():
    trace = (
        'Traceback (most recent call last):\n'
        '  File "/usr/lib/python3.12/site-packages/starlette/routing.py", line 68, in app\n'
        '    response = await func(request)\n'
        '  File "backend/app/services/payment_service.py", line 42, in process_transaction\n'
        '    raise ConnectionRefusedError("Gateway unreachable")\n'
    )
    location = parse_stack_trace(trace)
    assert location is not None
    assert location.file_path == "backend/app/services/payment_service.py"
    assert location.line_number == 42
    assert location.function_name == "process_transaction"


def test_stack_trace_parser_javascript():
    trace = (
        'Error: Cannot read properties of undefined (reading "currency")\n'
        '    at processPayment (src/api/payment.ts:55:18)\n'
        '    at dispatch (node_modules/express/lib/router.js:12:4)\n'
    )
    location = parse_stack_trace(trace)
    assert location is not None
    assert location.file_path == "src/api/payment.ts"
    assert location.line_number == 55
    assert location.column_number == 18
    assert location.function_name == "processPayment"


def test_stack_trace_parser_path_normalization():
    assert normalize_file_path("C:\\Users\\User\\Project\\backend\\app\\main.py") == "Users/User/Project/backend/app/main.py"
    assert normalize_file_path("/app/backend/app/service.py") == "backend/app/service.py"
    assert normalize_file_path("file:///var/app/src/index.ts") == "src/index.ts"


def test_stack_trace_parser_unresolvable():
    assert parse_stack_trace("") is None
    assert parse_stack_trace("Fatal system crash occurred without traceback") is None


# ==========================================
# 2. GitHub Connection Verification Tests
# ==========================================

@pytest.mark.anyio
async def test_github_verification_success():
    gh = GitHubService(owner="testowner", repo="testrepo", default_branch="main")
    with patch.object(gh, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = [
            # 1. GET /repos/testowner/testrepo
            (AsyncMock(headers={"x-ratelimit-remaining": "55"}), {"default_branch": "main"}),
            # 2. GET /repos/testowner/testrepo/branches/main
            (AsyncMock(headers={"x-ratelimit-remaining": "54"}), {"name": "main"}),
        ]
        res = await gh.verify_connection(branch="main")
        assert res.connected is True
        assert res.repository_accessible is True
        assert res.branch_accessible is True
        assert "verified successfully" in res.message


@pytest.mark.anyio
async def test_github_verification_repo_not_found():
    from backend.app.services.github_service import GitHubNotFoundError
    gh = GitHubService(owner="nonexistent", repo="repo", default_branch="main")
    with patch.object(gh, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = GitHubNotFoundError("Not found")
        res = await gh.verify_connection(branch="main")
        assert res.connected is False
        assert res.repository_accessible is False
        assert res.branch_accessible is False
        assert "not found" in res.message.lower()


@pytest.mark.anyio
async def test_github_verification_branch_not_found():
    from backend.app.services.github_service import GitHubNotFoundError
    gh = GitHubService(owner="testowner", repo="testrepo", default_branch="feature-x")
    with patch.object(gh, "_request", new_callable=AsyncMock) as mock_req:
        mock_req.side_effect = [
            (AsyncMock(headers={}), {"default_branch": "main"}),
            GitHubNotFoundError("Branch not found"),
        ]
        res = await gh.verify_connection(branch="feature-x")
        assert res.connected is False
        assert res.repository_accessible is True
        assert res.branch_accessible is False
        assert "feature-x" in res.message


# ==========================================
# 3. Source Context Extraction Tests
# ==========================================

@pytest.mark.anyio
async def test_get_source_context_matched():
    gh = GitHubService(owner="testowner", repo="testrepo")
    fake_code = "\n".join([f"line {i} content" for i in range(1, 21)])
    with patch.object(gh, "get_file", new_callable=AsyncMock) as mock_gf:
        mock_gf.return_value = GitHubFileContent(
            path="src/service.py",
            name="service.py",
            size=len(fake_code),
            sha="abcdef123",
            decoded_content=fake_code,
            is_binary=False,
        )
        lines, snippet, status = await gh.get_source_context(
            path="src/service.py",
            line=10,
            ref="abcdef1234567890abcdef1234567890abcdef12",
            window=3,
        )
        assert status == "MATCHED"
        assert len(lines) == 7  # lines 7 to 13
        target_lines = [l for l in lines if l.is_target]
        assert len(target_lines) == 1
        assert target_lines[0].line_number == 10
        assert "line 10 content" in target_lines[0].content


# ==========================================
# 4. End-to-End API Ingestion & Investigation
# ==========================================

def test_api_key_runtime_telemetry_ingestion_end_to_end(client):
    # 1. Create Project
    p_res = client.post("/api/projects", json={
        "name": "FinTech Platform",
        "description": "Payment and checkout infrastructure"
    })
    assert p_res.status_code == 201
    proj_id = p_res.json()["id"]

    # 2. Create Application with GitHub Repo Binding
    a_res = client.post(f"/api/projects/{proj_id}/applications", json={
        "name": "FinTech Checkout Service",
        "language": "python",
        "framework": "FastAPI",
        "repo_owner": "fintech-org",
        "repo_name": "checkout-service",
        "default_branch": "main",
    })
    assert a_res.status_code == 201
    app_id = a_res.json()["id"]

    # 3. Create Environment with Deployed Commit
    deployed_sha = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"
    e_res = client.post(f"/api/applications/{app_id}/environments", json={
        "name": "production",
        "is_production": True,
        "current_commit": deployed_sha,
        "endpoint_url": "https://api.fintech.example.com",
    })
    assert e_res.status_code == 201
    env_data = e_res.json()
    env_id = env_data["id"]
    api_key = env_data["api_key"]
    assert api_key.startswith("ii_live_")

    # 4. Verify GitHub status route for this application
    with patch.object(GitHubService, "verify_connection", new_callable=AsyncMock) as mock_vc:
        mock_vc.return_value = GitHubApplicationVerification(
            connected=True,
            repository_accessible=True,
            branch_accessible=True,
            owner="fintech-org",
            repo="checkout-service",
            branch="main",
            message="Verified",
        )
        gh_status_res = client.get(f"/api/applications/{app_id}/github-status")
        assert gh_status_res.status_code == 200
        assert gh_status_res.json()["connected"] is True

    # 5. Ingest Runtime Incident using X-API-Key with realistic error and stack trace
    source_content = (
        "def process_transaction(order):\n"
        "    currency = order['currency']\n"
        "    amount = order['amount']\n"
        "    # Intentionally raised exception\n"
        "    if currency != 'USD':\n"
        "        raise ValueError('Unsupported currency')\n"
        "    return execute_transfer(amount)\n"
    )

    with patch.object(GitHubService, "get_file", new_callable=AsyncMock) as mock_gf, \
         patch.object(GitHubService, "get_commit", new_callable=AsyncMock) as mock_gc:

        mock_gf.return_value = GitHubFileContent(
            path="backend/services/payment.py",
            name="payment.py",
            size=len(source_content),
            sha=deployed_sha,
            decoded_content=source_content,
            is_binary=False,
        )
        mock_gc.return_value = GitHubCommitDetail(
            sha=deployed_sha,
            short_sha=deployed_sha[:7],
            message="feat: implement transaction processor",
            author=GitHubCommitAuthor(name="Dev Team", email="dev@example.com"),
            html_url="https://github.com/fintech-org/checkout-service/commit/" + deployed_sha,
        )

        inc_res = client.post(
            "/api/incidents",
            headers={"X-API-Key": api_key},
            json={
                "title": "Payment Processing Failure",
                "service": "FinTechCheckout",
                "summary": "Unhandled ValueError during checkout transaction.",
                "error_type": "ValueError",
                "error_message": "Unsupported currency EUR in transaction",
                "stack_trace": (
                    'Traceback (most recent call last):\n'
                    '  File "backend/services/payment.py", line 6, in process_transaction\n'
                    '    raise ValueError("Unsupported currency")\n'
                ),
                "metrics": {
                    "error_rate": 22.0,
                    "latency_p99": 920.0,
                    "latency_p50": 80.0,
                    "affected_users": 520,
                    "request_volume": 3500,
                    "deployment_recency_minutes": 15,
                    "cpu_utilization": 65.0,
                    "memory_utilization": 70.0,
                    "service_criticality": 4,
                }
            }
        )

        assert inc_res.status_code == 201
        data = inc_res.json()

        # Check topology binding
        assert data["projectId"] == proj_id
        assert data["applicationId"] == app_id
        assert data["environmentId"] == env_id

        # Check ML & Fuzzy outputs exist and are populated
        assert "severity" in data
        assert "risk" in data
        assert "riskScore" in data
        assert "anomalyDetected" in data

        # Check Deployed Commit resolution
        assert data.get("deployedCommit") == deployed_sha

        # Check GitHub Source Evidence
        gh_src = data.get("githubSourceEvidence")
        assert gh_src is not None
        assert gh_src["status"] == "MATCHED"
        assert gh_src["file_path"] == "backend/services/payment.py"
        assert gh_src["target_line"] == 6
        assert gh_src["deployment_commit"] == deployed_sha
        assert len(gh_src["source_lines"]) > 0


def test_github_failure_fallback_during_ingestion(client):
    # Tests that when GitHub is unavailable (or returns 404),
    # the incident creation pipeline DOES NOT crash and correctly reports failure without false match.
    from backend.app.services.github_service import GitHubNotFoundError

    with patch.object(GitHubService, "get_file", new_callable=AsyncMock) as mock_gf:
        mock_gf.side_effect = GitHubNotFoundError("Source file not found")

        inc_res = client.post(
            "/api/incidents",
            json={
                "title": "Service Crash with Missing Source",
                "service": "AnalyticsEngine",
                "commit_sha": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
                "error_type": "KeyError",
                "error_message": "Key 'session_token' missing",
                "stack_trace": (
                    'Traceback (most recent call last):\n'
                    '  File "src/auth/session.py", line 88, in get_session\n'
                    '    return store[session_id]\n'
                ),
            }
        )

        assert inc_res.status_code == 201
        data = inc_res.json()
        gh_src = data.get("githubSourceEvidence")
        assert gh_src is not None
        assert gh_src["status"] == "FILE_NOT_FOUND"
        assert "not found" in gh_src["message"].lower()
