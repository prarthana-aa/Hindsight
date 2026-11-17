"""
API Routers Package.
"""
from .auth import router as auth_router
from .wallet import router as wallet_router
from .prices import router as prices_router
from .portfolio import router as portfolio_router
from .advice import router as advice_router

__all__ = [
    "auth_router",
    "wallet_router",
    "prices_router",
    "portfolio_router",
    "advice_router",
]

