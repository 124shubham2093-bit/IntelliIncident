def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert data["service"] == "intelli-incident-backend"
    assert data["mlEngineReady"] is True
    assert data["fuzzyEngineReady"] is True

def test_root_route(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "IntelliIncident"
    assert data["status"] == "operational"
