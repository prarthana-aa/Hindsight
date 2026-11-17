"""
Asset Allocation and Suitability Rationale Engine.
Zero web/framework dependencies. Pure Python.

Implements rule-based strategic asset allocation (SAA) with 4 core proxy asset classes:
- NIFTY50: Indian Large-Cap Equity proxy (wealth compounding / domestic growth)
- GILT: Long-duration Indian Government Bond proxy (capital stability & regular yield)
- GOLD: Sovereign/Physical Gold proxy (inflation hedge & geopolitical crisis shelter)
- INTLEQ: Developed Market International Equity proxy (currency depreciation hedge & geographical diversification)
"""

from typing import Dict, Any, List

# Asset class metadata and proxy mapping
ASSET_PROXIES = {
    "NIFTY50": {
        "name": "Nifty 50 Index (Domestic Equity)",
        "role": "Core Growth & Capital Appreciation",
        "expected_return": 0.12,
        "volatility": 0.16,
    },
    "GILT": {
        "name": "10-Year Indian Sovereign Gilt (Debt)",
        "role": "Capital Preservation & Volatility Buffer",
        "expected_return": 0.07,
        "volatility": 0.04,
    },
    "GOLD": {
        "name": "Sovereign Gold / Physical Proxy",
        "role": "Inflation Hedge & Tail-Risk Defense",
        "expected_return": 0.09,
        "volatility": 0.12,
    },
    "INTLEQ": {
        "name": "International Equity (Nasdaq/S&P Proxy)",
        "role": "Geographic Diversification & Currency Hedge",
        "expected_return": 0.11,
        "volatility": 0.18,
    },
}

# SAA Target Allocation Table based on Risk Scores (1.0 - 10.0)
ALLOCATION_BANDS: List[Dict[str, Any]] = [
    {
        "band": "Conservative",
        "min_score": 1.0,
        "max_score": 3.49,
        "weights": {
            "NIFTY50": 0.15,
            "GILT": 0.60,
            "GOLD": 0.20,
            "INTLEQ": 0.05,
        },
        "description": "Heavy debt/gold weighting designed to safeguard principal and minimize drawdown risk.",
    },
    {
        "band": "Moderate-Conservative",
        "min_score": 3.5,
        "max_score": 5.49,
        "weights": {
            "NIFTY50": 0.30,
            "GILT": 0.45,
            "GOLD": 0.15,
            "INTLEQ": 0.10,
        },
        "description": "Conservative growth with substantial fixed income cushion and modest equity participation.",
    },
    {
        "band": "Moderate",
        "min_score": 5.5,
        "max_score": 7.49,
        "weights": {
            "NIFTY50": 0.50,
            "GILT": 0.30,
            "GOLD": 0.10,
            "INTLEQ": 0.10,
        },
        "description": "Balanced 60/40 growth/defensive blend providing market returns with moderated portfolio volatility.",
    },
    {
        "band": "Moderate-Aggressive",
        "min_score": 7.5,
        "max_score": 8.79,
        "weights": {
            "NIFTY50": 0.65,
            "GILT": 0.20,
            "GOLD": 0.05,
            "INTLEQ": 0.10,
        },
        "description": "Growth-oriented with 75% total equity exposure and debt reserved for opportunistic dry powder.",
    },
    {
        "band": "Aggressive",
        "min_score": 8.8,
        "max_score": 10.0,
        "weights": {
            "NIFTY50": 0.75,
            "GILT": 0.10,
            "GOLD": 0.05,
            "INTLEQ": 0.10,
        },
        "description": "Maximum wealth compounding orientation with 85% equity exposure and minimal debt dampener.",
    },
]


def get_allocation(risk_score: float) -> Dict[str, Any]:
    """
    Get recommended asset allocation given a final risk score (1.0 to 10.0).

    Returns:
    - weights: Dict[str, float] (summing strictly to 1.0)
    - band: str
    - description: str
    - expected_annual_return: float
    - expected_annual_volatility: float
    """
    score = max(1.0, min(10.0, risk_score))

    selected_band = ALLOCATION_BANDS[0]
    for b in ALLOCATION_BANDS:
        if b["min_score"] <= score <= b["max_score"]:
            selected_band = b
            break

    weights = selected_band["weights"].copy()

    # Calculate portfolio weighted expected return
    exp_return = sum(
        weights[asset] * ASSET_PROXIES[asset]["expected_return"]
        for asset in weights
    )

    # Simplified portfolio volatility approximation (ignoring correlation for v1 rule-based)
    exp_vol = sum(
        weights[asset] * ASSET_PROXIES[asset]["volatility"]
        for asset in weights
    )

    return {
        "risk_score": score,
        "band": selected_band["band"],
        "weights": weights,
        "description": selected_band["description"],
        "expected_annual_return": round(exp_return, 4),
        "expected_annual_volatility": round(exp_vol, 4),
    }


def compute_suitability_explanation(
    risk_score: float,
    capacity_score: float,
    tolerance_score: float,
    goal_type: str = "Wealth Creation",
    horizon_years: int = 5,
) -> str:
    """
    Generate an auditable, human-readable suitability explanation matching SEBI standards.
    Explains exactly why this specific allocation was chosen and why risk was constrained.
    """
    alloc = get_allocation(risk_score)
    weights = alloc["weights"]
    equity_pct = int(round((weights["NIFTY50"] + weights["INTLEQ"]) * 100))
    debt_pct = int(round(weights["GILT"] * 100))
    gold_pct = int(round(weights["GOLD"] * 100))

    if capacity_score < tolerance_score:
        constraint_clause = (
            f"Although your psychological risk tolerance is high ({tolerance_score}/10), "
            f"your financial capacity score ({capacity_score}/10) dictates a conservative ceiling. "
            f"Because you have near-term liquidity commitments or an investment horizon of ~{horizon_years} years, "
            f"we strictly avoid over-allocating to volatile assets to prevent forced capital liquidations."
        )
    elif tolerance_score < capacity_score:
        constraint_clause = (
            f"While your financial capacity could theoretically absorb higher volatility ({capacity_score}/10), "
            f"your behavioral risk tolerance score ({tolerance_score}/10) indicates high discomfort with market drawdowns. "
            f"To prevent panic-selling during inevitable equity corrections, equity is restricted to {equity_pct}%."
        )
    else:
        constraint_clause = (
            f"Your financial risk capacity ({capacity_score}/10) and emotional risk tolerance ({tolerance_score}/10) "
            f"are in close harmony. This balanced alignment permits an optimal allocation designed to achieve {goal_type}."
        )

    explanation = (
        f"Suitability Rationale ({alloc['band']} Profile, Score: {risk_score}/10):\n\n"
        f"Based on your target goal '{goal_type}' and a {horizon_years}-year time horizon, we have constructed a "
        f"diversified 4-asset portfolio consisting of {equity_pct}% Equity ({int(weights['NIFTY50']*100)}% Nifty 50, "
        f"{int(weights['INTLEQ']*100)}% International), {debt_pct}% Gilt Debt, and {gold_pct}% Gold.\n\n"
        f"{constraint_clause}\n\n"
        f"The {debt_pct}% sovereign debt anchor yields steady income while dampening portfolio swings, "
        f"and the {gold_pct}% gold position acts as a non-correlated hedge against macroeconomic and currency stress."
    )
    return explanation
