"""
Comprehensive Tests for Double-Entry Wallet Ledger and Reconciliation.

Proves:
- The wallet ledger always reconciles across arbitrary interleaved credits and debits.
- Running balance is strictly non-negative at all times.
- Decimal precision prevents rounding errors.
- Thread-safe concurrency.
- Append-only immutability.
"""

from decimal import Decimal
import random
import threading
import pytest
from backend.services.ledger import (
    credit,
    debit,
    get_balance,
    reconcile,
    get_ledger_history,
    InsufficientFundsError,
    InvalidAmountError,
)
from backend.models import User, WalletLedger
from backend.auth import hash_password


def test_credit_increases_balance(db, test_user):
    """Credit 1000 -> balance == 1000"""
    initial_bal = get_balance(db, test_user.id)
    assert initial_bal == Decimal("0.0000")

    entry = credit(db, test_user.id, Decimal("1000.00"), memo="Deposit 1")
    assert entry.entry_type == "CREDIT"
    assert entry.amount == Decimal("1000.00")
    assert entry.running_balance == Decimal("1000.00")

    bal = get_balance(db, test_user.id)
    assert bal == Decimal("1000.00")


def test_debit_decreases_balance(db, test_user):
    """Credit 1000, debit 500 -> balance == 500"""
    credit(db, test_user.id, Decimal("1000.00"), memo="Deposit")
    entry = debit(db, test_user.id, Decimal("500.00"), memo="Withdrawal")

    assert entry.entry_type == "DEBIT"
    assert entry.amount == Decimal("500.00")
    assert entry.running_balance == Decimal("500.00")

    bal = get_balance(db, test_user.id)
    assert bal == Decimal("500.00")


def test_debit_insufficient_funds_raises(db, test_user):
    """Credit 100, debit 200 -> raises InsufficientFundsError, balance remains 100"""
    credit(db, test_user.id, Decimal("100.00"), memo="Deposit")
    with pytest.raises(InsufficientFundsError):
        debit(db, test_user.id, Decimal("200.00"), memo="Overdraft Attempt")

    bal = get_balance(db, test_user.id)
    assert bal == Decimal("100.00")


def test_zero_balance_debit_raises(db, test_user):
    """Debit on fresh account raises InsufficientFundsError"""
    with pytest.raises(InsufficientFundsError):
        debit(db, test_user.id, Decimal("50.00"), memo="Illegal Debit")


def test_exact_balance_debit_succeeds(db, test_user):
    """Credit 500, debit 500 -> balance == 0"""
    credit(db, test_user.id, Decimal("500.00"), memo="Deposit")
    debit(db, test_user.id, Decimal("500.00"), memo="Full withdrawal")
    bal = get_balance(db, test_user.id)
    assert bal == Decimal("0.0000")

    audit = reconcile(db, test_user.id)
    assert audit["is_reconciled"] is True
    assert audit["latest_running_balance"] == Decimal("0.0000")


def test_running_balance_matches_sum(db, test_user):
    """After 10 random credits and debits, running_balance strictly matches sum(credits) - sum(debits)"""
    random.seed(123)
    current_expected = Decimal("0.00")

    for i in range(10):
        # 70% chance credit, 30% chance debit (if funds available)
        if random.random() < 0.7 or current_expected < Decimal("100.00"):
            amt = Decimal(str(random.randint(100, 1000)))
            credit(db, test_user.id, amt, memo=f"Credit {i}")
            current_expected += amt
        else:
            amt = Decimal(str(random.randint(50, int(current_expected))))
            debit(db, test_user.id, amt, memo=f"Debit {i}")
            current_expected -= amt

        audit = reconcile(db, test_user.id)
        assert audit["is_reconciled"] is True
        assert audit["latest_running_balance"] == current_expected


def test_multiple_credits_reconcile(db, test_user):
    """5 credits of varying amounts reconcile"""
    amounts = [Decimal("100.50"), Decimal("250.75"), Decimal("999.99"), Decimal("40.00"), Decimal("1500.25")]
    for a in amounts:
        credit(db, test_user.id, a, memo="Credit step")

    audit = reconcile(db, test_user.id)
    assert audit["is_reconciled"] is True
    assert audit["sum_credits"] == sum(amounts)
    assert audit["sum_debits"] == Decimal("0.00")
    assert audit["computed_balance"] == sum(amounts)


def test_interleaved_operations_reconcile(db, test_user):
    """Credit 5000, debit 1200, credit 800, debit 300; reconcile"""
    credit(db, test_user.id, Decimal("5000.00"), memo="C1")
    debit(db, test_user.id, Decimal("1200.00"), memo="D1")
    credit(db, test_user.id, Decimal("800.00"), memo="C2")
    debit(db, test_user.id, Decimal("300.00"), memo="D2")

    audit = reconcile(db, test_user.id)
    assert audit["is_reconciled"] is True
    assert audit["computed_balance"] == Decimal("4300.00")
    assert audit["latest_running_balance"] == Decimal("4300.00")
    assert audit["discrepancy"] == Decimal("0.0000")


