"""
Mamdani Soft Computing Fuzzy Risk Assessment Engine
Implements fuzzification, min-max inference, Centroid of Area (COA) defuzzification,
and dynamic explainability for IntelliIncident explicitly using scikit-fuzzy (skfuzzy).
"""

from typing import Dict, Any, List
import numpy as np
import skfuzzy as fuzz
from skfuzzy import membership as mf

from backend.app.fuzzy.membership_functions import (
    INPUT_MEMBERSHIPS,
    OUTPUT_MEMBERSHIPS,
    RISK_UNIVERSE,
)
from backend.app.fuzzy.fuzzy_rules import FUZZY_RULES

class FuzzyRiskEngine:
    """
    Fuzzy Risk Engine powered by scikit-fuzzy.
    Executes Mamdani inference and centroid defuzzification while preserving
    transparent rule activation weights for incident explainability.
    """
    def __init__(self):
        self.rules = FUZZY_RULES
        self.z_universe = RISK_UNIVERSE

    def evaluate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate fuzzy risk from crisp operational inputs using scikit-fuzzy.
        Supports both camelCase and snake_case keys.
        """
        # 0. Domain bounding to input universes of discourse
        error_rate = float(np.clip(float(inputs.get("errorRate", inputs.get("error_rate", 0.0))), 0.0, 50.0))
        user_impact = float(np.clip(float(inputs.get("userImpact", inputs.get("user_impact", 0.0))), 0.0, 100.0))
        latency = float(np.clip(float(inputs.get("latency", inputs.get("latency_p99", 0.0))), 0.0, 3000.0))
        deployment_recency = float(np.clip(float(inputs.get("deploymentRecency", inputs.get("deployment_recency_minutes", 180.0))), 0.0, 180.0))
        service_criticality = float(np.clip(float(inputs.get("serviceCriticality", inputs.get("service_criticality", 3.0))), 1.0, 5.0))

        # 1. Fuzzification using scikit-fuzzy interpolation across universe
        memberships = {
            "error_rate": {
                name: float(fuzz.interp_membership(
                    INPUT_MEMBERSHIPS["error_rate"]["universe_array"],
                    INPUT_MEMBERSHIPS["error_rate"]["shapes"][name],
                    error_rate
                ))
                for name in INPUT_MEMBERSHIPS["error_rate"]["shapes"]
            },
            "user_impact": {
                name: float(fuzz.interp_membership(
                    INPUT_MEMBERSHIPS["user_impact"]["universe_array"],
                    INPUT_MEMBERSHIPS["user_impact"]["shapes"][name],
                    user_impact
                ))
                for name in INPUT_MEMBERSHIPS["user_impact"]["shapes"]
            },
            "latency": {
                name: float(fuzz.interp_membership(
                    INPUT_MEMBERSHIPS["latency"]["universe_array"],
                    INPUT_MEMBERSHIPS["latency"]["shapes"][name],
                    latency
                ))
                for name in INPUT_MEMBERSHIPS["latency"]["shapes"]
            },
            "deployment_recency": {
                name: float(fuzz.interp_membership(
                    INPUT_MEMBERSHIPS["deployment_recency"]["universe_array"],
                    INPUT_MEMBERSHIPS["deployment_recency"]["shapes"][name],
                    deployment_recency
                ))
                for name in INPUT_MEMBERSHIPS["deployment_recency"]["shapes"]
            },
            "service_criticality": {
                name: float(fuzz.interp_membership(
                    INPUT_MEMBERSHIPS["service_criticality"]["universe_array"],
                    INPUT_MEMBERSHIPS["service_criticality"]["shapes"][name],
                    service_criticality
                ))
                for name in INPUT_MEMBERSHIPS["service_criticality"]["shapes"]
            },
        }

        # Determine dominant linguistic state for frontend display
        error_rate_state = max(memberships["error_rate"], key=memberships["error_rate"].get)
        user_impact_state = max(memberships["user_impact"], key=memberships["user_impact"].get)
        latency_state = max(memberships["latency"], key=memberships["latency"].get)
        deployment_recency_state = max(memberships["deployment_recency"], key=memberships["deployment_recency"].get)
        service_criticality_state = max(memberships["service_criticality"], key=memberships["service_criticality"].get)

        # 2. Mamdani Inference & Rule Activation
        aggregated_output = np.zeros_like(self.z_universe)
        triggered_rules: List[Dict[str, Any]] = []

        for rule in self.rules:
            antecedents = rule["antecedents"]
            consequent = rule["consequent"]

            # Mamdani min-conjunction of antecedents
            firing_strengths = [
                memberships[var_name].get(term, 0.0)
                for var_name, term in antecedents.items()
            ]
            rule_weight = min(firing_strengths) if firing_strengths else 0.0

            if rule_weight > 0.02: # Significant activation threshold
                triggered_rules.append({
                    "id": rule["id"],
                    "ruleText": rule["ruleText"],
                    "weight": round(float(rule_weight), 3),
                    "contribution": rule["contribution"],
                })

                # Mamdani implication: clip consequent membership function shape
                consequent_shape = OUTPUT_MEMBERSHIPS["shapes"][consequent]
                clipped = np.fmin(rule_weight, consequent_shape)

                # Mamdani aggregation via max-operator
                aggregated_output = np.fmax(aggregated_output, clipped)

        # Sort triggered rules by activation weight descending
        triggered_rules.sort(key=lambda r: r["weight"], reverse=True)

        # 3. Defuzzification via scikit-fuzzy's centroid method
        if np.sum(aggregated_output) > 1e-6:
            coa_score = float(fuzz.defuzz(self.z_universe, aggregated_output, "centroid"))
        else:
            coa_score = 0.0

        rounded_score = int(round(np.clip(coa_score, 0.0, 100.0)))

        # Linguistic Risk Level mapping
        if rounded_score >= 78:
            risk_level = "CRITICAL"
        elif rounded_score >= 60:
            risk_level = "HIGH"
        elif rounded_score >= 35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "riskScore": rounded_score,
            "riskLevel": risk_level,
            "inputs": {
                "errorRateState": error_rate_state,
                "userImpactState": user_impact_state,
                "latencyState": latency_state,
                "deploymentRecencyState": deployment_recency_state,
                "serviceCriticalityState": service_criticality_state,
            },
            "triggeredRules": triggered_rules,
            "defuzzificationMethod": "Centroid of Area (COA)",
        }
