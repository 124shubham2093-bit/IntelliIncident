def test_list_incidents(client):
    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert isinstance(incidents, list)
    assert len(incidents) > 0
    first = incidents[0]
    assert "id" in first
    assert "title" in first
    assert "severity" in first
    assert "risk" in first
    assert "riskScore" in first
    assert "anomalyDetected" in first
    assert "anomalyScore" in first
    assert "status" in first
    assert "affectedUsersCount" in first

def test_filter_incidents_by_severity(client):
    response = client.get("/api/incidents?severity=CRITICAL")
    assert response.status_code == 200
    incidents = response.json()
    for inc in incidents:
        assert inc["severity"] == "CRITICAL"

def test_filter_incidents_by_service(client):
    response = client.get("/api/incidents?service=payment-gateway")
    assert response.status_code == 200
    incidents = response.json()
    for inc in incidents:
        assert inc["service"] == "payment-gateway"

def test_get_incident_by_id(client):
    list_res = client.get("/api/incidents")
    first_id = list_res.json()[0]["id"]

    response = client.get(f"/api/incidents/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == first_id
    assert "metrics" in data
    assert "mlAnalysis" in data
    assert "fuzzyRisk" in data
    assert "evidenceTimeline" in data
    assert "rootCauseCandidates" in data
    assert "recommendations" in data

def test_get_nonexistent_incident(client):
    response = client.get("/api/incidents/INC-NONEXISTENT")
    assert response.status_code == 404
