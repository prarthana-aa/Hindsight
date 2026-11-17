"""
Portfolio and Order Management Router.
Handles market order placement, dashboard valuation, P&L, holdings, and rebalancing execution.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, Order, Holding, Portfolio, AuditLog
from ..auth import get_current_user
from ..schemas import (
    OrderCreateRequest,
    OrderResponse,
    PortfolioDashboardResponse,
    HoldingResponse,
)
from ..services.ledger import get_balance
from ..services.order_executor import place_order, OrderExecutionError
from ..services.price_service import get_latest_price
from finance_engine.rebalancer import (
    compute_drift,
    needs_rebalance,
    compute_rebalance_orders,
)

router = APIRouter(prefix="/portfolio", tags=["Portfolio & Orders"])


@router.post("/order", response_model=OrderResponse)
def create_order(
    payload: OrderCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute a market order (BUY or SELL) with strict idempotency protection.
    """
    try:
        order = place_order(
            db=db,
            user_id=user.id,
            asset=payload.asset.upper(),
            side=payload.side.upper(),
            quantity=payload.quantity,
            idempotency_key=payload.idempotency_key,
        )
        return OrderResponse.model_validate(order)
    except OrderExecutionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/orders", response_model=List[OrderResponse])
def get_user_orders(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get all past orders for the authenticated user.
    """
    orders = (
        db.query(Order)
        .filter(Order.user_id == user.id)
        .order_by(Order.created_at.desc())
        .all()
    )
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/dashboard", response_model=PortfolioDashboardResponse)
def get_portfolio_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return comprehensive portfolio valuation, cash balance, holdings, unrealized P&L,
    target allocation weights, and drift status.
    """
    cash_balance = get_balance(db, user.id)

    raw_holdings = (
        db.query(Holding)
        .filter(Holding.user_id == user.id, Holding.quantity > 0)
        .all()
    )

    holdings_responses: List[HoldingResponse] = []
    invested_value = Decimal("0.0000")
    total_cost_basis = Decimal("0.0000")

    holding_market_values: Dict[str, Decimal] = {}

    for h in raw_holdings:
        qty = Decimal(str(h.quantity))
        avg_cost = Decimal(str(h.avg_cost))
        quote = get_latest_price(db, h.asset)
        cur_price = Decimal(str(quote["close_price"]))

        mv = (qty * cur_price).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        cost_basis = (qty * avg_cost).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        unrealized = mv - cost_basis
        unrealized_pct = (
            ((unrealized / cost_basis) * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            if cost_basis > Decimal("0")
            else Decimal("0.00")
        )

        invested_value += mv
        total_cost_basis += cost_basis
        holding_market_values[h.asset] = mv

        holdings_responses.append(
            HoldingResponse(
                asset=h.asset,
                quantity=qty,
                avg_cost=avg_cost,
                current_price=cur_price,
                market_value=mv,
                unrealized_pnl=unrealized,
                unrealized_pnl_pct=unrealized_pct,
                current_weight=Decimal("0.0000"),  # updated below
            )
        )

    total_portfolio_value = cash_balance + invested_value
    total_unrealized_pnl = invested_value - total_cost_basis
    total_pnl_pct = (
        ((total_unrealized_pnl / total_cost_basis) * Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if total_cost_basis > Decimal("0")
        else Decimal("0.00")
    )

    # Compute actual weights
    current_weights_float: Dict[str, float] = {}
    for hr in holdings_responses:
        if total_portfolio_value > Decimal("0"):
            weight = (hr.market_value / total_portfolio_value).quantize(
                Decimal("0.0001"), rounding=ROUND_HALF_UP
            )
            hr.current_weight = weight
            current_weights_float[hr.asset] = float(weight)
        else:
            hr.current_weight = Decimal("0.0000")
            current_weights_float[hr.asset] = 0.0

    # Fetch user's target allocation if defined
    user_portfolio = (
        db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    )
    target_alloc = user_portfolio.target_allocation if user_portfolio else None

    drift_map: Optional[Dict[str, float]] = None
    rebalance_flag = False

    if target_alloc:
        drift_map = compute_drift(current_weights_float, target_alloc)
        rebalance_flag = needs_rebalance(current_weights_float, target_alloc)

    return PortfolioDashboardResponse(
        user_id=user.id,
        cash_balance=cash_balance,
        invested_value=invested_value,
        total_portfolio_value=total_portfolio_value,
        total_unrealized_pnl=total_unrealized_pnl,
        total_pnl_pct=total_pnl_pct,
        holdings=holdings_responses,
        target_allocation=target_alloc,
        drift_status=drift_map,
        needs_rebalance=rebalance_flag,
    )


@router.post("/rebalance/preview")
def preview_rebalance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compute proposed rebalancing orders using the finance engine.
    Does not execute trades.
    """
    user_portfolio = (
        db.query(Portfolio).filter(Portfolio.user_id == user.id).first()
    )
    if not user_portfolio or not user_portfolio.target_allocation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active target allocation portfolio set up.",
        )

    target_weights = user_portfolio.target_allocation

    raw_holdings = (
        db.query(Holding)
        .filter(Holding.user_id == user.id)
        .all()
    )

    current_prices: Dict[str, float] = {}
    current_holdings_dict: Dict[str, Dict[str, Any]] = {}
    invested_val = 0.0

    for asset in target_weights:
        quote = get_latest_price(db, asset)
        price_f = float(quote["close_price"])
        current_prices[asset] = price_f

        h = next((x for x in raw_holdings if x.asset == asset), None)
        qty_f = float(h.quantity) if h else 0.0
        mv_f = qty_f * price_f
        invested_val += mv_f
        current_holdings_dict[asset] = {"quantity": qty_f, "market_value": mv_f}

    cash_val = float(get_balance(db, user.id))
    total_val = cash_val + invested_val

    plan = compute_rebalance_orders(
        current_holdings=current_holdings_dict,
        target_weights=target_weights,
        total_portfolio_value=total_val,
        current_prices=current_prices,
    )

    return {
        "user_id": user.id,
        "total_portfolio_value": round(total_val, 2),
        "target_weights": target_weights,
        "rebalance_plan": plan,
    }


@router.post("/rebalance/execute")
def execute_rebalance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Explicit user approval to execute the proposed rebalancing orders.
    Executes SELLs first to release liquidity, then executes BUYs.
    """
    preview = preview_rebalance(user=user, db=db)
    proposals = preview["rebalance_plan"]["proposals"]

    if not proposals:
        return {"status": "NOOP", "message": "Portfolio is already balanced.", "orders": []}

    executed_orders = []
    now_str = str(int(Decimal(preview["total_portfolio_value"])))

    for idx, prop in enumerate(proposals):
        key = f"rebal_{user.id}_{prop['asset']}_{prop['side']}_{now_str}_{idx}"
        order = place_order(
            db=db,
            user_id=user.id,
            asset=prop["asset"],
            side=prop["side"],
            quantity=Decimal(str(prop["quantity"])),
            idempotency_key=key,
        )
        executed_orders.append(OrderResponse.model_validate(order))

    return {
        "status": "COMPLETED",
        "message": f"Successfully processed {len(executed_orders)} rebalance orders.",
        "orders": executed_orders,
    }
