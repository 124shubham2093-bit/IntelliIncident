"""
Fuzzy Logic Membership Functions for IntelliIncident
Implements triangular (trimf) and trapezoidal (trapmf) membership functions
across standard universes of discourse explicitly using scikit-fuzzy (skfuzzy).
"""

from typing import Tuple, Dict, Any, Callable
import numpy as np
import skfuzzy as fuzz
from skfuzzy import membership as mf

# Input Universes of Discourse Discretized Arrays
ERROR_RATE_UNIVERSE = np.linspace(0.0, 50.0, 501)
USER_IMPACT_UNIVERSE = np.linspace(0.0, 100.0, 501)
LATENCY_UNIVERSE = np.linspace(0.0, 3000.0, 601)
DEPLOYMENT_RECENCY_UNIVERSE = np.linspace(0.0, 180.0, 361)
SERVICE_CRITICALITY_UNIVERSE = np.linspace(1.0, 5.0, 401)
RISK_UNIVERSE = np.linspace(0.0, 100.0, 501)

def trimf(x: float, abc: Tuple[float, float, float]) -> float:
    """Evaluate triangular membership using scikit-fuzzy."""
    abc_arr = np.asarray(abc, dtype=float)
    x_arr = np.asarray([x], dtype=float)
    val = mf.trimf(x_arr, abc_arr)[0]
    return float(val)

def trapmf(x: float, abcd: Tuple[float, float, float, float]) -> float:
    """Evaluate trapezoidal membership using scikit-fuzzy."""
    abcd_arr = np.asarray(abcd, dtype=float)
    x_arr = np.asarray([x], dtype=float)
    val = mf.trapmf(x_arr, abcd_arr)[0]
    return float(val)

# Input Universes of Discourse & Fuzzy Sets using scikit-fuzzy
INPUT_MEMBERSHIPS = {
    "error_rate": {
        "universe": (0.0, 50.0),
        "universe_array": ERROR_RATE_UNIVERSE,
        "sets": {
            "LOW": lambda x: trapmf(x, (0.0, 0.0, 5.0, 12.0)),
            "MEDIUM": lambda x: trimf(x, (8.0, 18.0, 28.0)),
            "HIGH": lambda x: trapmf(x, (22.0, 35.0, 50.0, 50.0)),
        },
        "shapes": {
            "LOW": mf.trapmf(ERROR_RATE_UNIVERSE, [0.0, 0.0, 5.0, 12.0]),
            "MEDIUM": mf.trimf(ERROR_RATE_UNIVERSE, [8.0, 18.0, 28.0]),
            "HIGH": mf.trapmf(ERROR_RATE_UNIVERSE, [22.0, 35.0, 50.0, 50.0]),
        },
    },
    "user_impact": {
        "universe": (0.0, 100.0),
        "universe_array": USER_IMPACT_UNIVERSE,
        "sets": {
            "LOW": lambda x: trapmf(x, (0.0, 0.0, 15.0, 35.0)),
            "MEDIUM": lambda x: trimf(x, (25.0, 50.0, 75.0)),
            "HIGH": lambda x: trapmf(x, (65.0, 85.0, 100.0, 100.0)),
        },
        "shapes": {
            "LOW": mf.trapmf(USER_IMPACT_UNIVERSE, [0.0, 0.0, 15.0, 35.0]),
            "MEDIUM": mf.trimf(USER_IMPACT_UNIVERSE, [25.0, 50.0, 75.0]),
            "HIGH": mf.trapmf(USER_IMPACT_UNIVERSE, [65.0, 85.0, 100.0, 100.0]),
        },
    },
    "latency": {
        "universe": (0.0, 3000.0),
        "universe_array": LATENCY_UNIVERSE,
        "sets": {
            "LOW": lambda x: trapmf(x, (0.0, 0.0, 200.0, 600.0)),
            "MEDIUM": lambda x: trimf(x, (400.0, 1000.0, 1600.0)),
            "HIGH": lambda x: trapmf(x, (1300.0, 2200.0, 3000.0, 3000.0)),
        },
        "shapes": {
            "LOW": mf.trapmf(LATENCY_UNIVERSE, [0.0, 0.0, 200.0, 600.0]),
            "MEDIUM": mf.trimf(LATENCY_UNIVERSE, [400.0, 1000.0, 1600.0]),
            "HIGH": mf.trapmf(LATENCY_UNIVERSE, [1300.0, 2200.0, 3000.0, 3000.0]),
        },
    },
    "deployment_recency": {
        "universe": (0.0, 180.0),
        "universe_array": DEPLOYMENT_RECENCY_UNIVERSE,
        "sets": {
            "RECENT": lambda x: trapmf(x, (0.0, 0.0, 15.0, 45.0)),
            "MODERATE": lambda x: trimf(x, (30.0, 75.0, 120.0)),
            "OLD": lambda x: trapmf(x, (90.0, 150.0, 180.0, 180.0)),
        },
        "shapes": {
            "RECENT": mf.trapmf(DEPLOYMENT_RECENCY_UNIVERSE, [0.0, 0.0, 15.0, 45.0]),
            "MODERATE": mf.trimf(DEPLOYMENT_RECENCY_UNIVERSE, [30.0, 75.0, 120.0]),
            "OLD": mf.trapmf(DEPLOYMENT_RECENCY_UNIVERSE, [90.0, 150.0, 180.0, 180.0]),
        },
    },
    "service_criticality": {
        "universe": (1.0, 5.0),
        "universe_array": SERVICE_CRITICALITY_UNIVERSE,
        "sets": {
            "LOW": lambda x: trapmf(x, (1.0, 1.0, 1.5, 2.5)),
            "MEDIUM": lambda x: trimf(x, (2.0, 3.0, 4.0)),
            "HIGH": lambda x: trapmf(x, (3.5, 4.5, 5.0, 5.0)),
        },
        "shapes": {
            "LOW": mf.trapmf(SERVICE_CRITICALITY_UNIVERSE, [1.0, 1.0, 1.5, 2.5]),
            "MEDIUM": mf.trimf(SERVICE_CRITICALITY_UNIVERSE, [2.0, 3.0, 4.0]),
            "HIGH": mf.trapmf(SERVICE_CRITICALITY_UNIVERSE, [3.5, 4.5, 5.0, 5.0]),
        },
    },
}

# Output Universe of Discourse (Risk Score: 0 to 100) using scikit-fuzzy
OUTPUT_MEMBERSHIPS = {
    "universe": (0.0, 100.0),
    "universe_array": RISK_UNIVERSE,
    "sets": {
        "LOW": lambda x: trapmf(x, (0.0, 0.0, 15.0, 35.0)),
        "MEDIUM": lambda x: trimf(x, (25.0, 50.0, 70.0)),
        "HIGH": lambda x: trimf(x, (55.0, 75.0, 90.0)),
        "VERY_HIGH": lambda x: trapmf(x, (75.0, 88.0, 100.0, 100.0)),
    },
    "shapes": {
        "LOW": mf.trapmf(RISK_UNIVERSE, [0.0, 0.0, 15.0, 35.0]),
        "MEDIUM": mf.trimf(RISK_UNIVERSE, [25.0, 50.0, 70.0]),
        "HIGH": mf.trimf(RISK_UNIVERSE, [55.0, 75.0, 90.0]),
        "VERY_HIGH": mf.trapmf(RISK_UNIVERSE, [75.0, 88.0, 100.0, 100.0]),
    },
}
