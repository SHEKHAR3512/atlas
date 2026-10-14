# ATLAS
## Autonomous Trading & Learning Agent System

> An autonomous quantitative research, backtesting, paper-trading, risk-management, and algorithmic execution platform for Indian equity markets (NSE cash equities, Long only).

---

## 1. Operating Architecture & Principle

ATLAS operates on a strict, unidirectional risk-governed hierarchy:

```text
LLM / Research AI
        ↓
Trading hypothesis
        ↓
Strategy engine
        ↓
Statistical validation (Walk-Forward & Monte Carlo)
        ↓
Signal
        ↓
Portfolio engine (Fractional Kelly Criterion)
        ↓
Risk engine (Deterministic Hard Limits)
        ↓
Compliance & Circuit Breakers
        ↓
Execution engine
        ↓
Paper Broker / Real Broker (Angel One)
```

**Cardinal Rules:**
- **Capital preservation has priority over profit generation.**
- An LLM is strictly prohibited from placing orders directly.
- The AI cannot disable circuit breakers or increase maximum portfolio risk.
- **Fail-Closed by Design:** Any missing credential, unacknowledged live flag, stale data, or portfolio mismatch freezes trading immediately.
- Default mode is always **PAPER TRADING** with simulated Indian cash delivery charges and slippage.

---

## 2. System Prerequisites

- **OS:** Ubuntu Linux (x86_64)
- **Python:** Python 3.12+ (Python 3.14 compatible)
- **Node.js:** Node LTS 22 (`.nvmrc` included)
- **Docker & Docker Compose:** Optional for containers, or native standalone mode.
- **Optional Local AI:** Ollama running on `http://localhost:11434` (falls back seamlessly to `DisabledAIProvider`).

---

## 3. Quick Start & Setup

### Clone and Configure Environment

```bash
git clone <repository>
cd atlas

# Copy environment variables template
cp .env.example .env
```

The default `.env` is configured for **Paper Trading**:

```env
TRADING_MODE=PAPER
ENABLE_LIVE_TRADING=false
BROKER=paper
INITIAL_PAPER_CAPITAL=100000
MARKET=NSE
TIMEZONE=Asia/Kolkata
```

### Automatic Setup

```bash
make setup
```

This initializes the virtual environment (`.venv`), installs quantitative dependencies, and builds the frontend dashboard.

### Seed Database with NSE Universe & Strategies

```bash
make seed
```

Seeds 12 liquid NSE equities (RELIANCE, TCS, HDFCBANK, INFY, ICICIBANK, SBIN, etc.), 4 baseline strategies, and calibrated historical daily bars.

### Launch Application

```bash
make up
```

Services will be accessible locally:

| Service | URL | Description |
|---|---|---|
| **Web Dashboard** | `http://localhost:3000` | Full dark quantitative trading dashboard |
| **FastAPI REST API** | `http://localhost:8000` | Core backend REST API |
| **Interactive API Docs**| `http://localhost:8000/docs` | Swagger OpenAPI specification |
| **Prometheus Metrics** | `http://localhost:8000/metrics` | Quantitative Prometheus metrics |
| **Grafana Dashboard** | `http://localhost:3001` | Grafana telemetry monitoring (Docker mode) |

---

## 4. Key Makefile Commands

| Command | Description |
|---|---|
| `make setup` | Create virtualenv and install Python + Node dependencies |
| `make up` | Start backend API and Next.js dashboard |
| `make down` | Stop all running services |
| `make restart` | Restart services |
| `make logs` | Tail service logs |
| `make migrate` | Apply database schemas |
| `make seed` | Populate instruments, historical market bars, and default portfolio |
| `make test` | Run full automated unit and integration test suite |
| `make paper` | Run autonomous paper trading daemon |
| `make backtest` | Execute historical backtests across all approved strategies |
| `make research` | Run the Autonomous Research Lab experiment and mutation queue |
| `make live-preflight` | Run strict preflight safety checks for live trading readiness |
| `make kill` | **Trigger Emergency Hard Kill Switch (Immediate Fail-Closed)** |
| `make backup` | Create snapshot database backup in `backups/` |
| `make restore FILE=path` | Restore database snapshot from file |

---

## 5. Strategy Library

