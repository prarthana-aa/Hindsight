# Hindsight: Micro-Investing Robo-Advisor (M1 Backend)

> **IMPORTANT LEGAL & EDUCATIONAL DISCLAIMER**  
> *All capital and currency values in this platform are 100% virtual simulations (INR). No real securities, banking, or brokerage systems are accessed. All recommendations and portfolio models are educational simulations designed for academic purposes and do not constitute registered investment advice under SEBI (Investment Advisers) Regulations, 2013.*

---

## 1. Overview & System Architecture

**Hindsight** is a micro-investing robo-advisor web platform designed for first-time retail investors. It profiles risk using SEBI-style capacity vs. tolerance evaluation, generates explainable asset allocations across 4 core proxies (`NIFTY50`, `GILT`, `GOLD`, `INTLEQ`), executes mock market orders, tracks holdings with weighted average cost basis, and enforces an immutable double-entry wallet ledger.

```
                      +---------------------------------------+
                      |       Web Frontend / API Clients      |
                      +---------------------------------------+
                                          |
                              HTTP / REST / Bearer JWT
                                          v
+-----------------------------------------------------------------------------+
|                            FASTAPI BACKEND                                  |
|                                                                             |
|  +-----------------------------------------------------------------------+  |
|  | Routers: /auth  |  /wallet  |  /prices  |  /portfolio  |  /advice     |  |
|  +-----------------------------------------------------------------------+  |
|                                     |                                       |
|                  +------------------+------------------+                    |
|                  v                                     v                    |
|       +---------------------+               +---------------------+         |
|       |    Wallet Ledger    |               |   Order Executor    |         |
|       |  Double-Entry Engine|               |   Idempotent Logic  |         |
|       +---------------------+               +---------------------+         |
|                  |                                     |                    |
|                  +------------------+------------------+                    |
|                                     v                                       |
|                           +-------------------+                             |
|                           |   SQLite Engine   |                             |
|                           | (hindsight.db)    |                             |
|                           +-------------------+                             |
+-----------------------------------------------------------------------------+
                               |                             |
                               v                             v
           +-------------------------------+   +-----------------------------+
           |     PRICE DATA SERVICE        |   |       FINANCE ENGINE        |
           |                               |   |   (Zero Web Dependencies)   |
           | 1. In-memory TTL Cache (5m)   |   |                             |
           | 2. Live Market Feed (yfinance)|   | * Risk Capacity & Tolerance |
           | 3. SQLite Cached Historical   |   | * Suitability Ceiling Logic |
           | 4. Bundled Fallback (CSV)     |   | * Asset Allocation (SAA)    |
           +-------------------------------+   | * Drift & Rebalancing       |
                                               +-----------------------------+
```

---

## 2. Key Architectural Guarantees (Viva Defense Highlights)

### A. Double-Entry Style Append-Only Wallet Ledger
- **Append-Only Immutability**: No `UPDATE` or `DELETE` statements are ever executed on `wallet_ledger`.
- **Mathematical Invariant**: Running balance is strictly non-negative at all times ($running\_balance \ge 0$).
- **Reconciliation Engine**: Reconstructs cumulative sum of all `CREDIT` entries minus all `DEBIT` entries and asserts exact match against the latest recorded running balance ($discrepancy = 0.0000$).
- **Precision**: Uses Python's `Decimal` throughout to eradicate floating-point IEEE-754 drift.

### B. Idempotent Mock Order Engine
- Every order requires a client-generated or unique `idempotency_key`.
- If a duplicate order request arrives (e.g. network retry or double-click), the engine immediately returns the existing executed order without charging the wallet twice.
- **Friction Modeling**: Simulates 10 bps (0.10%) transaction fees and 5 bps (0.05%) execution slippage.
- **Holding Accounting**: Calculates real-time weighted average cost basis:
  $$\text{New Average Cost} = \frac{(\text{Old Qty} \times \text{Old Avg Cost}) + (\text{Buy Qty} \times \text{Exec Price})}{\text{Old Qty} + \text{Buy Qty}}$$

