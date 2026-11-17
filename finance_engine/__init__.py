"""
Finance Engine for Hindsight Robo-Advisor.
This package contains pure financial logic:
- Risk profiling & suitability scoring
- Rule-based & constraint asset allocation
- Portfolio drift detection & rebalancing order generation

Zero web or framework dependencies.
"""
from .risk_scoring import score_questionnaire, get_risk_label, QUESTIONS, RULE_VERSION
from .allocation import get_allocation, compute_suitability_explanation, ASSET_PROXIES
from .rebalancer import compute_drift, needs_rebalance, compute_rebalance_orders

__all__ = [
    "score_questionnaire",
    "get_risk_label",
    "QUESTIONS",
    "RULE_VERSION",
    "get_allocation",
    "compute_suitability_explanation",
    "ASSET_PROXIES",
    "compute_drift",
    "needs_rebalance",
    "compute_rebalance_orders",
]
