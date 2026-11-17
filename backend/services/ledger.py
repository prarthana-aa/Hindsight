"""
Double-Entry Style Wallet Ledger Service.

Financial Ledger Principles:
1. Append-Only: No UPDATE or DELETE statements are ever executed on WalletLedger.
2. Invariant: Running balance is guaranteed >= 0 at all times.
3. Strict Reconciliation: Recomputed sum(CREDIT) - sum(DEBIT) must exactly equal running_balance.
4. Concurrency Safe: Uses reentrant threading lock for atomic SQLite serialization.
5. All calculations use Decimal for exact financial precision without float drift.
"""

from decimal import Decimal
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models import WalletLedger

# Thread lock for SQLite atomic serialization
ledger_lock = threading.RLock()


class InsufficientFundsError(Exception):
    """Raised when an operation would drive the wallet balance below zero."""
    pass


class InvalidAmountError(Exception):
    """Raised when an invalid or non-positive amount is supplied."""
    pass


def get_balance(db: Session, user_id: str) -> Decimal:
    """
    Get the latest running balance for a user.
    Reads the most recent ledger row running_balance.
    Returns Decimal("0.0000") if user has no ledger entries.
    """
    with ledger_lock:
        latest_entry = (
            db.query(WalletLedger)
            .filter(WalletLedger.user_id == user_id)
            .order_by(desc(WalletLedger.seq))
            .first()
        )
        if not latest_entry:
            return Decimal("0.0000")
        return Decimal(str(latest_entry.running_balance))


def credit(
    db: Session,
    user_id: str,
    amount: Decimal,
    memo: str,
    reference_id: Optional[str] = None,
) -> WalletLedger:
    """
    Credit the user's virtual wallet.
    Increases running balance by amount.

    Appends an immutable CREDIT entry.
    """
    if amount <= Decimal("0"):
        raise InvalidAmountError(f"Credit amount must be positive, got {amount}")

    with ledger_lock:
        current_bal = get_balance(db, user_id)
        new_balance = current_bal + Decimal(str(amount))

        entry = WalletLedger(
            user_id=user_id,
            entry_type="CREDIT",
            amount=Decimal(str(amount)),
            running_balance=new_balance,
            reference_id=reference_id,
            memo=memo,
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.flush()
        return entry


def debit(
    db: Session,
    user_id: str,
    amount: Decimal,
    memo: str,
    reference_id: Optional[str] = None,
) -> WalletLedger:
    """
    Debit the user's virtual wallet.
    Decreases running balance by amount.

    Raises InsufficientFundsError if current_balance < amount.
    Appends an immutable DEBIT entry.
    """
    if amount <= Decimal("0"):
        raise InvalidAmountError(f"Debit amount must be positive, got {amount}")

    with ledger_lock:
        current_bal = get_balance(db, user_id)
        amount_dec = Decimal(str(amount))

        if current_bal < amount_dec:
            raise InsufficientFundsError(
                f"Insufficient funds: Available balance ₹{current_bal:.2f}, attempted debit ₹{amount_dec:.2f}"
            )

        new_balance = current_bal - amount_dec

        entry = WalletLedger(
            user_id=user_id,
            entry_type="DEBIT",
            amount=amount_dec,
            running_balance=new_balance,
            reference_id=reference_id,
            memo=memo,
            created_at=datetime.now(timezone.utc),
        )
        db.add(entry)
        db.flush()
        return entry


def get_ledger_history(
    db: Session,
    user_id: str,
    limit: int = 50,
    offset: int = 0,
) -> List[WalletLedger]:
    """
    Fetch paginated ledger entries in reverse chronological order.
    """
    return (
        db.query(WalletLedger)
        .filter(WalletLedger.user_id == user_id)
        .order_by(desc(WalletLedger.seq))
        .offset(offset)
        .limit(limit)
        .all()
    )


def reconcile(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Perform audit reconciliation for a user's wallet.
    Calculates:
      sum_credits = sum of all CREDIT rows
      sum_debits = sum of all DEBIT rows
      computed_balance = sum_credits - sum_debits
      latest_running_balance = running_balance on the most recent ledger entry

    Asserts computed_balance == latest_running_balance.
    Returns audit report dictionary.
    """
    with ledger_lock:
        entries = (
            db.query(WalletLedger)
            .filter(WalletLedger.user_id == user_id)
            .order_by(WalletLedger.seq.asc())
            .all()
        )

        sum_credits = Decimal("0.0000")
        sum_debits = Decimal("0.0000")
        running_verification = Decimal("0.0000")
        internal_step_error = False

        for e in entries:
            amt = Decimal(str(e.amount))
            if e.entry_type == "CREDIT":
                sum_credits += amt
                running_verification += amt
            elif e.entry_type == "DEBIT":
                sum_debits += amt
                running_verification -= amt

            # Check that each step's recorded running_balance matched the reconstructed state
            if Decimal(str(e.running_balance)) != running_verification:
                internal_step_error = True

        computed_balance = sum_credits - sum_debits
        latest_running = get_balance(db, user_id)
        discrepancy = computed_balance - latest_running

        is_reconciled = (discrepancy == Decimal("0.0000")) and not internal_step_error

        return {
            "user_id": user_id,
            "is_reconciled": is_reconciled,
            "ledger_count": len(entries),
            "sum_credits": sum_credits,
            "sum_debits": sum_debits,
            "computed_balance": computed_balance,
            "latest_running_balance": latest_running,
            "discrepancy": discrepancy,
            "status": "BALANCED_AUDIT_VERIFIED" if is_reconciled else "DISCREPANCY_DETECTED",
            "checked_at": datetime.now(timezone.utc),
        }

