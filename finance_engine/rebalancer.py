"""
Portfolio Drift Detection and Rebalancing Engine.
Zero web/framework dependencies. Pure Python.

Implements:
1. Multi-asset drift monitoring against strategic asset allocation targets
2. Tolerance-band trigger logic (default: ±5 percentage points drift)
3. Rebalancing order generation:
   - Evaluates current holdings vs target valuation
   - Sells overweight assets first (generating liquidity)
   - Buys underweight assets second (deploying liquidity)
   - Minimizes turnover and transaction cost drag
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional

DEFAULT_DRIFT_THRESHOLD = 0.05  # 5 percentage points


def compute_drift(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
) -> Dict[str, float]:
    """
    Compute absolute drift for each asset: current_weight - target_weight.
    Returns signed float values (e.g. +0.07 means 7% overweight, -0.04 means 4% underweight).
    """
    all_assets = set(current_weights.keys()).union(set(target_weights.keys()))
    drift: Dict[str, float] = {}
    for asset in all_assets:
        cw = current_weights.get(asset, 0.0)
        tw = target_weights.get(asset, 0.0)
        drift[asset] = round(cw - tw, 4)
    return drift


def needs_rebalance(
    current_weights: Dict[str, float],
    target_weights: Dict[str, float],
    threshold: float = DEFAULT_DRIFT_THRESHOLD,
) -> bool:
    """
    Returns True if any single asset's absolute drift |current - target| >= threshold.
    """
    drift_map = compute_drift(current_weights, target_weights)
    for asset, d in drift_map.items():
        if abs(d) >= threshold:
            return True
    return False


def compute_rebalance_orders(
    current_holdings: Dict[str, Dict[str, Any]],
    target_weights: Dict[str, float],
    total_portfolio_value: float,
    current_prices: Dict[str, float],
    transaction_cost_bps: int = 10,
    slippage_bps: int = 5,
    min_trade_amount: float = 100.0,
) -> Dict[str, Any]:
    """
    Generate executable rebalancing proposals.

    Parameters:
    - current_holdings: {asset: {"quantity": float, "market_value": float}}
    - target_weights: {asset: float (0.0 to 1.0)}
    - total_portfolio_value: total current value across all holdings (+ any investable cash)
    - current_prices: {asset: latest price}
    - transaction_cost_bps: broker/tax cost basis points (default 10 bps = 0.1%)
    - slippage_bps: price slippage basis points (default 5 bps = 0.05%)
    - min_trade_amount: ignore rebalance delta smaller than this to avoid micro-churn

    Returns:
    - proposals: List of proposed order dicts (SELLs first, then BUYs)
    - total_turnover: float
    - estimated_fees: float
    - drift_before: Dict[str, float]
    """
    if total_portfolio_value <= 0:
        return {
            "proposals": [],
            "total_turnover": 0.0,
            "estimated_fees": 0.0,
            "drift_before": {},
        }

    # Calculate current weights
    current_weights: Dict[str, float] = {}
    for asset in target_weights:
        h = current_holdings.get(asset, {})
        mv = float(h.get("market_value", 0.0))
        current_weights[asset] = round(mv / total_portfolio_value, 4)

    drift_before = compute_drift(current_weights, target_weights)

    sell_orders: List[Dict[str, Any]] = []
    buy_orders: List[Dict[str, Any]] = []

    total_turnover = 0.0
    total_fees = 0.0

    for asset, target_w in target_weights.items():
        price = current_prices.get(asset)
        if not price or price <= 0:
            continue

        target_value = total_portfolio_value * target_w
        current_value = float(current_holdings.get(asset, {}).get("market_value", 0.0))
        delta_value = target_value - current_value

        if abs(delta_value) < min_trade_amount:
            continue

        fee_rate = (transaction_cost_bps + slippage_bps) / 10000.0

        if delta_value < 0:
            # Overweight: Sell excess
            sell_amount = abs(delta_value)
            sell_qty = round(sell_amount / price, 4)
            if sell_qty > 0:
                est_fee = round(sell_amount * fee_rate, 2)
                sell_orders.append({
                    "asset": asset,
                    "side": "SELL",
                    "quantity": sell_qty,
                    "estimated_price": round(price, 2),
                    "estimated_gross": round(sell_amount, 2),
                    "estimated_fee": est_fee,
                    "estimated_net": round(sell_amount - est_fee, 2),
                    "reason": f"Harvest profits: Asset is {round(drift_before.get(asset, 0)*100, 1)}% overweight against target allocation.",
                })
                total_turnover += sell_amount
                total_fees += est_fee
        elif delta_value > 0:
            # Underweight: Buy shortfall
            buy_amount = delta_value
            buy_qty = round(buy_amount / price, 4)
            if buy_qty > 0:
                est_fee = round(buy_amount * fee_rate, 2)
                buy_orders.append({
                    "asset": asset,
                    "side": "BUY",
                    "quantity": buy_qty,
                    "estimated_price": round(price, 2),
                    "estimated_gross": round(buy_amount, 2),
                    "estimated_fee": est_fee,
                    "estimated_net": round(buy_amount + est_fee, 2),
                    "reason": f"Replenish position: Asset is {round(abs(drift_before.get(asset, 0))*100, 1)}% underweight against target allocation.",
                })
                total_turnover += buy_amount
                total_fees += est_fee

    # Crucial sequencing: Sell overweight first to liberate cash, then execute buys
    proposals = sell_orders + buy_orders

    return {
        "proposals": proposals,
        "total_turnover": round(total_turnover, 2),
        "estimated_fees": round(total_fees, 2),
        "drift_before": drift_before,
    }
