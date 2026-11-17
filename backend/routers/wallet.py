"""
Wallet and Ledger Router.
Exposes endpoints for virtual deposits, balance queries, audit reconciliation,
and paginated ledger inspection.
"""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..schemas import (
    DepositRequest,
    WalletBalanceResponse,
    LedgerEntryResponse,
    ReconciliationReport,
)
from ..services.ledger import (
    credit,
    get_balance,
    get_ledger_history,
    reconcile,
    InvalidAmountError,
)

router = APIRouter(prefix="/wallet", tags=["Wallet & Ledger"])


@router.post("/deposit", response_model=LedgerEntryResponse)
def deposit_virtual_cash(
    payload: DepositRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deposit virtual INR into the user's wallet.
    Appends an immutable CREDIT row to the double-entry wallet ledger.
    """
    try:
        entry = credit(
            db=db,
            user_id=user.id,
            amount=payload.amount,
            memo=payload.memo or "Virtual Cash Deposit",
            reference_id=f"DEP-{int(Decimal(payload.amount))}",
        )
        db.commit()
        db.refresh(entry)
        return entry
    except InvalidAmountError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/balance", response_model=WalletBalanceResponse)
def get_wallet_balance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the user's current running wallet balance and recent ledger movements.
    """
    bal = get_balance(db, user.id)
    recent_entries = get_ledger_history(db, user.id, limit=10, offset=0)

    last_ts = recent_entries[0].created_at if recent_entries else None

    return WalletBalanceResponse(
        user_id=user.id,
        current_balance=bal,
        currency="INR",
        last_updated=last_ts,
        recent_transactions=[LedgerEntryResponse.model_validate(e) for e in recent_entries],
    )


@router.get("/ledger", response_model=List[LedgerEntryResponse])
def get_full_ledger(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get paginated append-only double-entry ledger history for the authenticated user.
    """
    entries = get_ledger_history(db, user.id, limit=limit, offset=offset)
    return [LedgerEntryResponse.model_validate(e) for e in entries]


@router.get("/reconcile", response_model=ReconciliationReport)
def run_ledger_reconciliation(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Execute mathematical ledger audit reconciliation.
    Reconstructs sum(credits) - sum(debits) and verifies that every historical step
    matches the ledger's recorded running balance with 0.00 discrepancy.
    """
    report = reconcile(db, user.id)
    return ReconciliationReport(
        user_id=report["user_id"],
        is_reconciled=report["is_reconciled"],
        ledger_count=report["ledger_count"],
        sum_credits=report["sum_credits"],
        sum_debits=report["sum_debits"],
        computed_balance=report["computed_balance"],
        latest_running_balance=report["latest_running_balance"],
        discrepancy=report["discrepancy"],
        status=report["status"],
        checked_at=report["checked_at"],
    )

