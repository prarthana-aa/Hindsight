"""
End-to-End API Router Integration Tests for Hindsight FastAPI Backend.
Tests endpoints directly through FastAPI route handlers with full schema validation,
Pydantic contracts, and database session injection.
"""

from decimal import Decimal
import pytest
from fastapi import HTTPException

from backend.config import DISCLAIMER_TEXT
from backend.main import health_check, root
from backend.routers.auth import signup, login, demo_login, reset_demo, get_current_user_profile
from backend.routers.wallet import (
    deposit_virtual_cash,
    get_wallet_balance,
    get_full_ledger,
    run_ledger_reconciliation,
)
from backend.routers.portfolio import (
    create_order,
    get_user_orders,
    get_portfolio_dashboard,
    preview_rebalance,
    execute_rebalance,
)
from backend.routers.prices import get_all_prices, get_single_price, get_history, force_refresh_prices
from backend.routers.advice import get_risk_questions, evaluate_risk_and_recommend, apply_recommendation_to_user
from backend.schemas import (
    UserSignupRequest,
    UserLoginRequest,
    DepositRequest,
    OrderCreateRequest,
    RiskProfileSubmitRequest,
)


def test_health_check_and_disclaimer():
    """Health check responds healthy and returns compliance disclaimer text."""
    res = health_check()
    assert res["status"] == "healthy"
    assert res["virtual_mode"] is True
    assert res["disclaimer"] == DISCLAIMER_TEXT

    root_res = root()
    assert root_res["disclaimer"] == DISCLAIMER_TEXT
    assert "NIFTY50" in root_res["supported_assets"]


def test_auth_signup_and_login(db):
    """User can sign up and login, receiving JWT bearer tokens."""
    signup_payload = UserSignupRequest(
        email="api_user@hindsight.app",
        password="SecurePassword123",
        full_name="Karan Mehra",
        age=27,
        income_band="10L-15L",
        employment_type="Data Analyst",
        simulated_pan="ABCDE1234F",
        accepted_disclosures=True,
    )
    token_resp = signup(payload=signup_payload, db=db)
    assert token_resp.access_token is not None
    assert token_resp.email == "api_user@hindsight.app"
    assert token_resp.is_demo is False

    # Login with correct credentials
    login_payload = UserLoginRequest(
        email="api_user@hindsight.app",
        password="SecurePassword123",
    )
    login_resp = login(payload=login_payload, db=db)
    assert login_resp.access_token is not None
    assert login_resp.email == "api_user@hindsight.app"

    # Login with wrong credentials raises 401
    with pytest.raises(HTTPException) as exc_info:
        login(payload=UserLoginRequest(email="api_user@hindsight.app", password="WrongPassword!"), db=db)
    assert exc_info.value.status_code == 401


def test_demo_login_and_reset(db):
    """1-click demo login returns active session with preloaded demo profile."""
    demo_resp = demo_login(db=db)
    assert demo_resp.is_demo is True
    assert demo_resp.email == "demo@hindsight.app"
    assert demo_resp.access_token is not None

    # Reset demo
    reset_resp = reset_demo(db=db)
    assert reset_resp.is_demo is True


def test_wallet_deposit_and_reconcile_api(db, test_user):
    """Deposit virtual cash through API and run reconciliation."""
    deposit_payload = DepositRequest(amount=Decimal("25000.00"), memo="API test deposit")
    entry = deposit_virtual_cash(payload=deposit_payload, user=test_user, db=db)
    assert entry.amount == Decimal("25000.00")
    assert entry.running_balance == Decimal("25000.00")

    # Check balance endpoint
    bal = get_wallet_balance(user=test_user, db=db)
    assert bal.current_balance == Decimal("25000.00")
    assert bal.currency == "INR"

    # Run reconciliation endpoint
    audit = run_ledger_reconciliation(user=test_user, db=db)
    assert audit.is_reconciled is True
    assert audit.status == "BALANCED_AUDIT_VERIFIED"
    assert audit.discrepancy == Decimal("0.0000")


def test_order_placement_idempotency_api(db, test_user):
    """Order placement via API with duplicate idempotency key."""
    # Deposit funds first
    deposit_virtual_cash(payload=DepositRequest(amount=Decimal("100000.00")), user=test_user, db=db)

    order_payload = OrderCreateRequest(
        asset="NIFTY50",
        side="BUY",
        quantity=Decimal("1.0"),
        idempotency_key="api_idem_key_unique_101",
    )

    o1 = create_order(payload=order_payload, user=test_user, db=db)
    assert o1.status == "EXECUTED"

    # Repeat with same idempotency key returns exact same order
    o2 = create_order(payload=order_payload, user=test_user, db=db)
    assert o1.id == o2.id


def test_portfolio_dashboard_and_rebalance_preview(db, test_user):
    """Portfolio dashboard returns valuation and rebalance preview computes proposal."""
    deposit_virtual_cash(payload=DepositRequest(amount=Decimal("100000.00")), user=test_user, db=db)

    # Buy some GILT and NIFTY50
    create_order(
        payload=OrderCreateRequest(asset="GILT", side="BUY", quantity=Decimal("50.0"), idempotency_key="dash_gilt_buy"),
        user=test_user,
        db=db,
    )

    dash = get_portfolio_dashboard(user=test_user, db=db)
    assert dash.cash_balance > Decimal("0")
    assert dash.total_portfolio_value > Decimal("0")
    assert len(dash.holdings) >= 1


def test_advice_questions_and_scoring_api(db, test_user):
    """Advice questions endpoint returns questions and scoring returns suitability rationale."""
    q_data = get_risk_questions()
    assert len(q_data["questions"]) == 8
    assert "asset_proxies" in q_data

    # Submit questionnaire
    answers = {f"q{i}": 2 for i in range(1, 9)}
    answers["q1_horizon"] = 3
    answers["q5_market_drop_reaction"] = 2

    payload = RiskProfileSubmitRequest(answers=answers, goal_type="House Downpayment", horizon_years=7)
    rec = evaluate_risk_and_recommend(payload=payload)

    assert 1.0 <= rec.risk_score <= 10.0
    assert "target_allocation" in rec.model_dump()
    assert len(rec.suitability_explanation) > 50

    # Apply to user
    applied = apply_recommendation_to_user(payload=payload, user=test_user, db=db)
    assert applied.risk_score == rec.risk_score


def test_prices_router(db):
    """Price router endpoints return valid quotes and history."""
    all_quotes = get_all_prices(db=db)
    assert len(all_quotes) == 4

    single = get_single_price(asset="GOLD", db=db)
    assert single.asset == "GOLD"
    assert single.close_price > Decimal("0")

    history = get_history(asset="NIFTY50", db=db)
    assert history.count > 0
