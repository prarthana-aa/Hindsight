"""
Tests for Finance Engine (Pure Python: Risk Scoring, Allocation, Rebalancing).
Verifies mathematical formulas and regulatory suitability rules.
"""

import pytest
from finance_engine.risk_scoring import (
    score_questionnaire,
    get_risk_label,
    RULE_VERSION,
    QUESTIONS,
)
from finance_engine.allocation import (
    get_allocation,
    compute_suitability_explanation,
    ALLOCATION_BANDS,
)
from finance_engine.rebalancer import (
    compute_drift,
    needs_rebalance,
    compute_rebalance_orders,
)


def test_risk_score_uses_min_capacity_tolerance():
    """
    Suitability Rule: Final score must always equal min(capacity_score, tolerance_score).
    If an investor has capacity=9.0 but tolerance=3.0, the advisor must constrain risk to 3.0.
    """
    # High capacity answers (options index 3/4) but low tolerance (panic sell, 0 experience)
    answers = {
        "q1_horizon": 4,           # 15+ yrs -> high capacity
        "q2_goal_urgency": 4,      # Aggressive growth
        "q3_income_stability": 3,  # Highly secure
        "q4_liquidity_need": 3,    # Impossible to withdraw
        "q5_market_drop_reaction": 0,  # Panic and sell all! -> tolerance = 1.0
        "q6_experience": 0,        # No experience -> tolerance = 1.5
        "q7_volatility_preference": 0,  # Guaranteed return only -> tolerance = 1.5
        "q8_age_band": 0,          # Young
    }

    result = score_questionnaire(answers)
    assert result["capacity_score"] > 6.0
    assert result["tolerance_score"] < 4.0
    assert result["final_score"] == min(result["capacity_score"], result["tolerance_score"])
    assert result["constraint_driver"] == "tolerance"
    assert "Conservative" in result["risk_label"]


def test_all_risk_bands_produce_valid_allocations():
    """Every score from 1.0 to 10.0 produces a valid allocation with valid band."""
    for score in [1.0, 2.5, 3.5, 5.0, 6.5, 7.5, 8.5, 9.0, 10.0]:
        alloc = get_allocation(score)
        assert "weights" in alloc
        assert "band" in alloc
        assert alloc["expected_annual_return"] > 0
        assert alloc["expected_annual_volatility"] > 0


@pytest.mark.parametrize("band_dict", ALLOCATION_BANDS)
def test_allocation_weights_sum_to_one(band_dict):
    """Allocation weights across all strategic bands sum strictly to 1.0."""
    total_w = sum(band_dict["weights"].values())
    assert abs(total_w - 1.0) < 1e-6


def test_conservative_has_low_equity():
    """Conservative profiles (score <= 3) must have equity (NIFTY50 + INTLEQ) <= 25%."""
    alloc = get_allocation(2.0)
    weights = alloc["weights"]
    equity_exposure = weights["NIFTY50"] + weights["INTLEQ"]
    assert equity_exposure <= 0.25
    assert weights["GILT"] >= 0.50


def test_aggressive_has_high_equity():
    """Aggressive profiles (score >= 9) must have equity (NIFTY50 + INTLEQ) >= 75%."""
    alloc = get_allocation(9.5)
    weights = alloc["weights"]
    equity_exposure = weights["NIFTY50"] + weights["INTLEQ"]
    assert equity_exposure >= 0.75
    assert weights["GILT"] <= 0.15


def test_drift_detection_flags_breach():
    """Drift detection flags True when any asset breaches the 5% tolerance threshold."""
    target = {"NIFTY50": 0.50, "GILT": 0.30, "GOLD": 0.10, "INTLEQ": 0.10}
    # Current has Nifty at 56% (+6% drift)
    current = {"NIFTY50": 0.56, "GILT": 0.24, "GOLD": 0.10, "INTLEQ": 0.10}

    drift = compute_drift(current, target)
    assert drift["NIFTY50"] == 0.06
    assert drift["GILT"] == -0.06
    assert needs_rebalance(current, target, threshold=0.05) is True


def test_drift_detection_no_breach():
    """Drift within 5% band does not trigger rebalancing."""
    target = {"NIFTY50": 0.50, "GILT": 0.30, "GOLD": 0.10, "INTLEQ": 0.10}
    current = {"NIFTY50": 0.52, "GILT": 0.29, "GOLD": 0.10, "INTLEQ": 0.09}

    assert needs_rebalance(current, target, threshold=0.05) is False


def test_rebalance_orders_sells_first():
    """Rebalance orders sequence SELL proposals before BUY proposals to liberate liquidity first."""
    target = {"NIFTY50": 0.50, "GILT": 0.50}
    holdings = {
        "NIFTY50": {"quantity": 10.0, "market_value": 70000.0},  # 70% (overweight)
        "GILT": {"quantity": 300.0, "market_value": 30000.0},    # 30% (underweight)
    }
    prices = {"NIFTY50": 7000.0, "GILT": 100.0}

    res = compute_rebalance_orders(
        current_holdings=holdings,
        target_weights=target,
        total_portfolio_value=100000.0,
        current_prices=prices,
    )
    proposals = res["proposals"]
    assert len(proposals) == 2
    assert proposals[0]["side"] == "SELL"
    assert proposals[0]["asset"] == "NIFTY50"
    assert proposals[1]["side"] == "BUY"
    assert proposals[1]["asset"] == "GILT"


def test_suitability_explanation_not_empty():
    """Suitability explanation is descriptive and contains key regulatory keywords."""
    text = compute_suitability_explanation(
        risk_score=6.0,
        capacity_score=8.0,
        tolerance_score=6.0,
        goal_type="Retirement",
        horizon_years=12,
    )
    assert len(text) > 100
    assert "Suitability Rationale" in text
    assert "Retirement" in text
    assert "Equity" in text


def test_rule_version_in_output():
    """Scoring outputs contain auditable rule version string."""
    answers = {q["id"]: 0 for q in QUESTIONS}
    score_out = score_questionnaire(answers)
    assert "rule_version" in score_out
    assert score_out["rule_version"] == RULE_VERSION