ATLAS V1 includes 4 core quantitative strategy families for NSE cash equities:

1. **Strategy A — Trend Following (`trend_following_v1`):**
   - Multi-timeframe moving averages (EMA 20, 50, 200) + ADX trend strength + ATR trailing stops.
   - Compatible regimes: `bull_trend`, `low_volatility`.

2. **Strategy B — Cross-Sectional Momentum (`momentum_cross_sectional_v1`):**
   - Ranks liquid universe by medium-term risk-adjusted momentum (Return / Realized Volatility).
   - Liquidity volume filters and top decile selection.

3. **Strategy C — Mean Reversion (`mean_reversion_rsi_v1`):**
   - RSI oversold bounces + Lower Bollinger Band touches + Rolling Z-score.
   - Strictly active in `sideways` or `low_volatility` regimes.

4. **Strategy D — Donchian Breakout (`breakout_donchian_v1`):**
   - 20-day high breakouts with 1.25x volume confirmation and ATR volatility stops.

---

## 6. Mathematical Capital Allocation & Fractional Kelly

Position sizing follows an immutable quantitative pipeline:

$$f^* = \frac{b \cdot p - q}{b}$$

Where:
- $p$ = Verified historical win rate (calculated from $\ge 100$ trades)
- $q = 1 - p$
- $b$ = Payoff ratio ($\text{Average Win} / |\text{Average Loss}|$)
- Fractional Kelly multiplier: $0.25$ (Quarter-Kelly)
- Absolute hard ceiling: $3.0\%$ per position ($f^* \le 0.03$)

If sample size $< 100$ trades, Kelly is bounded to conservative bootstrap ($0.5\%$) or zero.

---

## 7. Hard Risk Limits & Circuit Breakers

The deterministic Risk Engine enforces hard constraints that cannot be modified by AI:

- **Maximum Position Size:** 3.0% of portfolio equity
- **Maximum Gross Exposure:** 60.0% of portfolio equity
- **Maximum Sector Exposure:** 15.0% of portfolio equity
- **Daily Loss Circuit Breaker:** 1.5% maximum daily loss
- **Weekly Loss Circuit Breaker:** 4.0% maximum weekly loss
- **Portfolio Drawdown Circuit Breaker:** 8.0% peak-to-trough drawdown
- **Maximum Allowed Slippage:** 20 bps
- **Restricted Asset Invariants:** Long-only cash equities (No shorts, no margin, no futures, no options, no leverage).

---

## 8. Live Trading Safety Preflight Gate

To prevent accidental live capital loss, live execution is locked behind strict barriers:

1. `TRADING_MODE=LIVE`
2. `ENABLE_LIVE_TRADING=true`
3. `LIVE_TRADING_ACK=I_UNDERSTAND_REAL_CAPITAL_IS_AT_RISK`
4. Angel One API key, Client Code, Password, and TOTP secret configured.
5. Whitelisted Static IP confirmed.
6. `make live-preflight` passes all 9 safety checklist items.

**If any variable or check fails, live execution FAILS CLOSED.**

---

## 9. Testing & Quality Assurance

Run the comprehensive test suite:

```bash
make test
```

Tests cover:
- Mathematical fractional Kelly sizing & edge bounds
- Risk Engine limit enforcement & scale-down logic
- Kill switch instant order rejection
- Drawdown breach triggers
- Realistic NSE Cash Delivery fee schedule (Brokerage, STT, Exchange, GST, SEBI, Stamp Duty)
- Slippage models with market impact
- All four quantitative strategy signal engines
- Full end-to-end integration: `Signal → Allocator → Risk Engine → PaperBroker → Execution → Portfolio → Reconciliation`.

---

## 10. User Experience & Explainability

ATLAS features a dark quantitative dashboard (`http://localhost:3000`) with:
- Real-time portfolio equity curves, drawdown gauges, and asset allocation
- Active positions and idempotent order execution logs
- Autonomous Research Lab candidate and experiment viewer
- Risk Center with current vs maximum limit telemetry
- Macro Market Regime indicators
- **"WHY DID ATLAS MAKE THIS TRADE?"** — Section 52 Explainability view detailing the exact statistical observations, win rate, Kelly calculation, risk checks, and execution reasoning for every position.
