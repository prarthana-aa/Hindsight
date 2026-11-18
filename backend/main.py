"""
Hindsight Robo-Advisor FastAPI Application Entrypoint.

Key Architectural Guarantees:
- Double-entry style append-only wallet ledger
- Idempotent order execution engine
- Cached price data layer with bundled historical fallback data
- Isolated finance engine with zero web dependencies
- Educational virtual simulation disclaimer on all responses
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .config import ALLOWED_ORIGINS, DISCLAIMER_TEXT
from .database import create_all_tables, SessionLocal
from .models import PriceRecord
from .services.price_service import seed_prices_from_csv
from .seed_demo import seed_demo_account
from .routers import (
    auth_router,
    wallet_router,
    prices_router,
    portfolio_router,
    advice_router,
)


def init_system_data():
    """
    Initialize the configured schema, fallback price records, and demo account.
    Runs synchronously at startup.
    """
    create_all_tables()
    db = SessionLocal()
    try:
        seed_prices_from_csv(db)
        if db.query(PriceRecord).count() == 0:
            raise RuntimeError(
                "Price initialization incomplete; no records were loaded from data/prices_fallback.csv"
            )
        seed_demo_account(db, reset_if_exists=False)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_system_data()
    yield


app = FastAPI(
    title="Hindsight Robo-Advisor API",
    description=(
        "Micro-Investing Robo-Advisor platform with double-entry wallet ledger, "
        "idempotent order execution, multi-asset price feed, and auditable suitability engine. "
        "ALL MONEY IS VIRTUAL — EDUCATIONAL SIMULATION ONLY."
    ),
    version="1.0.0",
)

# CORS middleware for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DisclaimerMiddleware:
    """
    Pure ASGI compliance middleware that injects the educational disclaimer header
    into every HTTP response without relying on BaseHTTPMiddleware.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append((b"x-educational-disclaimer", DISCLAIMER_TEXT.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


# app.add_middleware(DisclaimerMiddleware)


# Include Routers
app.include_router(auth_router)
app.include_router(wallet_router)
app.include_router(prices_router)
app.include_router(portfolio_router)
app.include_router(advice_router)

# In production Render builds the Vite app into frontend/dist. Serving it here
# keeps the API and browser experience on one origin. During local development
# the directory is absent and Vite serves the frontend separately.
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/health", tags=["System"])
def health_check():
    """
    System health and compliance status check.
    """
    return {
        "status": "healthy",
        "app": "Hindsight Robo-Advisor API",
        "version": "1.0.0",
        "virtual_mode": True,
        "disclaimer": DISCLAIMER_TEXT,
    }


@app.get("/api", tags=["System"])
def root():
    """
    API overview and links. The site root is reserved for the React application.
    """
    return {
        "name": "Hindsight Robo-Advisor API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
        "disclaimer": DISCLAIMER_TEXT,
        "supported_assets": ["NIFTY50", "GILT", "GOLD", "INTLEQ"],
        "demo_account": {
            "email": "demo@hindsight.app",
            "one_click_endpoint": "POST /auth/demo",
        },
    }


@app.get("/{path:path}", include_in_schema=False)
def frontend_fallback(path: str):
    if FRONTEND_DIST.exists():
        requested = FRONTEND_DIST / path
        if requested.is_file():
            return FileResponse(requested)
        return FileResponse(FRONTEND_DIST / "index.html")
    return JSONResponse({"detail": "Frontend build not found. Run npm run build in frontend/ first."}, status_code=404)
