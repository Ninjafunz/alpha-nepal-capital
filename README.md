# Alpha Nepal Capital

[![Daily Cycle](https://github.com/Ninjafunz/alpha-nepal-capital/actions/workflows/daily_cycle.yml/badge.svg)](https://github.com/Ninjafunz/alpha-nepal-capital/actions/workflows/daily_cycle.yml)
[![License: CC BY-NC-ND 4.0](https://img.shields.io/badge/License-CC%20BY--NC--ND%204.0-lightgrey.svg)](LICENSE)
[![Strategy: ASA-V1.ethics](https://img.shields.io/badge/Strategy-ASA--V1.ethics-blue.svg)](config/investment_policy.yaml)
[![Status: FLOURISHING](https://img.shields.io/badge/Status-FLOURISHING-00d26a.svg)](https://Ninjafunz.github.io/alpha-nepal-capital/website)
[![Compliance: 100%](https://img.shields.io/badge/Strategy%20Compliance-100%25-00d26a.svg)](config/investment_policy.yaml)

> *"Can a human-designed investment strategy, autonomously executed by an AI-managed virtual investment company using real-time market information, generate sustainable risk-adjusted returns in the Nepalese equity market?"*
>
> — Core Research Question, Alpha Nepal Capital

**Live Public Investor Portal:** [https://Ninjafunz.github.io/alpha-nepal-capital/website](https://Ninjafunz.github.io/alpha-nepal-capital/website)

---

## What is this?

Alpha Nepal Capital is an **empirical research experiment** — a fully operational virtual investment company run entirely by an autonomous AI management system, executing a human-designed investment philosophy on real NEPSE (Nepal Stock Exchange) and global market data.

**The human founder designed the strategy. The AI operates the company. The market judges the results.**

This is not a trading bot, not a recommendation tool, and not financial advice. It is a transparent, live, public record of whether AI can faithfully execute a structured investment constitution — the ASA-V1.ethics framework — and generate meaningful alpha over time.

---

## Architecture at a Glance

```
Human Founder (Chief Strategist)          AI Management (Autonomous Execution)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━         ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Investment philosophy (ASA-V1.ethics)   • Real-time NEPSE + Global price feed
• Risk tolerance & hard constraint limits • 3-Layer opportunity scoring engine
• Portfolio rules (25% stock, 40% sector) • Cognitive Delta threshold filter
• Starting capital (NPR 100M)             • Constitutional position sizer
• Strategy revisions (founder approval)  • Virtual trade execution + ledger
                                          • Daily / monthly AI reporting
```

---

## The ASA-V1.ethics Investment Constitution

```
Every investment vehicle is governed by exactly four structural forces and one cognitive gap.
Profits are found in the velocity of mispricing between academic consensus and physical reality.
Ethics are the longest-duration call option on regulatory goodwill.
```

### 3-Layer Scoring Pipeline

| Layer | Weight | What it evaluates |
|---|---|---|
| **Layer 1: Structural Anchoring** | 35% | Capital velocity, physical/operational risk, regulatory transition risk, bottleneck asymmetry |
| **Layer 2: Literature Audit** | 30% | Kondratiev/Elite Theory alignment, Prospect Theory mispriced middle, real options, regulatory capture |
| **Layer 3: Cognitive Delta Engine** | 35% | Three-bias audit (Narrative, Anchoring, Recency); requires **Delta ≥ 20%** gap between intrinsic value and market price before any capital is deployed |

### Constitutional Hard Rules

| Rule | Limit |
|---|---|
| Max single stock exposure | 25% |
| Max sector concentration | 40% |
| Min cash liquidity reserve | 5% |
| Max active holdings | 15 |
| Max portfolio drawdown (halt) | 25% |
| Strategy compliance score | 100% required |

### 3 Strategic Execution Routes

| Route | Description | Target Allocation |
|---|---|---|
| **Alpha — Defensive Moat** | Insulated infrastructure & sovereign-backed cash flows | 60% |
| **Beta — Contra-Cyclical Raid** | Deep value turnarounds with D/E > 2x and depressed P/E | 25% |
| **Gamma — Policy Hack** | Companies exceeding regulatory standards by 20%+ | 15% |

---

## Four-Portfolio Experimental Control Group

To objectively measure whether AI execution adds alpha, four portfolios run in parallel:

| Portfolio | Strategy | AI-Managed? |
|---|---|:---:|
| **Alpha Nepal Capital (P1)** | ASA-V1.ethics — NEPSE Equities (NPR 100M) | ✅ |
| **Global Equity Profile (P2)** | Global equities via yfinance (USD 1M offshore) | ✅ |
| **Commodities Profile (P3)** | Gold futures & commodities (USD 1M offshore) | ✅ |
| **Crypto Profile (P4)** | Bitcoin / major crypto (USD 1M offshore) | ✅ |

> **Regulatory note:** Nepalese law prohibits domestic capital from investing abroad. Global, Commodities, and Crypto portfolios are modelled as a legally isolated offshore subsidiary and tracked in USD.

---

## How the Daily Cycle Works

Every trading day (Sun–Thu), GitHub Actions automatically runs:

```
1. Price Ingestion       → NEPSE delayed quotes + yfinance for global assets
2. Fundamentals          → Audited P/E, EPS, book value per NEPSE sector
3. AI Decision Pipeline  → Score all assets → threshold filter → position sizer → execute
4. Leverage Manager      → Evaluates borrow/repay based on yield vs. cost of capital
5. Self-Reflection       → Win/loss post-mortems, AI accuracy tracking
6. Compliance Audit      → 6-rule constitutional check (must be 100%)
7. Benchmark Comparison  → 4-portfolio comparative NAV and Sharpe ratio tables
8. JSON Export + Deploy  → website/data/*.json committed → GitHub Pages rebuilt
```

---

## Repository Structure

```
alpha-nepal-capital/
├── config/
│   ├── investment_policy.yaml     # The IPS Constitution (human-defined)
│   ├── company_profile.yaml       # 4 portfolio profiles and starting capital
│   └── universe.yaml              # Eligible securities universe
│
├── src/
│   ├── cli.py                     # Entry point: `alpha-nepal run-daily`
│   ├── data/
│   │   ├── models.py              # Decision, Transaction, Stock, PriceBar data classes
│   │   ├── store.py               # SQLite immutable ledger
│   │   └── global_markets.py     # yfinance integration (global/crypto/commodity prices)
│   ├── strategy/
│   │   ├── scorer.py              # 3-Layer ASA-V1.ethics scoring engine
│   │   ├── macro_delta.py         # Cognitive delta for non-NEPSE assets
│   │   └── policy.py             # Typed IPS configuration loader (Pydantic)
│   ├── portfolio/
│   │   ├── engine.py              # Per-profile PortfolioEngine (cash, holdings, liabilities)
│   │   ├── position_sizer.py      # Constitutional position sizing with hard limits
│   │   ├── leverage_manager.py    # Borrow/Repay based on yield vs. cost of capital
│   │   └── transaction.py         # NEPSE transaction cost model (broker, SEBON, DP)
│   ├── decision/
│   │   ├── pipeline.py            # Core brain: threshold triage → sizer → VirtualExecutor
│   │   └── executor.py            # VirtualExecutor: builds tx, updates portfolio, logs ledger
│   ├── governance/
│   │   └── reflection.py          # AI self-reflection, win/loss post-mortems, win-rate
│   └── export/
│       └── json_bridge.py         # Exports all state to website/data/*.json
│
├── website/                       # GitHub Pages investor portal
│   ├── index.html                 # Overview / hero dashboard
│   ├── portfolio.html             # Live holdings and sector breakdown
│   ├── performance.html           # Comparative NAV trajectory charts
│   ├── decisions.html             # AI decision feed with reasoning memos
│   ├── journal.html               # Win/loss post-mortems and AI accuracy log
│   ├── strategy.html              # IPS constitution and compliance audit
│   ├── financials.html            # Balance sheet and income statement
│   ├── reports.html               # Monthly CEO reports
│   ├── about.html                 # Governance matrix and research framework
│   ├── css/style.css
│   ├── js/
│   │   ├── app.js                 # Data loader, clock renderer, live staleness detection
│   │   ├── charts.js              # Chart.js NAV and sector allocation charts
│   │   └── utils.js               # Formatters (NPR, %, dates, badges)
│   └── data/                      # Auto-generated JSON (committed by CI every trading day)
│       ├── clocks.json            # Market time, AI last run, live/stale status
│       ├── company.json           # NAV, total assets, return, status
│       ├── portfolio.json         # Active holdings, sector weights
│       ├── decisions.json         # All AI decisions with scores and reasoning
│       ├── transactions.json      # Executed virtual trades
│       ├── compliance.json        # 6-rule constitutional audit results
│       ├── benchmarks.json        # Comparative portfolio performance data
│       ├── financials.json        # Balance sheet and income statement
│       ├── journal.json           # AI self-reflection entries and win-rate
│       └── profile_race.json      # 4-portfolio comparative race data
│
├── tests/                         # pytest unit tests
├── .github/workflows/
│   └── daily_cycle.yml            # Daily autonomous CI pipeline (Sun–Thu 09:30 UTC)
└── pyproject.toml
```

---

## Quickstart

```bash
# Clone
git clone https://github.com/Ninjafunz/alpha-nepal-capital.git
cd alpha-nepal-capital

# Install
pip install -e .

# Run the full autonomous daily cycle locally
python -m src.cli run-daily

# Or use the CLI entry point
alpha-nepal run-daily
```

### CLI Reference

| Command | Description |
|---|---|
| `alpha-nepal run-daily` | Full daily cycle: ingest → score → threshold → execute → export |
| `alpha-nepal status` | Portfolio holdings, sector weights, P&L, NAV |
| `alpha-nepal compliance` | Rule-by-rule constitutional audit |
| `alpha-nepal decisions` | Recent AI decisions with cognitive delta scores |
| `alpha-nepal benchmark` | 4-portfolio comparative return, Sharpe, drawdown |
| `alpha-nepal export-json` | Export database state to `website/data/*.json` |

---

## GitHub Pages Setup

1. Push to a **public GitHub repository**.
2. Go to **Settings → Pages → Build and deployment → Source** → set to **GitHub Actions**.
3. The `daily_cycle.yml` workflow will automatically:
   - Run every trading day (Sun–Thu, 09:30 UTC)
   - Execute the full investment cycle
   - Commit updated `website/data/*.json`
   - Redeploy the GitHub Pages investor portal

---

## Disclaimer

This project is **strictly for academic research and educational purposes**.

- All trading activity is **virtual and simulated**. No real money is managed.
- NEPSE price data is used under fair use for non-commercial research.
- This is **not financial advice**. Nothing in this repository should be construed as a recommendation to buy, sell, or hold any security.
- The human founder retains all intellectual property rights over the ASA-V1.ethics investment philosophy and strategy architecture.

---

## License

© 2026 Ninjafunz (Alpha Nepal Capital Founder). All rights reserved.

This project is licensed under the **Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License**.

See [LICENSE](LICENSE) for full terms.
