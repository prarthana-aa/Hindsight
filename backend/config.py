"""
Configuration and constants for Hindsight Robo-Advisor.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FALLBACK_CSV_PATH = DATA_DIR / "prices_fallback.csv"
DB_PATH = BASE_DIR / "hindsight.db"


def _database_url() -> str:
    """Return the configured database URL, preserving SQLite for local use."""
    configured = os.getenv("DATABASE_URL", "").strip()
    if not configured:
        return f"sqlite:///{DB_PATH}"

    # Neon commonly supplies a postgres:// URL. SQLAlchemy's psycopg dialect
    # is explicit here because psycopg2 is intentionally not a dependency.
    if configured.startswith("postgres://"):
        return "postgresql+psycopg://" + configured[len("postgres://"):]
    if configured.startswith("postgresql://"):
        return "postgresql+psycopg://" + configured[len("postgresql://"):]
    return configured


DB_URL = _database_url()

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").strip().lower()
_configured_database_url = os.getenv("DATABASE_URL", "").strip()
if ENVIRONMENT == "production" and not _configured_database_url:
    raise RuntimeError("DATABASE_URL must be set in production; refusing ephemeral SQLite.")
_DEV_SECRET_KEY = "hindsight-local-development-secret"
_configured_secret = os.getenv("SECRET_KEY", "").strip()
if ENVIRONMENT == "production" and len(_configured_secret) < 32:
    raise RuntimeError("SECRET_KEY must be set to a secure value in production.")
SECRET_KEY = _configured_secret or _DEV_SECRET_KEY

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

# Security & Authentication
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Market Execution & Costs
# 10 bps = 0.10% transaction fees (brokerage, STT, exchange charges)
TRANSACTION_COST_BPS = 10
# 5 bps = 0.05% expected market slippage
SLIPPAGE_BPS = 5

# Price Cache & Data Feed
PRICE_CACHE_TTL_SECONDS = 300  # 5 minutes
ASSETS = ["NIFTY50", "GILT", "GOLD", "INTLEQ"]

# Proxy Yahoo Finance Ticker mapping for real-world fallback
YFINANCE_TICKERS = {
    "NIFTY50": "^NSEI",
    "GILT": "^IRX",       # Yield/proxy
    "GOLD": "GC=F",       # Gold continuous futures
    "INTLEQ": "QQQ",      # Nasdaq proxy
}

# Pre-seeded Demo Account Credentials
DEMO_USER_EMAIL = "demo@hindsight.app"
DEMO_USER_PASSWORD = "DemoInvestor@2026"
DEMO_USER_NAME = "Aarav Sharma (Demo)"
DEMO_INITIAL_CAPITAL = 100000.00  # ₹1,00,000 virtual INR

# Legal & Compliance
DISCLAIMER_TEXT = (
    "EDUCATIONAL SIMULATION ONLY: Hindsight is a micro-investing robo-advisor simulation. "
    "All currency figures represent virtual INR. No real money or securities are traded. "
    "This does not constitute SEBI-registered investment advice."
)
