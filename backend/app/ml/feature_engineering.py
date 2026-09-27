"""
Feature Engineering Layer for IntelliIncident
Extracts, transforms, and standardizes operational telemetry signals.
Prevents target leakage strictly: ground truth severity and risk scores
are never passed as model features.
"""

from typing import Dict, Any, List, Union
import numpy as np
import pandas as pd

FEATURE_COLUMNS = [
    "error_rate",
    "latency_p99",
    "latency_p50",
    "affected_users",
    "cpu_utilization",
    "memory_utilization",
    "deployment_recency_minutes",
    "request_volume",
    "service_criticality",
    "latency_ratio",
    "error_volume_interaction",
    "resource_saturation",
]

FEATURE_METADATA = [
    {"feature": "error_rate", "displayName": "Error Rate Spike (%)", "category": "Error Telemetry"},
    {"feature": "latency_p99", "displayName": "P99 Latency (ms)", "category": "Latency"},
    {"feature": "latency_p50", "displayName": "P50 Latency (ms)", "category": "Latency"},
    {"feature": "affected_users", "displayName": "Active User Impact Volume", "category": "Business SLA"},
    {"feature": "cpu_utilization", "displayName": "CPU Saturation (%)", "category": "Infrastructure"},
    {"feature": "memory_utilization", "displayName": "Memory Saturation (%)", "category": "Infrastructure"},
    {"feature": "deployment_recency_minutes", "displayName": "Deployment Recency (mins)", "category": "Change Events"},
    {"feature": "request_volume", "displayName": "Request Volume (req/s)", "category": "Traffic Load"},
    {"feature": "service_criticality", "displayName": "Service Criticality Tier", "category": "Topology"},
    {"feature": "latency_ratio", "displayName": "P99/P50 Latency Ratio", "category": "Latency Tail"},
    {"feature": "error_volume_interaction", "displayName": "Error Volume Rate", "category": "Error Telemetry"},
    {"feature": "resource_saturation", "displayName": "Peak Resource Saturation", "category": "Infrastructure"},
]

def extract_features(data: Union[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]) -> pd.DataFrame:
    """
    Extract and engineer features from raw telemetry dictionaries or DataFrame.
    Guarantees no target leakage: target fields ('severity', 'risk_score', 'risk')
    are excluded from the returned feature DataFrame.
    """
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # Map possible alternative casing from API / frontend
    column_mapping = {
        "errorRate": "error_rate",
        "latencyP99": "latency_p99",
        "latencyP50": "latency_p50",
        "affectedUsers": "affected_users",
        "affectedUsersCount": "affected_users",
        "cpuUtilization": "cpu_utilization",
        "memoryUtilization": "memory_utilization",
        "deploymentRecencyMinutes": "deployment_recency_minutes",
        "requestVolume": "request_volume",
        "serviceCriticality": "service_criticality",
    }
    df = df.rename(columns=column_mapping)

    # Defaults for missing features
    defaults = {
        "error_rate": 0.0,
        "latency_p99": 100.0,
        "latency_p50": 30.0,
        "affected_users": 0,
        "cpu_utilization": 20.0,
        "memory_utilization": 20.0,
        "deployment_recency_minutes": 180,
        "request_volume": 1000,
        "service_criticality": 3,
    }
    for col, default_val in defaults.items():
        if col not in df.columns:
            df[col] = default_val
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default_val)

    # Compute engineered features
    p50_safe = df["latency_p50"].clip(lower=1.0)
    df["latency_ratio"] = df["latency_p99"] / p50_safe
    df["error_volume_interaction"] = (df["error_rate"] * df["request_volume"]) / 100.0
    df["resource_saturation"] = df[["cpu_utilization", "memory_utilization"]].max(axis=1)

    # Return only feature columns
    return df[FEATURE_COLUMNS]
