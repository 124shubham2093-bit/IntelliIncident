"""
Fuzzy Rule Base for IntelliIncident Soft Computing Risk Assessment
Defines Mamdani IF-THEN rules for incident risk evaluation.
"""

from typing import List, Dict, Any

FUZZY_RULES = [
    {
        "id": "RULE-01",
        "antecedents": {"error_rate": "HIGH", "user_impact": "HIGH"},
        "consequent": "VERY_HIGH",
        "ruleText": "IF Error Rate is HIGH AND User Impact is HIGH THEN Risk is VERY HIGH",
        "description": "Catastrophic business failure pattern with broad customer-facing errors.",
        "contribution": "High activation from concurrent error rate and broad user impact.",
    },
    {
        "id": "RULE-02",
        "antecedents": {"latency": "HIGH", "service_criticality": "HIGH"},
        "consequent": "HIGH",
        "ruleText": "IF Latency is HIGH AND Service Criticality is HIGH THEN Risk is HIGH",
        "description": "Tier-1 SLA breach due to severe responsiveness degradation.",
        "contribution": "Elevated latency on mission-critical service.",
    },
    {
        "id": "RULE-03",
        "antecedents": {"deployment_recency": "RECENT", "error_rate": "HIGH"},
        "consequent": "VERY_HIGH",
        "ruleText": "IF Deployment Recency is RECENT AND Error Rate is HIGH THEN Risk is VERY HIGH",
        "description": "Defective deployment anomaly with immediate regression impact.",
        "contribution": "Temporal proximity to recent release correlates strongly with failure.",
    },
    {
        "id": "RULE-04",
        "antecedents": {"error_rate": "MEDIUM", "user_impact": "MEDIUM"},
        "consequent": "MEDIUM",
        "ruleText": "IF Error Rate is MEDIUM AND User Impact is MEDIUM THEN Risk is MEDIUM",
        "description": "Moderate operational incident with contained blast radius.",
        "contribution": "Moderate operating telemetry within acceptable variance.",
    },
    {
        "id": "RULE-05",
        "antecedents": {"latency": "MEDIUM", "service_criticality": "LOW"},
        "consequent": "LOW",
        "ruleText": "IF Latency is MEDIUM AND Service Criticality is LOW THEN Risk is LOW",
        "description": "Background or non-critical latency elevation within tolerable limits.",
        "contribution": "Low criticality tier dampens latency impact.",
    },
    {
        "id": "RULE-06",
        "antecedents": {"error_rate": "LOW", "user_impact": "LOW"},
        "consequent": "LOW",
        "ruleText": "IF Error Rate is LOW AND User Impact is LOW THEN Risk is LOW",
        "description": "Nominal baseline operational state.",
        "contribution": "Nominal operational telemetry baseline.",
    },
    {
        "id": "RULE-07",
        "antecedents": {"deployment_recency": "RECENT", "latency": "HIGH"},
        "consequent": "HIGH",
        "ruleText": "IF Deployment Recency is RECENT AND Latency is HIGH THEN Risk is HIGH",
        "description": "Post-release performance degradation or resource contention.",
        "contribution": "Recent code deployment causing latency degradation.",
    },
    {
        "id": "RULE-08",
        "antecedents": {"service_criticality": "HIGH", "user_impact": "HIGH"},
        "consequent": "VERY_HIGH",
        "ruleText": "IF Service Criticality is HIGH AND User Impact is HIGH THEN Risk is VERY HIGH",
        "description": "Severe consumer disruption on critical tier service.",
        "contribution": "High customer blast radius on Tier 1 infrastructure.",
    },
    {
        "id": "RULE-09",
        "antecedents": {"error_rate": "HIGH", "latency": "HIGH"},
        "consequent": "VERY_HIGH",
        "ruleText": "IF Error Rate is HIGH AND Latency is HIGH THEN Risk is VERY HIGH",
        "description": "Cascading service failure across both reliability and speed.",
        "contribution": "Dual degradation across latency and reliability metrics.",
    },
    {
        "id": "RULE-10",
        "antecedents": {"error_rate": "LOW", "latency": "LOW", "service_criticality": "LOW"},
        "consequent": "LOW",
        "ruleText": "IF Error Rate is LOW AND Latency is LOW AND Service Criticality is LOW THEN Risk is LOW",
        "description": "Healthy non-critical operations.",
        "contribution": "Clean telemetry on auxiliary service.",
    },
]
