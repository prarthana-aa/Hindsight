"""
SQLAlchemy ORM Data Models for Hindsight Robo-Advisor.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Numeric,
    DateTime,
    Date,
    ForeignKey,
    Boolean,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from .database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    age = Column(Float, nullable=True)
    income_band = Column(String(100), nullable=True)
    employment_type = Column(String(100), nullable=True)
    pan_hash = Column(String(64), nullable=True)  # SHA-256 hash of simulated PAN
    kyc_status = Column(String(50), default="verified", nullable=False)  # pending, verified
    consent_ts = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    is_demo = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships with full cascade on delete
    risk_profile = relationship("RiskProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    portfolio = relationship("Portfolio", back_populates="user", uselist=False, cascade="all, delete-orphan")
    ledger_entries = relationship("WalletLedger", back_populates="user", order_by="WalletLedger.created_at.asc()", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", order_by="Order.created_at.desc()", cascade="all, delete-orphan")
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    answers = Column(JSON, nullable=False)  # Map of question_id -> option_index
    capacity_score = Column(Float, nullable=False)
    tolerance_score = Column(Float, nullable=False)
    final_score = Column(Float, nullable=False)
    risk_label = Column(String(50), nullable=False)
    rule_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="risk_profile")


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_type = Column(String(100), nullable=False)  # emergency, house, retirement, custom
    title = Column(String(200), nullable=False)
    target_amount = Column(Numeric(18, 2), nullable=False)
    target_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="goals")


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    target_allocation = Column(JSON, nullable=False)  # {"NIFTY50": 0.50, "GILT": 0.30, ...}
    strategy = Column(String(100), default="rule_based_saa", nullable=False)
    suitability_rationale = Column(String(2000), nullable=True)
    rule_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="portfolio")


class WalletLedger(Base):
    """
    Append-Only Double-Entry Wallet Ledger Table.
    Every financial transaction appends a record with the exact running balance.
    No UPDATE or DELETE is ever executed on this table.
    Sequential 'seq' integer guarantees strict monotonic chronological ordering.
    """
    __tablename__ = "wallet_ledger"

    seq = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(String(36), default=generate_uuid, unique=True, nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entry_type = Column(String(10), nullable=False)  # CREDIT, DEBIT
    amount = Column(Numeric(18, 4), nullable=False)  # Positive transaction delta
    running_balance = Column(Numeric(18, 4), nullable=False)  # Balance after this movement
    reference_id = Column(String(100), nullable=True, index=True)  # Links to Order ID or deposit txn
    memo = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User", back_populates="ledger_entries")


class Order(Base):
    """
    Order execution record with strict idempotency constraint.
    """
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Numeric(18, 6), nullable=False)
    price = Column(Numeric(18, 4), nullable=False)  # Executed price per unit
    gross_amount = Column(Numeric(18, 4), nullable=False)  # qty * price
    transaction_cost = Column(Numeric(18, 4), nullable=False)  # Brokerage & taxes
    net_amount = Column(Numeric(18, 4), nullable=False)  # gross + fee (BUY) or gross - fee (SELL)
    status = Column(String(20), nullable=False)  # PENDING, EXECUTED, FAILED
    idempotency_key = Column(String(128), unique=True, nullable=False, index=True)
    failure_reason = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    executed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="orders")


class Holding(Base):
    """
    Current portfolio position per asset per user.
    Maintains weighted-average cost basis.
    """
    __tablename__ = "holdings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    asset = Column(String(20), nullable=False)
    quantity = Column(Numeric(18, 6), default=0.0, nullable=False)
    avg_cost = Column(Numeric(18, 4), default=0.0, nullable=False)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="holdings")

    __table_args__ = (
        UniqueConstraint("user_id", "asset", name="uq_user_asset_holding"),
    )


class PriceRecord(Base):
    """
    Cached historical and latest close prices.
    """
    __tablename__ = "prices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    asset = Column(String(20), nullable=False, index=True)
    price_date = Column(Date, nullable=False, index=True)
    close_price = Column(Numeric(18, 4), nullable=False)
    source = Column(String(50), default="fallback", nullable=False)  # live, cache, fallback
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("asset", "price_date", name="uq_asset_price_date"),
    )


class AuditLog(Base):
    """
    Immutable compliance audit trail.
    Every suitability recommendation, rule version, and order is stamped here.
    """
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_data = Column(JSON, nullable=False)
    rule_version = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
