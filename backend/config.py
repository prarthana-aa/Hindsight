"""
Configuration and constants for Hindsight Robo-Advisor.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FALLBACK_CSV_PATH = DATA_DIR / "prices_fallback.csv"
DB_PATH = BASE_DIR / "hindsight.db"
DB_URL = f"sqlite:///{DB_PATH}"

# Security & Authentication
SECRET_KEY = "hindsight-robo-dev-secret-key-change-in-production"
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
