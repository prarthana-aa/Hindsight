"""
Robo-Advice and Suitability Router.
Exposes risk questionnaire, scoring, asset allocation, and suitability explanation.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, RiskProfile, Portfolio, AuditLog
from ..auth import get_current_user
from ..schemas import RiskProfileSubmitRequest, RecommendationResponse, UserRecommendationResponse, AssetRecommendationResponse
from ..config import DISCLAIMER_TEXT
from finance_engine.risk_scoring import (
    QUESTIONS,
    score_questionnaire,
    RULE_VERSION,
)
from finance_engine.allocation import (
    get_allocation,
    compute_suitability_explanation,
    ASSET_PROXIES,
)

router = APIRouter(prefix="/advice", tags=["Robo-Advice & Suitability"])


@router.get("/profile", response_model=UserRecommendationResponse)
def get_user_recommendation(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the authenticated user's persisted risk profile and target allocation."""
    risk_profile = db.query(RiskProfile).filter(RiskProfile.user_id == user.id).first()
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    if not risk_profile or not portfolio or not portfolio.target_allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Complete the risk assessment to generate your recommendation.",
        )

    allocation = get_allocation(risk_profile.final_score)
    capacity = float(risk_profile.capacity_score)
    tolerance = float(risk_profile.tolerance_score)
    driver = "capacity" if capacity < tolerance else "tolerance" if tolerance < capacity else "balanced"
    assets = [
        AssetRecommendationResponse(
            asset=asset,
            name=metadata["name"],
            role=metadata["role"],
            target_weight=float(portfolio.target_allocation.get(asset, 0.0)),
            expected_return=float(metadata["expected_return"]),
            volatility=float(metadata["volatility"]),
        )
        for asset, metadata in ASSET_PROXIES.items()
    ]
    return UserRecommendationResponse(
        risk_score=float(risk_profile.final_score),
        risk_label=risk_profile.risk_label,
        capacity_score=capacity,
        tolerance_score=tolerance,
        constraint_driver=driver,
        target_allocation={key: float(value) for key, value in portfolio.target_allocation.items()},
        suitability_explanation=portfolio.suitability_rationale or allocation["description"],
        expected_annual_return=float(allocation["expected_annual_return"]),
        expected_annual_volatility=float(allocation["expected_annual_volatility"]),
        rule_version=risk_profile.rule_version,
        disclaimer=DISCLAIMER_TEXT,
        assets=assets,
    )


@router.get("/questions")
def get_risk_questions():
    """
    Retrieve the 8 standardized suitability questionnaire questions and answer options.
    """
    return {
        "rule_version": RULE_VERSION,
        "questions": QUESTIONS,
        "asset_proxies": ASSET_PROXIES,
        "disclaimer": DISCLAIMER_TEXT,
    }


@router.post("/score", response_model=RecommendationResponse)
def evaluate_risk_and_recommend(payload: RiskProfileSubmitRequest):
    """
    Evaluate user's answers and generate suitability recommendation.
    Pure calculation, does not require authentication or database mutations.
    """
    score_res = score_questionnaire(payload.answers)
    final_score = score_res["final_score"]
    cap_score = score_res["capacity_score"]
    tol_score = score_res["tolerance_score"]

    alloc_res = get_allocation(final_score)

    suitability_text = compute_suitability_explanation(
        risk_score=final_score,
        capacity_score=cap_score,
        tolerance_score=tol_score,
        goal_type=payload.goal_type or "Wealth Creation",
        horizon_years=payload.horizon_years or 5,
    )

    return RecommendationResponse(
        risk_score=final_score,
        risk_label=score_res["risk_label"],
        capacity_score=cap_score,
        tolerance_score=tol_score,
        constraint_driver=score_res["constraint_driver"],
        target_allocation=alloc_res["weights"],
        suitability_explanation=suitability_text,
        expected_annual_return=alloc_res["expected_annual_return"],
        expected_annual_volatility=alloc_res["expected_annual_volatility"],
        rule_version=RULE_VERSION,
        disclaimer=DISCLAIMER_TEXT,
    )


@router.post("/apply", response_model=RecommendationResponse)
def apply_recommendation_to_user(
    payload: RiskProfileSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Score the questionnaire and apply the recommended portfolio allocation to the user's account.
    Creates an immutable audit log entry containing the exact inputs and rule version.
    """
    rec = evaluate_risk_and_recommend(payload)
    now = datetime.now(timezone.utc)

    # 1. Update or create RiskProfile
    existing_profile = (
        db.query(RiskProfile).filter(RiskProfile.user_id == user.id).first()
    )
    if existing_profile:
        existing_profile.answers = payload.answers
        existing_profile.capacity_score = rec.capacity_score
        existing_profile.tolerance_score = rec.tolerance_score
        existing_profile.final_score = rec.risk_score
        existing_profile.risk_label = rec.risk_label
        existing_profile.rule_version = rec.rule_version
    else:
        new_profile = RiskProfile(
            user_id=user.id,
            answers=payload.answers,
            capacity_score=rec.capacity_score,
            tolerance_score=rec.tolerance_score,
            final_score=rec.risk_score,
            risk_label=rec.risk_label,
            rule_version=rec.rule_version,
            created_at=now,
        )
        db.add(new_profile)

    # 2. Update or create Portfolio target allocation
    existing_portfolio = (
        db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    )
    if existing_portfolio:
        existing_portfolio.target_allocation = rec.target_allocation
        existing_portfolio.suitability_rationale = rec.suitability_explanation
        existing_portfolio.rule_version = rec.rule_version
    else:
        new_portfolio = Portfolio(
            user_id=user.id,
            target_allocation=rec.target_allocation,
            strategy="rule_based_saa",
            suitability_rationale=rec.suitability_explanation,
            rule_version=rec.rule_version,
            created_at=now,
        )
        db.add(new_portfolio)

    # 3. Create compliance AuditLog record
    audit_entry = AuditLog(
        user_id=user.id,
        event_type="RECOMMENDATION_APPLIED",
        event_data={
            "answers": payload.answers,
            "capacity_score": rec.capacity_score,
            "tolerance_score": rec.tolerance_score,
            "final_score": rec.risk_score,
            "risk_label": rec.risk_label,
            "target_allocation": rec.target_allocation,
            "suitability_explanation": rec.suitability_explanation,
        },
        rule_version=rec.rule_version,
        created_at=now,
    )
    db.add(audit_entry)
    db.commit()

    return rec
