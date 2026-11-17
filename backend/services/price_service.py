"""
Price Data Service with In-Memory Cache, Live Fetch, SQLite Persistence, and Fallback CSV.
"""

import os
from decimal import Decimal
import csv
import time
from typing import Dict, Any, Optional, List
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..config import FALLBACK_CSV_PATH, PRICE_CACHE_TTL_SECONDS, ASSETS, YFINANCE_TICKERS
from ..models import PriceRecord

# Flag controlling live external requests (disabled by default in test/sandbox to avoid network timeouts)
ALLOW_LIVE_PRICE_FETCH = os.environ.get("HINDSIGHT_LIVE_PRICE_FETCH", "false").lower() in ("true", "1")

# In-memory price cache: {asset: {"price": Decimal, "date": date, "source": str, "ts": float, "is_stale": bool}}
_PRICE_CACHE: Dict[str, Dict[str, Any]] = {}


def load_fallback_csv() -> Dict[str, List[Dict[str, Any]]]:
    """
    Read bundled historical prices CSV.
    Returns: {asset: [{"date": date_obj, "close": Decimal}, ...]}
    """
    data: Dict[str, List[Dict[str, Any]]] = {a: [] for a in ASSETS}
    if not FALLBACK_CSV_PATH.exists():
        return data

    with open(FALLBACK_CSV_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            asset = row["asset"].strip()
            if asset in data:
                try:
                    d = datetime.strptime(row["date"].strip(), "%Y-%m-%d").date()
                    c = Decimal(row["close"].strip())
                    data[asset].append({"date": d, "close": c})
                except Exception:
                    continue

    for a in data:
        data[a].sort(key=lambda x: x["date"])
    return data


def seed_prices_from_csv(db: Session) -> int:
    """
    Seed SQLite prices table from the fallback CSV if empty.
    Returns number of records inserted.
    """
    existing_count = db.query(PriceRecord).count()
    if existing_count > 0:
        return 0

    csv_data = load_fallback_csv()
    records_to_insert = []
    now = datetime.now(timezone.utc)

    for asset, points in csv_data.items():
        for pt in points:
            records_to_insert.append(
                PriceRecord(
                    asset=asset,
                    price_date=pt["date"],
                    close_price=pt["close"],
                    source="fallback",
                    fetched_at=now,
                )
            )

    if records_to_insert:
        db.bulk_save_objects(records_to_insert)
        db.commit()
    return len(records_to_insert)


def _try_fetch_yfinance(asset: str) -> Optional[Decimal]:
    """
    Attempt to fetch real-world quote via yfinance with timeout handling.
    Returns None if network is offline or ticker is not found.
    """
    if not ALLOW_LIVE_PRICE_FETCH:
        return None

    ticker_sym = YFINANCE_TICKERS.get(asset)
    if not ticker_sym:
        return None

    try:
        import yfinance as yf
        t = yf.Ticker(ticker_sym)
        # Fast info check
        fast_info = getattr(t, "fast_info", None)
        if fast_info:
            price = fast_info.last_price
            if price and price > 0:
                return Decimal(str(round(price, 2)))
    except Exception:
        pass
    return None


def get_latest_price(db: Session, asset: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Retrieve the latest price for an asset.

    Resolution hierarchy:
    1. Active in-memory cache (if TTL valid and not force_refresh)
    2. Live market fetch via yfinance
    3. SQLite prices table (seeded historical/latest close)
    4. Bundled fallback CSV file
    """
    now_ts = time.time()
    now_dt = datetime.now(timezone.utc)

    # 1. In-memory cache check
    if not force_refresh and asset in _PRICE_CACHE:
        cached = _PRICE_CACHE[asset]
        if now_ts - cached["cached_at_ts"] < PRICE_CACHE_TTL_SECONDS:
            return {
                "asset": asset,
                "close_price": cached["price"],
                "price_date": cached["date"],
                "source": "cache",
                "is_stale": cached.get("is_stale", False),
                "as_of": cached["as_of"],
            }

    # 2. Try live fetch
    live_price = _try_fetch_yfinance(asset)
    if live_price is not None:
        today = date.today()
        # Save to DB if new
        existing = (
            db.query(PriceRecord)
            .filter(PriceRecord.asset == asset, PriceRecord.price_date == today)
            .first()
        )
        if not existing:
            rec = PriceRecord(
                asset=asset,
                price_date=today,
                close_price=live_price,
                source="live",
                fetched_at=now_dt,
            )
            db.add(rec)
            db.commit()

        quote = {
            "asset": asset,
            "close_price": live_price,
            "price_date": today,
            "source": "live",
            "is_stale": False,
            "as_of": now_dt,
            "cached_at_ts": now_ts,
            "price": live_price,
            "date": today,
        }
        _PRICE_CACHE[asset] = quote
        return quote

    # 3. SQLite price records table
    latest_rec = (
        db.query(PriceRecord)
        .filter(PriceRecord.asset == asset)
        .order_by(desc(PriceRecord.price_date))
        .first()
    )
    if latest_rec:
        price_val = Decimal(str(latest_rec.close_price))
        quote = {
            "asset": asset,
            "close_price": price_val,
            "price_date": latest_rec.price_date,
            "source": "fallback",
            "is_stale": True,  # Using historical close
            "as_of": latest_rec.fetched_at,
            "cached_at_ts": now_ts,
            "price": price_val,
            "date": latest_rec.price_date,
        }
        _PRICE_CACHE[asset] = quote
        return quote

    # 4. Direct CSV fallback
    csv_data = load_fallback_csv()
    asset_points = csv_data.get(asset, [])
    if asset_points:
        latest_pt = asset_points[-1]
        price_val = latest_pt["close"]
        quote = {
            "asset": asset,
            "close_price": price_val,
            "price_date": latest_pt["date"],
            "source": "fallback",
            "is_stale": True,
            "as_of": now_dt,
            "cached_at_ts": now_ts,
            "price": price_val,
            "date": latest_pt["date"],
        }
        _PRICE_CACHE[asset] = quote
        return quote

    # 5. Default baseline safety
    default_prices = {
        "NIFTY50": Decimal("24500.00"),
        "GILT": Decimal("101.20"),
        "GOLD": Decimal("75000.00"),
        "INTLEQ": Decimal("210.50"),
    }
    fallback_val = default_prices.get(asset, Decimal("100.00"))
    quote = {
        "asset": asset,
        "close_price": fallback_val,
        "price_date": date.today(),
        "source": "fallback",
        "is_stale": True,
        "as_of": now_dt,
        "cached_at_ts": now_ts,
        "price": fallback_val,
        "date": date.today(),
    }
    _PRICE_CACHE[asset] = quote
    return quote


def get_price_history(
    db: Session,
    asset: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch price history for an asset from the database.
    """
    query = db.query(PriceRecord).filter(PriceRecord.asset == asset)
    if start_date and isinstance(start_date, date):
        query = query.filter(PriceRecord.price_date >= start_date)
    if end_date and isinstance(end_date, date):
        query = query.filter(PriceRecord.price_date <= end_date)

    records = query.order_by(PriceRecord.price_date.asc()).all()
    return [{"date": r.price_date, "close": Decimal(str(r.close_price))} for r in records]

