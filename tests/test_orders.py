"""
Tests for Idempotent Order Execution Engine, Slippage, Cost Calculation, and Holding Accounting.
"""

from decimal import Decimal
import pytest
from backend.services.ledger import credit, get_balance
from backend.services.order_executor import place_order, OrderExecutionError
from backend.models import Order, Holding, AuditLog
from backend.models import User
from backend.auth import hash_password
from datetime import datetime, timezone
from backend.config import TRANSACTION_COST_BPS, SLIPPAGE_BPS


def test_idempotent_buy_same_key(db, test_user):
    """Submitting the same idempotency_key twice executes only once and returns the exact same order."""
    credit(db, test_user.id, Decimal("50000.00"), memo="Initial funds")
    key = "idem_key_test_001"

    order1 = place_order(
        db=db,
        user_id=test_user.id,
        asset="NIFTY50",
        side="BUY",
        quantity=Decimal("1.0"),
        idempotency_key=key,
    )
    assert order1.status == "EXECUTED"

    order2 = place_order(
        db=db,
        user_id=test_user.id,
        asset="NIFTY50",
        side="BUY",
        quantity=Decimal("1.0"),
        idempotency_key=key,
    )
    # Must be exact same order ID
    assert order1.id == order2.id
    assert order1.executed_at == order2.executed_at

    # Check total orders in database is exactly 1
    total_orders = db.query(Order).filter(Order.idempotency_key == key).count()
    assert total_orders == 1


def test_idempotency_key_cannot_cross_accounts(db, test_user):
    """A key used by one account cannot return or mutate that account's order."""
    other_user = User(
        email="otherinvestor@hindsight.app",
        hashed_password=hash_password("OtherSecret123"),
        full_name="Other Investor",
        consent_ts=datetime.now(timezone.utc),
        is_demo=False,
    )
    db.add(other_user)
    db.commit()

    credit(db, test_user.id, Decimal("50000.00"), memo="Initial funds")
    credit(db, other_user.id, Decimal("50000.00"), memo="Initial funds")
    key = "cross_account_key_001"

    place_order(
        db=db,
        user_id=test_user.id,
        asset="NIFTY50",
        side="BUY",
        quantity=Decimal("1.0"),
        idempotency_key=key,
    )

    with pytest.raises(OrderExecutionError, match="another account"):
        place_order(
            db=db,
            user_id=other_user.id,
            asset="NIFTY50",
            side="BUY",
            quantity=Decimal("1.0"),
            idempotency_key=key,
        )


def test_buy_debits_wallet(db, test_user):
    """After BUY, wallet balance is reduced by exact net_amount (gross + fee)."""
    initial_cash = Decimal("100000.00")
    credit(db, test_user.id, initial_cash, memo="Cash buffer")

    order = place_order(
        db=db,
        user_id=test_user.id,
        asset="GILT",
        side="BUY",
        quantity=Decimal("10.0"),
        idempotency_key="buy_debit_key_002",
    )
    assert order.status == "EXECUTED"

    new_cash = get_balance(db, test_user.id)
    assert new_cash == initial_cash - order.net_amount
    assert order.net_amount == order.gross_amount + order.transaction_cost


def test_buy_credits_holdings(db, test_user):
    """After BUY, holdings quantity increases by order quantity."""
    credit(db, test_user.id, Decimal("50000.00"), memo="Cash")

    place_order(
        db=db,
        user_id=test_user.id,
        asset="GILT",
        side="BUY",
        quantity=Decimal("50.0"),
        idempotency_key="holdings_credit_key_003",
    )

    holding = db.query(Holding).filter(Holding.user_id == test_user.id, Holding.asset == "GILT").first()
    assert holding is not None
    assert holding.quantity == Decimal("50.0")
    assert holding.avg_cost > Decimal("0.0")


def test_buy_avg_cost_weighted(db, test_user):
    """Multiple buys calculate the exact weighted average cost basis."""
    credit(db, test_user.id, Decimal("100000.00"), memo="Cash")

    order1 = place_order(
        db=db,
        user_id=test_user.id,
        asset="INTLEQ",
        side="BUY",
        quantity=Decimal("10.0"),
        idempotency_key="avg_cost_key_1",
    )
    order2 = place_order(
        db=db,
        user_id=test_user.id,
        asset="INTLEQ",
        side="BUY",
        quantity=Decimal("20.0"),
        idempotency_key="avg_cost_key_2",
    )

    holding = db.query(Holding).filter(Holding.user_id == test_user.id, Holding.asset == "INTLEQ").first()
    assert holding.quantity == Decimal("30.0")

    # Expected weighted avg: (10 * p1 + 20 * p2) / 30
    expected_avg = ((Decimal("10.0") * order1.price) + (Decimal("20.0") * order2.price)) / Decimal("30.0")
    assert abs(holding.avg_cost - expected_avg) < Decimal("0.001")


