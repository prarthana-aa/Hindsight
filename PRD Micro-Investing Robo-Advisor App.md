# PRD: Micro-Investing Robo-Advisor App

*Working name: **Hindsight** (rename freely). Context: FT4 component, Programming for Fintech Honors. Format: shareable web link with a ready demo account, no signup needed to try it.*

## 1. Overview

A mini wealth-management platform that onboards a user, profiles their risk, recommends a diversified portfolio with a clear suitability explanation, then manages it: it executes mock orders at real market prices from a virtual wallet, tracks holdings and P&L, monitors goal progress, and alerts the user when the portfolio drifts and needs rebalancing. A "Learn" area (backtester and a historical-crash game) shows why the advice works.

**One-line pitch:** *"A robo-advisor that builds your portfolio, explains why, manages it for you, and lets you test it against 2008 before risking a rupee."*

**Important framing:** all money is virtual and all outputs are educational simulations, not investment advice. This is stated in the UI and the README.

## 2. Problem

- First-time investors don't know how to split money across equity, debt, and gold, so they pick random funds or follow friends.
- Most apps recommend products without explaining the *why*, so users panic-sell in downturns.
- Beginners have nowhere safe to practice investing and seeing real portfolio behavior.
- Rebalancing is ignored, so portfolios drift away from the user's risk level without anyone noticing.

## 3. Goals and Non-Goals

**Goals**

- Deliver an end-to-end fintech flow: onboarding, KYC-lite, risk profile, recommendation, execution, monitoring, rebalancing.
- Make every recommendation explainable and auditable.
- Be demo-ready from a single link with a pre-loaded demo account.
- Show real financial engineering in code (allocation, optimization, backtesting, portfolio accounting).
- Be easy to defend in a viva: every number traceable to a formula.

**Non-Goals (v1)**

- No real money, no real broker or payment integration.
- No real KYC document verification (simulated only).
- No individual stock picking, derivatives, or crypto.
- Not regulated advice. Uses SEBI-style disclosure language for realism only.

## 4. Target Users

| Persona | Need |
| --- | --- |
| **First-time investor (primary)** | Know what to buy, why, and how much |
| **Student learner** | Practice with virtual money, learn from mistakes |
| **Evaluator (professor/recruiter)** | See a complete, well-engineered fintech flow quickly |

## 5. User Flow

1. **Landing**: "Try demo account" or "Create account".
2. **Onboarding and KYC-lite**: name, age, income band, employment type, simulated PAN/Aadhaar format check, consent and disclosures.
3. **Risk profiling**: \~8-question questionnaire covering horizon, goal, income stability, loss tolerance, and experience. Output is a risk score (1-10) and a label (Conservative to Aggressive).
4. **Goal setup**: pick a goal (emergency fund, house, retirement, custom), target amount, and date.
5. **Recommendation**: target allocation across asset classes, projected range, and a **suitability explanation** ("Because your horizon is 12 years and your loss tolerance is moderate, 55% equity...").
6. **Funding**: add virtual money to the wallet (lump sum and/or monthly SIP).
7. **Execution**: the app places mock buy orders at real prices to reach the target allocation.
8. **Dashboard**: holdings, allocation vs. target, P&L, goal progress and probability, upcoming SIPs.
9. **Monitoring**: drift detection triggers a rebalance alert; user approves, orders execute, and the audit log records it.
10. **Learn**: run a backtest of the user's portfolio, or play a historical crash scenario.

## 6. Core Features

### F1. Authentication and demo mode (P0)

- Email-style signup with local or lightweight auth, plus a one-click **demo account** pre-loaded with a portfolio and a few months of history so the link works instantly.

### F2. KYC-lite onboarding (P0)

- Collect basic profile, validate PAN format, and show a simulated verification step.
- Store consent and disclosure acceptance with a timestamp.

### F3. Risk profiling engine (P0)

- Weighted questionnaire producing a risk score, split into **risk capacity** (can you afford losses: horizon, income stability) and **risk tolerance** (will you stay calm).
- Final risk level is the *lower* of the two, which is how real suitability logic works, and it's easy to explain.

