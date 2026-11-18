"""
Pydantic v2 Request and Response Schemas.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


# -------------------------------------------------------------
# Auth Schemas
# -------------------------------------------------------------
class UserSignupRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2)
    age: Optional[float] = Field(default=28)
    income_band: Optional[str] = Field(default="5L-15L")
    employment_type: Optional[str] = Field(default="Salaried")
    simulated_pan: Optional[str] = Field(default="ABCDE1234F")
    accepted_disclosures: bool = Field(default=True)


class UserLoginRequest(BaseModel):
    email: str = Field(..., pattern=EMAIL_PATTERN)
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    is_demo: bool


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    age: Optional[float]
    income_band: Optional[str]
    employment_type: Optional[str]
    kyc_status: str
    is_demo: bool
    created_at: datetime

    class Config:
        from_attributes = True


# -------------------------------------------------------------
# Wallet & Ledger Schemas
# -------------------------------------------------------------
class DepositRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=4)
    memo: Optional[str] = Field(default="Virtual Wallet Top-up")


class LedgerEntryResponse(BaseModel):
    id: str
    user_id: str
    entry_type: str  # CREDIT, DEBIT
    amount: Decimal
    running_balance: Decimal
    reference_id: Optional[str]
    memo: str
    created_at: datetime

    class Config:
        from_attributes = True


class WalletBalanceResponse(BaseModel):
    user_id: str
    current_balance: Decimal
    currency: str = "INR"
    last_updated: Optional[datetime]
    recent_transactions: List[LedgerEntryResponse]


class ReconciliationReport(BaseModel):
    user_id: str
    is_reconciled: bool
    ledger_count: int
    sum_credits: Decimal
    sum_debits: Decimal
    computed_balance: Decimal
    latest_running_balance: Decimal
    discrepancy: Decimal
    status: str
    checked_at: datetime


# -------------------------------------------------------------
# Price Schemas
# -------------------------------------------------------------
class PriceQuote(BaseModel):
    asset: str
    close_price: Decimal
    price_date: date
    source: str  # live, cache, fallback
    is_stale: bool
    as_of: datetime


class PriceHistoryItem(BaseModel):
    date: date
    close: Decimal


class PriceHistoryResponse(BaseModel):
    asset: str
    count: int
    data: List[PriceHistoryItem]


# -------------------------------------------------------------
# Order & Portfolio Schemas
# -------------------------------------------------------------
class OrderCreateRequest(BaseModel):
    asset: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: Decimal = Field(..., gt=0)
    idempotency_key: str = Field(..., min_length=8)


class OrderResponse(BaseModel):
    id: str
    user_id: str
    asset: str
    side: str
    quantity: Decimal
    price: Decimal
    gross_amount: Decimal
    transaction_cost: Decimal
    net_amount: Decimal
    status: str
    idempotency_key: str
    failure_reason: Optional[str]
    created_at: datetime
    executed_at: Optional[datetime]

    class Config:
        from_attributes = True


class HoldingResponse(BaseModel):
    asset: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    current_weight: Decimal


class PortfolioDashboardResponse(BaseModel):
    user_id: str
    cash_balance: Decimal
    invested_value: Decimal
    total_portfolio_value: Decimal
    total_unrealized_pnl: Decimal
    total_pnl_pct: Decimal
    holdings: List[HoldingResponse]
    target_allocation: Optional[Dict[str, float]]
    drift_status: Optional[Dict[str, float]]
    needs_rebalance: bool


# -------------------------------------------------------------
# Risk & Advice Schemas
# -------------------------------------------------------------
class RiskProfileSubmitRequest(BaseModel):
    answers: Dict[str, int]  # question_id -> option_index
    goal_type: Optional[str] = "Wealth Creation"
    horizon_years: Optional[int] = 5


class RecommendationResponse(BaseModel):
    risk_score: float
    risk_label: str
    capacity_score: float
    tolerance_score: float
    constraint_driver: str
    target_allocation: Dict[str, float]
    suitability_explanation: str
    expected_annual_return: float
    expected_annual_volatility: float
    rule_version: str
    disclaimer: str


class AssetRecommendationResponse(BaseModel):
    asset: str
    name: str
    role: str
    target_weight: float
    expected_return: float
    volatility: float


class UserRecommendationResponse(RecommendationResponse):
    assets: List[AssetRecommendationResponse]
