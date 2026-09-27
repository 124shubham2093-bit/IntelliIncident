from backend.app.rca.root_cause_engine import RootCauseEngine
from backend.app.services.recommendation_service import RecommendationService

def test_root_cause_candidates_ranking():
    engine = RootCauseEngine()
    incident = {"service": "payment-gateway", "severity": "CRITICAL"}
    metrics = {
        "error_rate": 28.0,
        "latency_p99": 2800.0,
        "latency_p50": 60.0,
        "cpu_utilization": 45.0,
        "memory_utilization": 50.0,
        "deployment_recency_minutes": 15,
        "request_volume": 5000,
    }
    deployments = [{"id": "DEP-1", "service": "payment-gateway", "status": "FAILED"}]
    logs = [{"message": "Exception in payment transaction"}]

    candidates = engine.analyze(incident, metrics, logs, deployments)
    assert len(candidates) == 6
    # Candidates should be sorted by score descending
    scores = [c["score"] for c in candidates]
    assert scores == sorted(scores, reverse=True)
    # DEPLOYMENT should rank high because recency is 15min and failed deployment exists
    top_candidate = candidates[0]
    assert top_candidate["category"] in ["DEPLOYMENT", "DATABASE", "CODE_ERROR"]

def test_recommendations_never_auto_executed_and_labeled():
    top_cand = {"category": "DEPLOYMENT"}
    recommendations = RecommendationService.generate_recommendations(
        top_candidate=top_cand, service_name="payment-gateway", severity="CRITICAL"
    )
    assert len(recommendations) > 0
    for rec in recommendations:
        assert rec["priority"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        assert rec["category"] in ["INVESTIGATION", "MITIGATION", "ROLLBACK", "VERIFICATION"]
        if rec.get("actionCmd"):
            # Strictly verify that command is labeled as Operator action or Suggested command
            desc = rec["description"]
            assert "Operator action" in desc or "Suggested command" in desc
