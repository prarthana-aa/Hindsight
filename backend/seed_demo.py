"""
Demo Account Seeder for Hindsight Robo-Advisor.
Creates a fully functional, pre-populated demo account so evaluators
can experience the complete dashboard immediately without signing up.
"""

from decimal import Decimal
from datetime import datetime, date, timedelta, timezone
from sqlalchemy.orm import Session

from .config import (
    DEMO_USER_EMAIL,
    DEMO_USER_PASSWORD,
    DEMO_USER_NAME,
    DEMO_INITIAL_CAPITAL,
)
from .models import User, RiskProfile, Goal, Portfolio, Holding, Order, WalletLedger
from .auth import hash_password
from .services.ledger import credit, reconcile
from .services.order_executor import place_order
from .services.price_service import seed_prices_from_csv
from finance_engine.allocation import get_allocation, compute_suitability_explanation


def seed_demo_account(db: Session, reset_if_exists: bool = False) -> User:
    """
    Ensure the demo user exists with a populated portfolio, wallet ledger,
    and realistic investment history.
    """
    seed_prices_from_csv(db)

    demo_user = db.query(User).filter(User.email == DEMO_USER_EMAIL).first()

    if demo_user and not reset_if_exists:
        return demo_user

    if demo_user and reset_if_exists:
        # Cascade cleanup demo user
        db.delete(demo_user)
        db.commit()

    # 1. Create User
    now = datetime.now(timezone.utc)
    demo_user = User(
        email=DEMO_USER_EMAIL,
        hashed_password=hash_password(DEMO_USER_PASSWORD),
        full_name=DEMO_USER_NAME,
        age=29,
        income_band="15L-25L",
        employment_type="Software Engineer",
        pan_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        kyc_status="verified",
        consent_ts=now,
        is_demo=True,
        created_at=now - timedelta(days=90),
    )
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)

    # 2. Risk Profile & Suitability
    answers = {
        "q1_horizon": 3,           # 7-15 years
        "q2_goal_urgency": 3,      # Retirement/Wealth creation
        "q3_income_stability": 2,  # Secure salaried
        "q4_liquidity_need": 2,    # Unlikely to withdraw
        "q5_market_drop_reaction": 3,  # View as buying opportunity
        "q6_experience": 2,        # Intermediate (2-5 years)
        "q7_volatility_preference": 2,  # Portfolio C (+14%)
        "q8_age_band": 1,          # 25-35
    }
    risk_prof = RiskProfile(
        user_id=demo_user.id,
        answers=answers,
        capacity_score=8.0,
        tolerance_score=7.5,
        final_score=7.5,
        risk_label="Moderate-Aggressive",
        rule_version="v1.0.0",
        created_at=now - timedelta(days=90),
    )
    db.add(risk_prof)

    # 3. Primary Goal
    goal = Goal(
        user_id=demo_user.id,
        goal_type="house",
        title="Apartment Down Payment",
        target_amount=Decimal("2500000.00"),
        target_date=date.today() + timedelta(days=365 * 5),
        created_at=now - timedelta(days=90),
    )
    db.add(goal)

    # 4. Target Portfolio
    alloc_info = get_allocation(7.5)
    suitability = compute_suitability_explanation(
        risk_score=7.5,
        capacity_score=8.0,
        tolerance_score=7.5,
        goal_type="Apartment Down Payment",
        horizon_years=5,
    )
    portfolio = Portfolio(
        user_id=demo_user.id,
        target_allocation=alloc_info["weights"],
        strategy="rule_based_saa",
        suitability_rationale=suitability,
        rule_version="v1.0.0",
        created_at=now - timedelta(days=90),
    )
    db.add(portfolio)
    db.commit()

    # 5. Fund Virtual Wallet: ₹1,00,000 initial capital
    credit(
        db=db,
        user_id=demo_user.id,
        amount=Decimal(str(DEMO_INITIAL_CAPITAL)),
        memo="Initial Virtual Capital Deposit",
        reference_id="DEP-INIT-001",
    )
    db.commit()

    # 6. Execute Mock Orders to populate initial diversified holdings (~₹75,000 invested, ₹25,000 cash reserve)
    # NIFTY50 (~₹45,000): ~1.85 units
    place_order(
        db=db,
        user_id=demo_user.id,
        asset="NIFTY50",
        side="BUY",
        quantity=Decimal("1.85"),
        idempotency_key=f"demo_init_order_nifty_{demo_user.id}",
    )

    # GILT (~₹14,000): ~140 units
    place_order(
        db=db,
        user_id=demo_user.id,
        asset="GILT",
        side="BUY",
        quantity=Decimal("140.0"),
        idempotency_key=f"demo_init_order_gilt_{demo_user.id}",
    )

    # GOLD (~₹4,000): ~0.05 units
    place_order(
        db=db,
        user_id=demo_user.id,
        asset="GOLD",
        side="BUY",
        quantity=Decimal("0.05"),
        idempotency_key=f"demo_init_order_gold_{demo_user.id}",
    )

    # INTLEQ (~₹8,000): ~38 units
    place_order(
        db=db,
        user_id=demo_user.id,
        asset="INTLEQ",
        side="BUY",
        quantity=Decimal("38.0"),
        idempotency_key=f"demo_init_order_intleq_{demo_user.id}",
    )

    # 7. Add a subsequent monthly SIP deposit & buy order for realism
    credit(
        db=db,
        user_id=demo_user.id,
        amount=Decimal("10000.00"),
        memo="Monthly SIP Top-up (Automated)",
        reference_id="SIP-AUTO-002",
    )
    db.commit()

    place_order(
        db=db,
        user_id=demo_user.id,
        asset="NIFTY50",
        side="BUY",
        quantity=Decimal("0.25"),
        idempotency_key=f"demo_sip_order_nifty_{demo_user.id}",
    )

    # Verify reconciliation passes
    reconcile(db, demo_user.id)
    return demo_user