def test_sell_credits_wallet(db, test_user):
    """After SELL, wallet is credited by net_amount (gross - fee)."""
    credit(db, test_user.id, Decimal("50000.00"), memo="Cash")
    # Buy first
    place_order(
        db=db,
        user_id=test_user.id,
        asset="GOLD",
        side="BUY",
        quantity=Decimal("0.20"),
        idempotency_key="sell_credit_setup",
    )
    cash_after_buy = get_balance(db, test_user.id)

    # Now sell
    sell_order = place_order(
        db=db,
        user_id=test_user.id,
        asset="GOLD",
        side="SELL",
        quantity=Decimal("0.10"),
        idempotency_key="sell_credit_action",
    )
    assert sell_order.status == "EXECUTED"

    cash_after_sell = get_balance(db, test_user.id)
    assert cash_after_sell == cash_after_buy + sell_order.net_amount
    assert sell_order.net_amount == sell_order.gross_amount - sell_order.transaction_cost


def test_sell_debits_holdings(db, test_user):
    """Selling decrements the holdings quantity."""
    credit(db, test_user.id, Decimal("50000.00"), memo="Cash")
    place_order(
        db=db,
        user_id=test_user.id,
        asset="GILT",
        side="BUY",
        quantity=Decimal("100.0"),
        idempotency_key="sell_debit_setup",
    )

    place_order(
        db=db,
        user_id=test_user.id,
        asset="GILT",
        side="SELL",
        quantity=Decimal("40.0"),
        idempotency_key="sell_debit_action",
    )

    holding = db.query(Holding).filter(Holding.user_id == test_user.id, Holding.asset == "GILT").first()
    assert holding.quantity == Decimal("60.0")


def test_buy_insufficient_funds_fails(db, test_user):
    """Buy with insufficient wallet balance transitions to status=FAILED without changing balance."""
    # User has 0 balance
    initial_bal = get_balance(db, test_user.id)
    assert initial_bal == Decimal("0.0000")

    order = place_order(
        db=db,
        user_id=test_user.id,
        asset="NIFTY50",
        side="BUY",
        quantity=Decimal("1.0"),
        idempotency_key="insufficient_funds_key",
    )
    assert order.status == "FAILED"
    assert "Insufficient wallet funds" in order.failure_reason

    # Balance remains 0
    assert get_balance(db, test_user.id) == initial_bal

    # Holdings were NOT created
    holding = db.query(Holding).filter(Holding.user_id == test_user.id, Holding.asset == "NIFTY50").first()
    assert holding is None


def test_sell_more_than_holdings_fails(db, test_user):
    """Sell order with quantity exceeding held amount fails cleanly."""
    credit(db, test_user.id, Decimal("50000.00"), memo="Cash")
    place_order(
        db=db,
        user_id=test_user.id,
        asset="GOLD",
        side="BUY",
        quantity=Decimal("0.05"),
        idempotency_key="short_sell_setup",
    )

    cash_before_sell = get_balance(db, test_user.id)

    # Attempt to sell 0.20 when holding only 0.05
    sell_order = place_order(
        db=db,
        user_id=test_user.id,
        asset="GOLD",
        side="SELL",
        quantity=Decimal("0.20"),
        idempotency_key="short_sell_illegal",
    )
    assert sell_order.status == "FAILED"
    assert "Insufficient asset holdings" in sell_order.failure_reason

    # Cash and holdings unchanged
    assert get_balance(db, test_user.id) == cash_before_sell
    holding = db.query(Holding).filter(Holding.user_id == test_user.id, Holding.asset == "GOLD").first()
    assert holding.quantity == Decimal("0.05")


def test_transaction_cost_applied(db, test_user):
    """Verify transaction cost corresponds to TRANSACTION_COST_BPS (10 bps = 0.1%)."""
    credit(db, test_user.id, Decimal("50000.00"), memo="Cash")
    order = place_order(
        db=db,
        user_id=test_user.id,
        asset="GILT",
        side="BUY",
        quantity=Decimal("100.0"),
        idempotency_key="tx_fee_test_key",
    )
    expected_fee = (order.gross_amount * Decimal(str(TRANSACTION_COST_BPS))) / Decimal("10000")
    assert abs(order.transaction_cost - expected_fee) <= Decimal("0.01")


def test_order_audit_log_written(db, test_user):
    """Executed orders create a corresponding immutable AuditLog entry."""
    credit(db, test_user.id, Decimal("50000.00"), memo="Cash")
    key = "audit_log_test_key_009"
    order = place_order(
        db=db,
        user_id=test_user.id,
        asset="INTLEQ",
        side="BUY",
        quantity=Decimal("5.0"),
        idempotency_key=key,
    )
    assert order.status == "EXECUTED"

    audit = (
        db.query(AuditLog)
        .filter(AuditLog.user_id == test_user.id, AuditLog.event_type == "ORDER_EXECUTED")
        .first()
    )
    assert audit is not None
    assert audit.event_data["order_id"] == order.id
    assert audit.event_data["idempotency_key"] == key
