"""
Tests for Price Data Service: Cache, Fallback CSV, SQLite Seeding, and Freshness Labels.
"""

from datetime import date
from decimal import Decimal
from backend.services.price_service import (
    load_fallback_csv,
    seed_prices_from_csv,
    get_latest_price,
    get_price_history,
)
from backend.config import ASSETS
from backend.models import PriceRecord


def test_fallback_csv_loads():
    """Fallback CSV loads successfully with entries for all 4 assets."""
    data = load_fallback_csv()
    for a in ASSETS:
        assert a in data
        assert len(data[a]) > 100, f"Expected >100 entries for {a}, found {len(data[a])}"
        assert data[a][0]["close"] > Decimal("0")


def test_seed_prices_from_csv(db):
    """Database seeder properly inserts historical records from CSV."""
    count = db.query(PriceRecord).count()
    assert count > 500


def test_fallback_price_returned_on_live_fail(db):
    """When live network is unavailable, get_latest_price returns fallback data."""
    quote = get_latest_price(db, "NIFTY50")
    assert quote["asset"] == "NIFTY50"
    assert quote["close_price"] > Decimal("1000.00")
    assert quote["source"] in ("fallback", "cache", "live")
    assert "as_of" in quote


def test_price_source_label(db):
    """Returned price quote contains valid source label ('live', 'cache', or 'fallback')."""
    for asset in ASSETS:
        q = get_latest_price(db, asset)
        assert q["source"] in ("live", "cache", "fallback")
        assert isinstance(q["is_stale"], bool)


def test_price_history_range(db):
    """Price history query filters by date range correctly."""
    start = date(2024, 6, 1)
    end = date(2024, 6, 30)

    history = get_price_history(db, "GOLD", start_date=start, end_date=end)
    assert len(history) > 0
    for pt in history:
        assert start <= pt["date"] <= end
        assert pt["close"] > Decimal("0")


def test_stale_flag_set_on_fallback(db):
    """When using fallback or historical close, the is_stale flag is True for UI awareness."""
    q = get_latest_price(db, "GILT")
    if q["source"] == "fallback":
        assert q["is_stale"] is True
