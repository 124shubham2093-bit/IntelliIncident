"""
Root Cause Analysis Engine for IntelliIncident
Generates ranked hypotheses with confidence scores, factual evidence citations,
and causal explanations.
"""

from typing import Dict, Any, List
from backend.app.rca.evidence_correlator import EvidenceCorrelator

CATEGORY_DESCRIPTIONS = {
    "DEPLOYMENT": {
        "candidate": "Recent Deployment Regression",
        "explanation": "High temporal correlation between production release completion and immediate error rate/latency degradation.",
    },
    "DATABASE": {
        "candidate": "Database Connection Pool Exhaustion & Query Contention",
        "explanation": "Elevated P99 response time and severe tail latency ratio indicative of exhausted connection pool or table lock serialization.",
    },
    "INFRASTRUCTURE": {
        "candidate": "Compute Resource Saturation / Memory Pressure",
        "explanation": "CPU or memory utilization exceeding nominal cluster thresholds leading to throttling and pod instability.",
    },
    "CODE_ERROR": {
        "candidate": "Unhandled Runtime Exception / Nil Pointer Dereference",
        "explanation": "Active unhandled exceptions surfaced in stderr/diagnostic logs causing request termination.",
    },
    "TRAFFIC": {
        "candidate": "Traffic Surge Exceeding Provisioned Capacity",
        "explanation": "Sudden arrival rate acceleration beyond ingress provisioning causing request queuing.",
    },
    "NETWORK": {
        "candidate": "Inter-Service Network Latency & Socket Degradation",
        "explanation": "Socket timeouts and transport handshake latency across internal mesh or third-party gateways.",
    },
}

class RootCauseEngine:
    def __init__(self):
        self.correlator = EvidenceCorrelator()

    def analyze(self, incident: Dict[str, Any], metrics: Dict[str, Any], logs: List[Dict[str, Any]] = None, deployments: List[Dict[str, Any]] = None, tickets: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        logs = logs or []
        deployments = deployments or []
        tickets = tickets or []

        correlations = self.correlator.correlate(incident, metrics, logs, deployments, tickets)

        candidates = []
        for cat_name, data in correlations.items():
            meta = CATEGORY_DESCRIPTIONS.get(cat_name, {
                "candidate": f"{cat_name.title()} Incident",
                "explanation": f"Observed symptoms indicate potential {cat_name.lower()} disruption.",
            })

            # Format evidence list; provide standard fallback if none triggered
            ev_list = data["evidence"]
            if not ev_list:
                ev_list = [f"Baseline metric inspection within acceptable limits for {cat_name.lower()}."]

            candidates.append({
                "candidate": meta["candidate"],
                "score": data["score"],
                "evidence": ev_list,
                "explanation": meta["explanation"],
                "category": cat_name,
            })

        # Rank candidates descending by confidence score
        candidates.sort(key=lambda c: c["score"], reverse=True)

        # Assign deterministic IDs
        for idx, cand in enumerate(candidates):
            cand["id"] = f"RC-{idx+1:02d}"

        return candidates