### F4. Portfolio construction (P0)

- Asset classes: Indian equity (Nifty 50 proxy), debt (gilt/short-term proxy), gold, optional international equity.
- Strategy options: (a) rule-based allocation by risk band, (b) mean-variance (Markowitz) optimization within risk constraints, (c) risk parity. v1 ships (a); (b) and (c) are P1.
- Output includes the **suitability explanation** and the efficient frontier chart (P1).

### F5. Virtual wallet and order execution (P0)

- Wallet balance, deposits, and a ledger of every movement.
- Mock order engine: market orders at the latest available price, with simple transaction cost and slippage assumptions.
- Order states: created, executed, failed (e.g., insufficient funds).

### F6. Portfolio accounting and dashboard (P0)

- Holdings, average cost, market value, unrealized P&L, XIRR for SIP flows.
- Allocation vs. target donut/bar, performance line vs. benchmark.

### F7. Goal tracking (P0)

- Required SIP calculator and goal-hit probability using a Monte Carlo simulation of the current portfolio.
- Progress bar and "how to get back on track" suggestions.

### F8. Drift detection and rebalancing (P0)

- Compare current weights to target. If any asset breaches a tolerance band (e.g., ±5 percentage points) or on a periodic schedule, raise an alert.
- Rebalance proposal shows the exact orders, estimated costs, and why; the user approves it.

### F9. Audit log and compliance layer (P0)

- Immutable log of every recommendation, input snapshot, rule or model version, user approval, and executed order.
- Standard disclosures, suitability statement, and a downloadable "advice record" PDF (P1).

### F10. Backtester (P1, Learn)

- Replay the user's recommended allocation over history with monthly rebalancing. Metrics: CAGR, volatility, max drawdown, Sharpe, worst 12 months, compared to benchmarks.

### F11. Crash game (P1, Learn)

- Replay a real historical period (2008, 2020, 2022) month by month with hidden future. The user adjusts allocation and is scored against buy-and-hold and the advisor.
- A behavior report flags panic-selling and rally-chasing.

### F12. Alerts and notifications (P1)

- In-app notifications for rebalance, SIP executed, goal off-track, and large drawdown.

### F13. Explain-it assistant (P2, stretch)

- An LLM layer that answers "why this allocation?" using only the computed rationale and never generates numbers.

## 7. System Architecture

| Layer | Responsibility |
| --- | --- |
| **Frontend (React)** | Onboarding, dashboard, charts, learn modes |
| **API (FastAPI or Node)** | Auth, accounts, orders, portfolio state, audit log |
| **Finance engine (Python or TypeScript modules)** | Risk scoring, allocation, optimizer, backtester, Monte Carlo, rebalancer |
| **Market data service** | Fetches and caches prices from a free API; falls back to bundled historical files |
| **Database (SQLite or Postgres)** | Users, wallet ledger, orders, holdings, audit log |

Key design choices worth stating in the viva:

- **Double-entry style ledger** for the wallet so balances always reconcile.
- **Idempotent order execution**, so a retried request can't double-buy.
- **Versioned rules and models**, so every recommendation is reproducible.
- **Engine separated from UI and API**, so it's unit-testable.

## 8. Data Model (core tables)

- `users` (id, profile, kyc\_status, consent\_ts)
- `risk_profiles` (user\_id, answers, capacity, tolerance, final\_score, version)
- `goals` (user\_id, target\_amount, target\_date, type)
- `portfolios` (user\_id, target\_allocation, strategy, version)
- `wallet_ledger` (id, user\_id, type, amount, balance\_after, ts)
- `orders` (id, user\_id, asset, side, qty, price, cost, status, idempotency\_key, ts)
- `holdings` (user\_id, asset, qty, avg\_cost)
- `audit_log` (id, user\_id, event, inputs\_snapshot, rule\_version, ts)
- `prices` (asset, date, close)

## 9. Functional Requirements