### C. Isolated Finance Engine (`finance_engine/`)
- Contains **zero** web or database dependencies (`no FastAPI`, `no SQLAlchemy`, `no HTTP`). Pure Python logic.
- **Suitability Floor Formula**:
  $$\text{Final Risk Score} = \min(\text{Capacity Score}, \text{Tolerance Score})$$
  *Why*: Even if an investor has an aggressive psychological appetite (tolerance = 10), if their time horizon is short or emergency buffer is zero (capacity = 2), suitability mandates a conservative allocation to prevent forced panic liquidation.
- **Auditable Explanations**: Produces human-readable rationale paragraphs and stamps rule versions (`v1.0.0`) into compliance audit logs.

### D. Resilient Multi-Tier Price Layer
- **Hierarchy**:
  1. In-memory TTL cache (5 min)
  2. Live market quote via `yfinance`
  3. SQLite `prices` table (persisted history)
  4. Bundled fallback CSV (`data/prices_fallback.csv` with 2000+ daily closes)
- Every price quote contains a `source` tag (`live`, `cache`, `fallback`) and an `is_stale` boolean flag so the UI can transparently inform the user.

---

## 3. Quickstart & Installation

### Requirements
- Python 3.11+
- Virtual environment (recommended)

### Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start FastAPI development server
uvicorn backend.main:app --reload --port 8000
```

### Frontend development

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` and choose **Try Demo**. Vite proxies API requests to FastAPI.

### One-service Render deployment

This repository includes `render.yaml`. Create a new Render Blueprint from the repository and deploy the `hindsight` web service. Render installs Python and frontend dependencies, builds `frontend/dist`, and FastAPI serves that build from the same public URL. No `VITE_API_BASE_URL` is required in production because API calls use relative paths.

The included SQLite database is suitable for a classroom demonstration, but free-host filesystem storage can be ephemeral and may be reset during a redeploy or service restart. Do not treat it as permanent production storage.

The API will be available at:
- Interactive Swagger UI: `http://localhost:8000/docs`
- OpenAPI Specification: `http://localhost:8000/openapi.json`
- Health check: `http://localhost:8000/health`

---

## 4. Running Tests

The test suite covers ledger reconciliation, order idempotency, finance engine math, and price fallback:

```bash
pytest tests/ -v
```

---

## 5. API Endpoints Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and educational disclaimer |
| `POST` | `/auth/signup` | Register new account with simulated KYC-lite check |
| `POST` | `/auth/login` | Login and receive Bearer JWT |
| `POST` | `/auth/demo` | **1-Click Demo Login** (pre-loads portfolio & history) |
| `POST` | `/auth/demo/reset` | Resets demo account to factory state |
| `GET` | `/auth/me` | Fetch authenticated user profile |
| `POST` | `/wallet/deposit` | Virtual cash top-up (appends CREDIT ledger entry) |
| `GET` | `/wallet/balance` | Current balance and recent transaction history |
| `GET` | `/wallet/ledger` | Paginated append-only ledger entries |
| `GET` | `/wallet/reconcile` | **Audit Reconciliation**: verifies mathematical ledger balance |
| `GET` | `/prices/` | Latest quotes for `NIFTY50`, `GILT`, `GOLD`, `INTLEQ` |
| `GET` | `/prices/{asset}` | Specific asset quote with freshness label |
| `GET` | `/prices/{asset}/history` | Historical daily close timeseries |
| `POST` | `/prices/refresh` | Force refresh cache / fetch live |
| `POST` | `/portfolio/order` | Place market BUY/SELL with `idempotency_key` |
| `GET` | `/portfolio/orders` | Historical executed orders |
| `GET` | `/portfolio/dashboard` | Portfolio valuation, holdings, unrealized P&L, drift |
| `POST` | `/portfolio/rebalance/preview`| Generate proposed rebalance orders (SELLs first) |
| `POST` | `/portfolio/rebalance/execute`| User approval to execute proposed rebalancing |
| `GET` | `/advice/questions` | 8-question suitability questionnaire |
| `POST` | `/advice/score` | Compute capacity, tolerance, final score & allocation |
| `POST` | `/advice/apply` | Save recommended allocation & write to audit log |
