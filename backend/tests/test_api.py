def test_ml_metrics_api(client):
    response = client.get("/api/ml/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "precision" in data
    assert "recall" in data
    assert "f1Score" in data
    assert "trainingSamplesCount" in data
    assert "lastTrainedDate" in data
    assert 0.0 <= data["accuracy"] <= 1.0

def test_ml_features_api(client):
    response = client.get("/api/ml/features")
    assert response.status_code == 200
    features = response.json()
    assert isinstance(features, list)
    assert len(features) > 0
    for f in features:
        assert "feature" in f
        assert "importance" in f
        assert "category" in f

def test_fuzzy_risk_api(client):
    payload = {
        "errorRate": 18.5,
        "userImpact": 65.0,
        "latency": 1400.0,
        "deploymentRecency": 25.0,
        "serviceCriticality": 4.0,
    }
    response = client.post("/api/fuzzy-risk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "riskScore" in data
    assert "riskLevel" in data
    assert "inputs" in data
    assert "triggeredRules" in data
    assert data["defuzzificationMethod"] == "Centroid of Area (COA)"

def test_analyze_incident_api(client):
    list_res = client.get("/api/incidents")
    first_id = list_res.json()[0]["id"]

    response = client.post(f"/api/analyze/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["incidentId"] == first_id
    assert "analyzedAt" in data
    assert "anomaly" in data
    assert "severityPrediction" in data
    assert "fuzzyRisk" in data
    assert "rootCauses" in data
    assert "recommendations" in data

def test_root_cause_api(client):
    list_res = client.get("/api/incidents")
    first_id = list_res.json()[0]["id"]

    response = client.get(f"/api/root-cause/{first_id}")
    assert response.status_code == 200
    candidates = response.json()
    assert isinstance(candidates, list)
    assert len(candidates) == 6

def test_incident_report_api(client):
    list_res = client.get("/api/incidents")
    first_id = list_res.json()[0]["id"]

    response = client.get(f"/api/reports/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert "incident" in data
    assert "generatedAt" in data
    assert "reportId" in data
    assert "summaryTitle" in data
