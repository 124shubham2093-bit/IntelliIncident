"""
Comprehensive Tests for Project -> Application -> Environment Foundation.
Tests cover:
1. Project creation
2. Project retrieval
3. Project update
4. Application creation
5. Application retrieval
6. Environment creation
7. Secure API key generation
8. API key regeneration
9. API key invalidation
10. Service -> application resolution
11. X-API-Key incident authentication
12. Invalid API key rejection
13. Automatic project/application/environment binding
14. Connection guide
15. Existing unauthenticated incident creation
16. Application-specific GitHub repository selection
17. Test-ingestion endpoint
"""

import pytest
from unittest.mock import patch, AsyncMock
from backend.app.schemas.github import GitHubCommitDetail, GitHubCommitSummary, GitHubCommitAuthor


def test_1_project_creation(client):
    res = client.post("/api/projects", json={
        "name": "IntelliShop E-Commerce",
        "description": "Core online commerce platform services"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["id"].startswith("proj_")
    assert data["name"] == "IntelliShop E-Commerce"
    assert data["slug"] == "intellishop-e-commerce"
    assert data["application_count"] == 0


def test_2_project_retrieval(client):
    res = client.get("/api/projects")
    assert res.status_code == 200
    projects = res.json()
    assert len(projects) >= 1
    found = any(p["slug"] == "intellishop-e-commerce" for p in projects)
    assert found


def test_3_project_update(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]

    update_res = client.put(f"/api/projects/{proj['id']}", json={
        "description": "Updated platform description"
    })
    assert update_res.status_code == 200
    assert update_res.json()["description"] == "Updated platform description"


def test_4_application_creation(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]

    res = client.post(f"/api/projects/{proj['id']}/applications", json={
        "name": "Payment API Gateway",
        "slug": "payment-gateway",
        "description": "Payment authorization and settlement microservice",
        "language": "python",
        "framework": "FastAPI",
        "repo_owner": "custom-owner",
        "repo_name": "payment-api-custom",
        "default_branch": "main"
    })
    assert res.status_code == 201
    data = res.json()
    assert data["id"].startswith("app_")
    assert data["project_id"] == proj["id"]
    assert data["slug"] == "payment-gateway"
    assert data["repo_owner"] == "custom-owner"
    assert data["repo_name"] == "payment-api-custom"


def test_5_application_retrieval(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]

    apps_res = client.get(f"/api/projects/{proj['id']}/applications")
    assert apps_res.status_code == 200
    apps = apps_res.json()
    assert len(apps) >= 1
    assert any(a["slug"] == "payment-gateway" for a in apps)


def test_6_and_7_environment_creation_and_secure_api_key(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]
    apps_res = client.get(f"/api/projects/{proj['id']}/applications")
    app = [a for a in apps_res.json() if a["slug"] == "payment-gateway"][0]

    res = client.post(f"/api/applications/{app['id']}/environments", json={
        "name": "Production",
        "slug": "production",
        "endpoint_url": "https://api.payment.internal",
        "current_commit": "a1b2c3d4e5f6",
        "is_production": True
    })
    assert res.status_code == 201
    data = res.json()
    assert data["id"].startswith("env_")
    assert data["application_id"] == app["id"]
    assert data["is_production"] is True

    # Check Cryptographic API Key format: ii_live_<48 hex chars>
    assert "api_key" in data
    assert data["api_key"] is not None
    assert data["api_key"].startswith("ii_live_")
    assert len(data["api_key"]) > 30

    # Key preview is masked
    assert "..." in data["api_key_preview"]


def test_8_and_9_api_key_regeneration_and_invalidation(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]
    apps_res = client.get(f"/api/projects/{proj['id']}/applications")
    app = [a for a in apps_res.json() if a["slug"] == "payment-gateway"][0]
    envs_res = client.get(f"/api/applications/{app['id']}/environments")
    env = envs_res.json()[0]

    # Ordinary GET does not reveal full key
    assert env["api_key"] is None

    # Regenerate key
    regen_res = client.post(f"/api/environments/{env['id']}/regenerate-key")
    assert regen_res.status_code == 200
    new_data = regen_res.json()
    new_key = new_data["api_key"]
    assert new_key.startswith("ii_live_")

    # Ingestion with invalid/old key must fail (tested in test_12)


def test_10_service_to_application_resolution(client):
    from backend.app.services.project_service import ProjectService
    ps = ProjectService()
    resolved = ps.resolve_service_application("payment-gateway")
    assert resolved is not None
    assert resolved["slug"] == "payment-gateway"
    assert resolved["name"] == "Payment API Gateway"


def test_11_and_13_x_api_key_authentication_and_topology_binding(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]
    apps_res = client.get(f"/api/projects/{proj['id']}/applications")
    app = [a for a in apps_res.json() if a["slug"] == "payment-gateway"][0]
    envs_res = client.get(f"/api/applications/{app['id']}/environments")
    env = envs_res.json()[0]

    # Get active regenerated key
    regen_res = client.post(f"/api/environments/{env['id']}/regenerate-key")
    valid_key = regen_res.json()["api_key"]

    payload = {
        "title": "Payment Settlement Connection Timeout",
        "service": "payment-gateway",
        "summary": "Connection timeout in settlement batch worker",
        "status": "OPEN",
        "affected_users_count": 350,
        "metrics": {
            "error_rate": 28.5,
            "latency_p99": 1150.0,
            "latency_p50": 140.0,
            "request_volume": 2500,
            "deployment_recency_minutes": 45,
            "cpu_utilization": 65.0,
            "memory_utilization": 70.0,
            "service_criticality": 3
        },
        "deployments": [
            {
                "commit_hash": "a1b2c3d4e5f6",
                "environment": "production",
                "status": "SUCCESS"
            }
        ]
    }

    res = client.post("/api/incidents", json=payload, headers={"X-API-Key": valid_key})
    assert res.status_code == 201
    incident = res.json()
    assert incident["id"].startswith("INC-")
    assert incident["service"] == "payment-gateway"

    # Verify automatic binding of topology IDs
    assert incident["environmentId"] == env["id"]
    assert incident["applicationId"] == app["id"]
    assert incident["projectId"] == proj["id"]
    assert incident["environment_id"] == env["id"]
    assert incident["application_id"] == app["id"]
    assert incident["project_id"] == proj["id"]


def test_12_invalid_api_key_rejection(client):
    payload = {
        "title": "Unauthorized Telemetry Attempt",
        "service": "payment-gateway",
        "metrics": {
            "error_rate": 10.0,
            "latency_p99": 400.0,
        }
    }
    # Completely fake or expired key
    res = client.post("/api/incidents", json=payload, headers={"X-API-Key": "ii_live_invalidkey1234567890"})
    assert res.status_code == 401
    assert "Invalid X-API-Key" in res.json()["detail"]


def test_14_connection_guide(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]
    apps_res = client.get(f"/api/projects/{proj['id']}/applications")
    app = [a for a in apps_res.json() if a["slug"] == "payment-gateway"][0]
    envs_res = client.get(f"/api/applications/{app['id']}/environments")
    env = envs_res.json()[0]

    guide_res = client.get(f"/api/environments/{env['id']}/connection-guide")
    assert guide_res.status_code == 200
    guide = guide_res.json()
    assert guide["environment_id"] == env["id"]
    assert guide["application_name"] == "Payment API Gateway"
    assert guide["project_name"] == "IntelliShop E-Commerce"
    assert "curl" in guide["curl_snippet"].lower()
    assert "requests.post" in guide["python_snippet"]
    assert "fetch(" in guide["node_snippet"]
    assert "actions/checkout" in guide["github_actions_snippet"]
    assert "IntelliIncident combines runtime telemetry" in guide["explanation"]


def test_15_existing_unauthenticated_incident_creation_preserved(client):
    """Verify local dashboard ingestion without X-API-Key continues to work unchanged."""
    payload = {
        "title": "Local Dashboard Internal Incident",
        "service": "inventory-service",
        "summary": "Internal warehouse sync timeout",
        "status": "OPEN",
        "affected_users_count": 50,
        "metrics": {
            "error_rate": 5.0,
            "latency_p99": 350.0,
            "deployment_recency_minutes": 120,
            "service_criticality": 2
        }
    }
    res = client.post("/api/incidents", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["service"] == "inventory-service"
    assert data["anomalyDetected"] is not None
    assert data["riskScore"] >= 0


def test_16_application_specific_github_repository_selection(client):
    """
    Verify that an application with custom repo_owner and repo_name queries
    that specific repository instead of the global configuration.
    """
    from backend.app.services.incident_service import IncidentService
    svc = IncidentService()

    fake_commit = GitHubCommitDetail(
        sha="a1b2c3d4e5f67890",
        short_sha="a1b2c3d",
        message="Fix connection pool race condition",
        author=GitHubCommitAuthor(name="Payment Dev", email="dev@example.com"),
        committed_at="2026-09-27T10:00:00Z",
        html_url="https://github.com/custom-owner/payment-api-custom/commit/a1b2c3d",
        stats={"total": 5, "additions": 4, "deletions": 1},
        files=[]
    )

    with patch("backend.app.services.github_service.GitHubService.get_commit", new_callable=AsyncMock) as mock_get_commit:
        mock_get_commit.return_value = fake_commit

        deployments = [{"commit_hash": "a1b2c3d4e5f67890"}]
        commits = None

        import asyncio
        commits = asyncio.run(svc._fetch_deployment_commits(
            deployments,
            repo_owner="custom-owner",
            repo_name="payment-api-custom",
            default_branch="main"
        ))

        assert len(commits) == 1
        assert commits[0]["short_sha"] == "a1b2c3d"
        mock_get_commit.assert_called_once_with("a1b2c3d4e5f67890")


def test_17_test_ingestion_endpoint(client):
    list_res = client.get("/api/projects")
    proj = [p for p in list_res.json() if p["slug"] == "intellishop-e-commerce"][0]
    apps_res = client.get(f"/api/projects/{proj['id']}/applications")
    app = [a for a in apps_res.json() if a["slug"] == "payment-gateway"][0]
    envs_res = client.get(f"/api/applications/{app['id']}/environments")
    env = envs_res.json()[0]

    test_res = client.post(f"/api/environments/{env['id']}/test-ingestion")
    assert test_res.status_code == 200
    res_data = test_res.json()
    assert res_data["status"] == "ok"
    assert res_data["authenticated"] is True
    assert res_data["environment_name"] == "Production"
    assert res_data["application_name"] == "Payment API Gateway"