- Every recommendation stores its inputs, output, and rule version in the audit log.
- Wallet balance can never go negative; orders that would do so fail with a clear message.
- Portfolio value and P&L reconcile to the ledger and orders at all times (tested).
- Risk level always uses the lower of capacity and tolerance.
- Rebalance proposals require explicit user approval before execution.
- The demo account is resettable with one click.
- A disclaimer is visible on recommendation and results screens.

## 10. Non-Functional Requirements

| Area | Target |
| --- | --- |
| Performance | Dashboard < 1s load on cached data; backtest < 2s |
| Reliability | Price-fetch failures fall back to the last known price or bundled data and are flagged in the UI |
| Security | Hashed passwords, input validation, no real PII, no real financial data |
| Accessibility | Keyboard navigable, color-blind-safe charts |
| Testability | Engine and ledger unit-tested; sample accounts for integration tests |

## 11. Suggested Tech Stack

- **Frontend:** React + TypeScript + Vite, Tailwind, Recharts or D3
- **Backend:** FastAPI (Python) with SQLite for v1, which makes the finance engine natural to write with pandas and NumPy
- **Market data:** yfinance or a similar free source, cached, with bundled CSV fallback
- **Testing:** pytest for the engine and ledger, plus a few end-to-end flows
- **Hosting:** Vercel/Netlify (frontend) plus Render/Railway (backend). If hosting a backend is a hassle, a fully client-side fallback is possible using IndexedDB for state.

## 12. Success Metrics

- A new evaluator can reach a populated dashboard in under 10 seconds via demo mode.
- Ledger reconciliation test passes for 100% of generated scenarios.
- Backtest results match an independent hand or spreadsheet calculation within a small tolerance.
- Every recommendation has a retrievable audit record.
- Viva readiness: each module has a one-paragraph explanation of its formula and assumptions.

## 13. Milestones

| Phase | Scope | Outcome |
| --- | --- | --- |
| **M1: Foundations** | Data model, auth, wallet ledger, price data layer | Money moves correctly |
| **M2: Advice** | KYC-lite, risk profiling, rule-based allocation, suitability explanation | Recommendations with reasons |
| **M3: Investing** | Mock order engine, holdings, P&L dashboard, SIPs | A working investing app |
| **M4: Management** | Drift detection, rebalance flow, goal tracking, audit log | The "robo" part is real |
| **M5: Learn** | Backtester, crash game, behavior report | Differentiators and demo energy |
| **M6: Polish** | Demo account, disclosures, README and architecture diagram, report | Submission-ready |
| **Stretch** | Markowitz and risk parity, explain-it assistant, advice-record PDF | Extra depth |

## 14. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Free market API breaks or rate-limits | Cache aggressively, bundle historical CSVs, show a data-freshness label |
| Scope too big for the deadline | Strict P0/P1/P2 split; M1-M4 is a complete project on its own |
| Looks like real advice | Visible disclaimers, "virtual money" labeling, educational framing |
| Debt and gold data are messy | Use clear proxies, document the assumptions, and show them in the UI |
| Hosting a backend for the link | Use a free backend host, or fall back to client-side storage |
| Ledger or P&L bugs | Reconciliation tests and idempotency keys from day one |

## 15. Open Questions

- Does FT4 require specific elements (an API integration, ML, blockchain, a written report, a viva demo)? This may add or reorder features.
- Is a multi-user login needed, or is demo mode plus a simple signup enough?
- Python backend or fully client-side? This depends on hosting and the course's language expectations.
- Which two or three historical scenarios to ship for the crash game.

## 16. Prompt Seed for antigravity

> Build a robo-advisor web app per this PRD. Start with M1: a FastAPI backend with SQLite, a double-entry-style wallet ledger, idempotent order execution, and a price data layer with cached and bundled fallback data. Write pytest tests that prove the ledger always reconciles. Keep the finance engine (risk scoring, allocation, rebalancing) in a separate module with no web dependencies. All money is virtual; include disclaimers in the UI.
