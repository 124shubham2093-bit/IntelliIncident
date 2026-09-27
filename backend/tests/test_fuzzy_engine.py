import pytest
from backend.app.fuzzy.fuzzy_engine import FuzzyRiskEngine
from backend.app.fuzzy.membership_functions import trimf, trapmf

def test_membership_functions():
    # Triangular membership
    assert trimf(10.0, (5.0, 10.0, 15.0)) == 1.0
    assert trimf(5.0, (5.0, 10.0, 15.0)) == 0.0
    assert trimf(15.0, (5.0, 10.0, 15.0)) == 0.0
    assert trimf(7.5, (5.0, 10.0, 15.0)) == 0.5

    # Trapezoidal membership
    assert trapmf(10.0, (5.0, 8.0, 12.0, 15.0)) == 1.0
    assert trapmf(3.0, (5.0, 8.0, 12.0, 15.0)) == 0.0
    assert trapmf(18.0, (5.0, 8.0, 12.0, 15.0)) == 0.0
    assert trapmf(6.5, (5.0, 8.0, 12.0, 15.0)) == 0.5

def test_fuzzy_risk_engine_low():
    engine = FuzzyRiskEngine()
    low_input = {
        "errorRate": 1.0,
        "userImpact": 5.0,
        "latency": 90.0,
        "deploymentRecency": 180.0,
        "serviceCriticality": 2.0,
    }
    result = engine.evaluate(low_input)
    assert result["riskLevel"] == "LOW"
    assert result["riskScore"] < 35
    assert result["defuzzificationMethod"] == "Centroid of Area (COA)"
    assert len(result["triggeredRules"]) > 0

def test_fuzzy_risk_engine_high_monotonicity():
    engine = FuzzyRiskEngine()
    low_res = engine.evaluate({
        "errorRate": 1.0, "userImpact": 10.0, "latency": 100.0,
        "deploymentRecency": 150.0, "serviceCriticality": 2.0
    })
    crit_res = engine.evaluate({
        "errorRate": 35.0, "userImpact": 90.0, "latency": 2500.0,
        "deploymentRecency": 10.0, "serviceCriticality": 5.0
    })
    assert crit_res["riskScore"] > low_res["riskScore"]
    assert crit_res["riskLevel"] in ["HIGH", "CRITICAL"]
    assert len(crit_res["triggeredRules"]) > 0
    for rule in crit_res["triggeredRules"]:
        assert 0.0 <= rule["weight"] <= 1.0

def test_fuzzy_risk_engine_inc_8610_consistency():
    engine = FuzzyRiskEngine()
    inc_inputs = {
        "errorRate": 42.19,
        "userImpact": 16.0,
        "latency": 514.3,
        "deploymentRecency": 102.0,
        "serviceCriticality": 3.0,
    }
    result = engine.evaluate(inc_inputs)
    assert result["inputs"]["errorRateState"] == "HIGH"
    triggered_ids = [r["id"] for r in result["triggeredRules"]]
    assert "RULE-06" not in triggered_ids
    assert "RULE-11" in triggered_ids
    assert "RULE-13" in triggered_ids
    assert result["riskScore"] >= 50

def test_fuzzy_risk_engine_no_false_rule_06_on_high_error():
    engine = FuzzyRiskEngine()
    for high_err in [25.0, 35.0, 42.19, 49.0]:
        result = engine.evaluate({
            "errorRate": high_err,
            "userImpact": 10.0,
            "latency": 200.0,
            "deploymentRecency": 120.0,
            "serviceCriticality": 3.0,
        })
        triggered_ids = [r["id"] for r in result["triggeredRules"]]
        assert "RULE-06" not in triggered_ids, f"RULE-06 fired with errorRate={high_err}"