def test_fractional_amounts_reconcile(db, test_user):
    """Fractional Decimal amounts like 333.3333, 666.6667 reconcile with zero float drift"""
    credit(db, test_user.id, Decimal("333.3333"), memo="Fractional credit 1")
    credit(db, test_user.id, Decimal("666.6667"), memo="Fractional credit 2")
    debit(db, test_user.id, Decimal("500.0000"), memo="Fractional debit")

    audit = reconcile(db, test_user.id)
    assert audit["is_reconciled"] is True
    assert audit["computed_balance"] == Decimal("500.0000")
    assert audit["latest_running_balance"] == Decimal("500.0000")


def test_ledger_entries_are_immutable(db, test_user):
    """Ledger table is append-only. No UPDATE occurs in service operations."""
    entry1 = credit(db, test_user.id, Decimal("1000.00"), memo="Initial")
    entry2 = debit(db, test_user.id, Decimal("400.00"), memo="Payment")

    entries = get_ledger_history(db, test_user.id)
    assert len(entries) == 2
    # Verify values on entry1 were not mutated by subsequent debit
    assert entries[1].amount == Decimal("1000.00")
    assert entries[1].running_balance == Decimal("1000.00")


def test_reconcile_on_new_account(db, test_user):
    """Fresh user has balance = 0, reconcile passes with 0 transactions"""
    audit = reconcile(db, test_user.id)
    assert audit["is_reconciled"] is True
    assert audit["ledger_count"] == 0
    assert audit["computed_balance"] == Decimal("0.00")
    assert audit["discrepancy"] == Decimal("0.00")


def test_large_transaction_sequence(db, test_user):
    """50 alternating random transactions reconcile at each step"""
    random.seed(999)
    current_bal = Decimal("0.00")

    # Seed initial buffer
    credit(db, test_user.id, Decimal("10000.00"), memo="Seed buffer")
    current_bal += Decimal("10000.00")

    for step in range(50):
        if random.random() < 0.5:
            delta = Decimal(str(random.randint(10, 500)))
            credit(db, test_user.id, delta, memo=f"Step credit {step}")
            current_bal += delta
        else:
            delta = Decimal(str(random.randint(10, 300)))
            debit(db, test_user.id, delta, memo=f"Step debit {step}")
            current_bal -= delta

    audit = reconcile(db, test_user.id)
    assert audit["is_reconciled"] is True
    assert audit["computed_balance"] == current_bal
    assert audit["latest_running_balance"] == current_bal
    assert audit["ledger_count"] == 51


def test_reference_id_stored(db, test_user):
    """Debit with reference_id stores the reference properly"""
    credit(db, test_user.id, Decimal("5000.00"), memo="Deposit")
    entry = debit(db, test_user.id, Decimal("1500.00"), memo="Stock order", reference_id="ORD-XYZ-999")

    assert entry.reference_id == "ORD-XYZ-999"
    retrieved = get_ledger_history(db, test_user.id)[0]
    assert retrieved.reference_id == "ORD-XYZ-999"


def test_multiple_users_isolated(db, test_user):
    """Operations on User A do not mutate User B's balance or ledger"""
    user_b = User(
        email="user_b@hindsight.app",
        hashed_password=hash_password("Pass123!"),
        full_name="Rajesh Kumar",
        is_demo=False,
    )
    db.add(user_b)
    db.commit()
    db.refresh(user_b)

    credit(db, test_user.id, Decimal("2000.00"), memo="User A Credit")
    credit(db, user_b.id, Decimal("500.00"), memo="User B Credit")

    assert get_balance(db, test_user.id) == Decimal("2000.00")
    assert get_balance(db, user_b.id) == Decimal("500.00")

    debit(db, test_user.id, Decimal("700.00"), memo="User A Debit")

    assert get_balance(db, test_user.id) == Decimal("1300.00")
    assert get_balance(db, user_b.id) == Decimal("500.00")

    audit_a = reconcile(db, test_user.id)
    audit_b = reconcile(db, user_b.id)
    assert audit_a["is_reconciled"] is True
    assert audit_b["is_reconciled"] is True


def test_concurrent_credits_safe(db, test_user):
    """Simulate concurrent threads crediting the wallet; final balance is strictly sum of credits"""
    num_threads = 5
    credit_amount = Decimal("100.00")

    def worker():
        credit(db, test_user.id, credit_amount, memo="Concurrent credit")

    threads = [threading.Thread(target=worker) for _ in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    audit = reconcile(db, test_user.id)
    expected_total = credit_amount * num_threads
    assert audit["is_reconciled"] is True
    assert audit["latest_running_balance"] == expected_total
