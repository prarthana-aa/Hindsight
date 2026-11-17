"""
Idempotent Mock Order Execution Engine.

Core Invariants:
1. Idempotency: Duplicate calls with the same idempotency_key return the existing order.
2. Atomic Execution: Wallet debit/credit, holding position updates, and order state transition
   occur in a single transactional unit with row/thread locking.
3. Realistic Market Friction: Applies transaction cost (10 bps) and slippage (5 bps).
4. Strict Asset & Balance Protection: Orders with insufficient funds or insufficient holdings
   fail cleanly without mutating the ledger or holdings.
"""

from decimal import Decimal, ROUND_HALF_UP
import threading
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..config import TRANSACTION_COST_BPS, SLIPPAGE_BPS, ASSETS
from ..models import Order, Holding, AuditLog
from .ledger import debit, credit, get_balance, ledger_lock
from .price_service import get_latest_price

order_execution_lock = threading.RLock()


class OrderExecutionError(Exception):
    """Raised when an order violates market or account rules."""
    pass


def place_order(
    db: Session,
    user_id: str,
    asset: str,
    side: str,
    quantity: Decimal,
    idempotency_key: str,
) -> Order:
    """
    Execute a market order idempotently.

    Parameters:
    - db: SQLAlchemy Session
    - user_id: ID of the ordering user
    - asset: Asset ticker symbol ('NIFTY50', 'GILT', 'GOLD', 'INTLEQ')
    - side: 'BUY' or 'SELL'
    - quantity: Number of units (Decimal > 0)
    - idempotency_key: Client-provided unique request identifier

    Returns:
    - Order record (EXECUTED or FAILED)
    """
    side = side.upper()
    if side not in ("BUY", "SELL"):
        raise OrderExecutionError(f"Invalid order side '{side}'. Must be 'BUY' or 'SELL'.")

    if quantity <= Decimal("0"):
        raise OrderExecutionError(f"Order quantity must be positive, got {quantity}")

    if asset not in ASSETS:
        raise OrderExecutionError(f"Unsupported asset '{asset}'. Supported: {ASSETS}")

    with order_execution_lock:
        # 1. Idempotency Check: return existing order if already processed
        existing_order = (
            db.query(Order)
            .filter(Order.idempotency_key == idempotency_key)
            .first()
        )
        if existing_order:
            return existing_order

        # 2. Fetch latest market price
        price_quote = get_latest_price(db, asset)
        base_price = Decimal(str(price_quote["close_price"]))

        # 3. Calculate slippage and execution price
        slippage_rate = Decimal(str(SLIPPAGE_BPS)) / Decimal("10000")
        if side == "BUY":
            exec_price = (base_price * (Decimal("1") + slippage_rate)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
        else:
            exec_price = (base_price * (Decimal("1") - slippage_rate)).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )

        # 4. Calculate gross amount, transaction cost, and net amount
        gross_amount = (quantity * exec_price).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        fee_rate = Decimal(str(TRANSACTION_COST_BPS)) / Decimal("10000")
        fee = (gross_amount * fee_rate).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        if side == "BUY":
            net_amount = gross_amount + fee
        else:
            net_amount = gross_amount - fee

        # 5. Create pending order row
        now = datetime.now(timezone.utc)
        order = Order(
            user_id=user_id,
            asset=asset,
            side=side,
            quantity=quantity,
            price=exec_price,
            gross_amount=gross_amount,
            transaction_cost=fee,
            net_amount=net_amount,
            status="PENDING",
            idempotency_key=idempotency_key,
            created_at=now,
        )
        db.add(order)
        db.flush()  # Generate order.id

        # 6. Validate balance or holdings and execute
        try:
            holding = (
                db.query(Holding)
                .filter(Holding.user_id == user_id, Holding.asset == asset)
                .first()
            )

            if side == "BUY":
                current_cash = get_balance(db, user_id)
                if current_cash < net_amount:
                    order.status = "FAILED"
                    order.failure_reason = (
                        f"Insufficient wallet funds. Required ₹{net_amount:.2f}, available ₹{current_cash:.2f}"
                    )
                    db.commit()
                    return order

                # Debit wallet
                debit(
                    db=db,
                    user_id=user_id,
                    amount=net_amount,
                    memo=f"Market BUY {quantity} {asset} @ ₹{exec_price:.2f}",
                    reference_id=order.id,
                )

                # Update holdings
                if not holding:
                    holding = Holding(
                        user_id=user_id,
                        asset=asset,
                        quantity=quantity,
                        avg_cost=exec_price,
                        last_updated=now,
                    )
                    db.add(holding)
                else:
                    old_qty = Decimal(str(holding.quantity))
                    old_cost = Decimal(str(holding.avg_cost))
                    new_qty = old_qty + quantity
                    # Weighted-average cost basis
                    new_avg = ((old_qty * old_cost) + (quantity * exec_price)) / new_qty
                    holding.quantity = new_qty
                    holding.avg_cost = new_avg.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                    holding.last_updated = now

            elif side == "SELL":
                held_qty = Decimal(str(holding.quantity)) if holding else Decimal("0")
                if held_qty < quantity:
                    order.status = "FAILED"
                    order.failure_reason = (
                        f"Insufficient asset holdings. Attempted to sell {quantity} {asset}, but only held {held_qty}"
                    )
                    db.commit()
                    return order

                # Credit wallet
                credit(
                    db=db,
                    user_id=user_id,
                    amount=net_amount,
                    memo=f"Market SELL {quantity} {asset} @ ₹{exec_price:.2f}",
                    reference_id=order.id,
                )

                # Update holdings
                new_qty = held_qty - quantity
                holding.quantity = new_qty
                if new_qty == Decimal("0"):
                    holding.avg_cost = Decimal("0.0000")
                holding.last_updated = now

            # 7. Mark order EXECUTED
            order.status = "EXECUTED"
            order.executed_at = datetime.now(timezone.utc)

            # 8. Record in audit log
            audit = AuditLog(
                user_id=user_id,
                event_type="ORDER_EXECUTED",
                event_data={
                    "order_id": order.id,
                    "asset": asset,
                    "side": side,
                    "quantity": float(quantity),
                    "price": float(exec_price),
                    "net_amount": float(net_amount),
                    "fee": float(fee),
                    "idempotency_key": idempotency_key,
                },
                rule_version="order_v1.0",
                created_at=datetime.now(timezone.utc),
            )
            db.add(audit)
            db.commit()
            return order

        except Exception as e:
            db.rollback()
            # In case of unhandled error, ensure order is logged as failed
            order.status = "FAILED"
            order.failure_reason = f"Execution error: {str(e)}"
            db.add(order)
            db.commit()
            return order

