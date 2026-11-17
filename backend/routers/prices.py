"""
Prices and Market Data Router.
Provides real-time quotes, fallback data, and historical prices for backtesting.
"""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..config import ASSETS
from ..schemas import PriceQuote, PriceHistoryResponse, PriceHistoryItem
from ..services.price_service import get_latest_price, get_price_history

router = APIRouter(prefix="/prices", tags=["Prices & Market Data"])


@router.get("/", response_model=List[PriceQuote])
def get_all_prices(db: Session = Depends(get_db)):
    """
    Get latest prices for all 4 core proxy assets (NIFTY50, GILT, GOLD, INTLEQ).
    """
    quotes = []
    for asset in ASSETS:
        q = get_latest_price(db, asset)
        quotes.append(PriceQuote(**q))
    return quotes


@router.get("/{asset}", response_model=PriceQuote)
def get_single_price(asset: str, db: Session = Depends(get_db)):
    """
    Get latest quote for a specific asset with data source and freshness label.
    """
    asset_upper = asset.upper()
    if asset_upper not in ASSETS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset}' is not tracked. Tracked assets: {ASSETS}",
        )
    q = get_latest_price(db, asset_upper)
    return PriceQuote(**q)


@router.get("/{asset}/history", response_model=PriceHistoryResponse)
def get_history(
    asset: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Get historical daily close prices for an asset.
    """
    asset_upper = asset.upper()
    if asset_upper not in ASSETS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset}' is not tracked. Tracked assets: {ASSETS}",
        )

    history = get_price_history(db, asset_upper, start_date=start_date, end_date=end_date)
    return PriceHistoryResponse(
        asset=asset_upper,
        count=len(history),
        data=[PriceHistoryItem(date=h["date"], close=h["close"]) for h in history],
    )


@router.post("/refresh", response_model=List[PriceQuote])
def force_refresh_prices(db: Session = Depends(get_db)):
    """
    Force a cache refresh and attempt live fetch for all assets.
    """
    quotes = []
    for asset in ASSETS:
        q = get_latest_price(db, asset, force_refresh=True)
        quotes.append(PriceQuote(**q))
    return quotes

