"""
Risk Profiling and Suitability Engine.
Zero web/framework dependencies. Pure Python stdlib.

Implements standard SEBI-style suitability logic:
Risk is partitioned into:
1. Risk Capacity (objective ability to absorb financial loss: time horizon, income stability, net worth, age band)
2. Risk Tolerance (psychological willingness to take risk: panic threshold, volatility comfort, market experience)

Suitability Rule:
Final Score = min(Capacity, Tolerance)
An investor may be psychologically willing to take high risk, but if their horizon is 1 year
or income is unstable, they lack capacity. Conversely, a wealthy individual who panics at 5% drops
lacks tolerance. The advisor must never recommend a portfolio exceeding the lower of the two.
"""

from typing import Dict, Any, List, Tuple

RULE_VERSION = "v1.0.0"

# (question_id, question_text, category, options)
# Each option: (label, capacity_score [1-10], tolerance_score [1-10])
QUESTIONS: List[Dict[str, Any]] = [
    {
        "id": "q1_horizon",
        "category": "capacity",
        "text": "What is your investment time horizon for this capital?",
        "options": [
            ("Less than 1 year (Very Short)", 1.0, 3.0),
            ("1 to 3 years (Short)", 3.0, 4.0),
            ("3 to 7 years (Medium)", 6.0, 6.0),
            ("7 to 15 years (Long)", 8.5, 8.0),
            ("15+ years (Very Long)", 10.0, 9.0),
        ],
    },
    {
        "id": "q2_goal_urgency",
        "category": "capacity",
        "text": "What is the primary goal for this money?",
        "options": [
            ("Emergency fund / capital preservation (Zero loss acceptable)", 1.0, 2.0),
            ("Buying a vehicle or near-term planned expense (Fixed date)", 3.5, 4.0),
            ("Down payment for a house in 5+ years (Flexible date)", 6.0, 6.0),
            ("Retirement / Wealth creation decades away", 9.0, 8.0),
            ("Aggressive growth / discretionary capital", 10.0, 10.0),
        ],
    },
    {
        "id": "q3_income_stability",
        "category": "capacity",
        "text": "How stable and predictable is your primary income stream?",
        "options": [
            ("Unstable / Freelance / Commission-based with erratic cashflow", 2.0, 4.0),
            ("Moderate / Small business / Early-stage startup employee", 5.0, 5.0),
            ("Secure / Salaried corporate or civil service professional", 8.0, 7.0),
            ("Highly secure with substantial passive income or emergency reserve", 10.0, 9.0),
        ],
    },
    {
        "id": "q4_liquidity_need",
        "category": "capacity",
        "text": "How likely are you to withdraw funds from this portfolio unexpectedly?",
        "options": [
            ("Very likely in the next 12 months", 1.0, 2.0),
            ("Possible if an emergency occurs (have limited emergency savings)", 4.0, 4.0),
            ("Unlikely (have 6+ months of separate emergency funds)", 8.0, 7.0),
            ("Virtually impossible (have dedicated reserves and insurance)", 10.0, 9.0),
        ],
    },
    {
        "id": "q5_market_drop_reaction",
        "category": "tolerance",
        "text": "If the market drops 20% over 2 months, how would you react?",
        "options": [
            ("Panic and sell all remaining investments to prevent further losses", 2.0, 1.0),
            ("Feel uncomfortable and sell a portion to move into cash", 4.0, 3.0),
            ("Hold through the volatility and do nothing", 6.0, 6.0),
            ("View it as a buying opportunity and invest additional capital", 8.0, 9.0),
            ("Be excited to aggressively deploy all available liquidity", 9.0, 10.0),
        ],
    },
    {
        "id": "q6_experience",
        "category": "tolerance",
        "text": "What is your previous investing experience with equity / mutual funds?",
        "options": [
            ("None (only fixed deposits or savings account)", 3.0, 1.5),
            ("Beginner (< 2 years, primarily passive index or mutual funds)", 5.0, 4.5),
            ("Intermediate (2-5 years through at least one market cycle)", 7.0, 7.0),
            ("Experienced (5+ years, comfortable with drawdowns and asset cycles)", 9.0, 9.5),
        ],
    },
    {
        "id": "q7_volatility_preference",
        "category": "tolerance",
        "text": "Which portfolio performance scenario would you prefer over 1 year?",
        "options": [
            ("Portfolio A: Guaranteed +6% return with 0% risk of loss", 3.0, 1.5),
            ("Portfolio B: +10% expected return, with possible range of -3% to +18%", 5.5, 5.0),
            ("Portfolio C: +14% expected return, with possible range of -12% to +28%", 7.5, 7.5),
            ("Portfolio D: +20% expected return, with possible range of -25% to +45%", 9.0, 9.5),
        ],
    },
    {
        "id": "q8_age_band",
        "category": "capacity",
        "text": "What is your age bracket?",
        "options": [
            ("Under 25 (Highest human capital runway)", 9.5, 8.0),
            ("25 to 35 (Peak earning accumulation)", 8.5, 7.5),
            ("36 to 50 (Balanced wealth accumulation)", 6.5, 6.5),
            ("51 to 60 (Approaching retirement)", 4.5, 5.0),
            ("Above 60 (Preservation / Post-retirement)", 2.5, 3.5),
        ],
    },
]


def get_risk_label(score: float) -> str:
    """
    Map score (1.0 - 10.0) to standardized SEBI-style risk categories.
    """
    if score < 3.5:
        return "Conservative"
    elif score < 5.5:
        return "Moderate-Conservative"
    elif score < 7.5:
        return "Moderate"
    elif score < 8.8:
        return "Moderate-Aggressive"
    else:
        return "Aggressive"


def score_questionnaire(answers: Dict[str, int]) -> Dict[str, Any]:
    """
    Score the user's questionnaire responses.

    Parameters:
    - answers: mapping of question_id -> selected option index (0-based)

    Returns:
    - capacity_score (float, 1-10)
    - tolerance_score (float, 1-10)
    - final_score (float, 1-10) = min(capacity, tolerance)
    - risk_label (str)
    - constraint_driver (str: 'capacity' | 'tolerance' | 'balanced')
    - rule_version (str)
    """
    capacity_points: List[float] = []
    tolerance_points: List[float] = []

    for q in QUESTIONS:
        qid = q["id"]
        cat = q.get("category", "capacity")
        option_idx = answers.get(qid, 0)
        options = q["options"]
        if option_idx < 0 or option_idx >= len(options):
            option_idx = 0

        _, cap, tol = options[option_idx]
        if cat == "capacity":
            capacity_points.append(cap)
        elif cat == "tolerance":
            tolerance_points.append(tol)
        else:
            capacity_points.append(cap)
            tolerance_points.append(tol)

    avg_capacity = sum(capacity_points) / len(capacity_points) if capacity_points else 5.0
    avg_tolerance = sum(tolerance_points) / len(tolerance_points) if tolerance_points else 5.0

    # Round to 1 decimal place
    capacity_score = round(max(1.0, min(10.0, avg_capacity)), 1)
    tolerance_score = round(max(1.0, min(10.0, avg_tolerance)), 1)

    # Suitability Core Rule:
    final_score = round(min(capacity_score, tolerance_score), 1)

    if capacity_score < tolerance_score:
        driver = "capacity"
    elif tolerance_score < capacity_score:
        driver = "tolerance"
    else:
        driver = "balanced"

    label = get_risk_label(final_score)

    return {
        "capacity_score": capacity_score,
        "tolerance_score": tolerance_score,
        "final_score": final_score,
        "risk_label": label,
        "constraint_driver": driver,
        "rule_version": RULE_VERSION,
    }
