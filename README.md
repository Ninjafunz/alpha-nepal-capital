# Alpha Nepal Capital — AI-Managed Virtual Investment Company

[![GitHub Actions](https://github.com/username/alpha-nepal-capital/actions/workflows/daily_cycle.yml/badge.svg)](https://github.com/username/alpha-nepal-capital/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Strategy: ASA-V1.ethics](https://img.shields.io/badge/Strategy-ASA--V1.ethics-blue.svg)](config/investment_policy.yaml)
[![Status: FLOURISHING](https://img.shields.io/badge/Status-FLOURISHING-00d26a.svg)](https://username.github.io/alpha-nepal-capital)

> *"Can a human-designed investment strategy, autonomously executed by an AI-managed virtual investment company using real-time market information, generate sustainable risk-adjusted returns in the Nepalese equity market?"*

**Live Public Investor Portal:** [https://username.github.io/alpha-nepal-capital](https://username.github.io/alpha-nepal-capital)

---

## 1. Executive Summary & Concept

Alpha Nepal Capital is founded as a **virtual investment company** with **NPR 100,000,000 in starting capital** and **10,000,000 virtual shares** at a par Net Asset Value (NAV) of **NPR 10.00 / share**.

* **The Founder / Chief Strategist (You):** Defines the core investment philosophy, constitutional risk boundaries, eligible sectors, position sizing rules, and cognitive delta criteria.
* **The AI Management Team:** Operates autonomously (Level 3 Autonomy) to monitor real-time NEPSE data, screen opportunities, calculate 3-layer investment scores, size positions, execute virtual trades against an immutable ledger, and publish daily/monthly reports.
* **The Website:** Functions as the public investor-relations portal, rendering live balance sheets, interactive NAV charts, AI decision streams, and compliance audits directly from committed JSON data.

---

## 2. The ASA-V1.ethics Investment Constitution

```
Every investment vehicle is governed by exactly four structural forces and one cognitive gap.
Profits are found in the velocity of mispricing between academic consensus and physical reality.
Ethics are the longest-duration call option on regulatory goodwill.
```

### The 3-Layer Scoring Model:
1. **Layer 1: Structural Anchoring (35% Weight)**
   * Capital Velocity (Liquidity flow, credit spreads, 90-day momentum)
   * Physical / Operational Risk (Supply chain resilience, NPL, hydro water flow/PPA)
   * Transition / Regulatory Risk (NRB directives, SEBON policy, tax tailwinds)
   * Bottleneck Asymmetry (Inelastic levers, steep marginal cost advantage)
2. **Layer 2: Theoretical Literature Audit (30% Weight)**
   * Elite Theory (Kondratiev macro alignment)
   * Prospect Theory (The "Mispriced Middle" between fear and greed)
   * Real Options (Unpriced asset optionality)
   * Regulatory Capture ("Golden Zone" dynamics)
3. **Layer 3: Cognitive Delta Engine (35% Weight)**
   * Three-Bias Check: Narrative Bias, Anchoring Bias, Recency Bias
   * Intrinsic Value vs. Market Price: Requires **Delta > 30%** to deploy capital

### The 3 Execution Routes:
* **Route Alpha (Defensive Moat):** Insulated infrastructure & sovereign-backed cash flows (60% target)
* **Route Beta (Contra-Cyclical Raid):** Deep value turnaround plays with D/E > 2x & beaten-down P/E (25% target)
* **Route Gamma (Policy Hack):** Exceeding regulatory compliance standards by 20%+ (15% target)

---

## 3. Four-Portfolio Experimental Control Group

To objectively determine whether AI execution adds value, four portfolios are tracked in parallel:

| Portfolio | Strategy Type | Autonomous AI? | Description |
|---|---|:---:|---|
| **Alpha Nepal Capital** | **ASA-V1.ethics** | **Yes** | AI dynamically sizes and allocates based on structural deltas |
| **Human Static** | Fixed Asset Allocation | No | Static pre-set allocation (40% Bank, 40% Hydro, 20% Cash) |
| **NEPSE Index** | Passive Market | No | Buy-and-hold the NEPSE Composite Index |
| **Equal-Weight** | Naive Quantitative | No | Equal allocation across top 10 universe stocks |

---

## 4. Installation & Quickstart

```bash
# Clone the repository
git clone https://github.com/username/alpha-nepal-capital.git
cd alpha-nepal-capital

# Install Python dependencies using uv or pip
pip install -e .

# Run the complete autonomous daily cycle
alpha-nepal run-daily

# View current company status and balance sheet
alpha-nepal status

# Check constitutional strategy compliance score
alpha-nepal compliance

# View recent AI decision memos
alpha-nepal decisions

# Compare performance against the 4 benchmarks
alpha-nepal benchmark
```

---

## 5. CLI Command Reference

| Command | Description |
|---|---|
| `alpha-nepal run-daily` | Ingests NEPSE data, runs decision pipeline, executes trades, snapshots NAV, exports JSON |
| `alpha-nepal status` | Displays active portfolio holdings, sector weights, P&L, and NAV |
| `alpha-nepal balance-sheet` | Prints audited company balance sheet |
| `alpha-nepal compliance` | Evaluates rule-by-rule obedience against the IPS Constitution |
| `alpha-nepal decisions` | Lists recent AI decisions with structural scores and cognitive delta % |
| `alpha-nepal benchmark` | Displays comparative return, volatility, Sharpe ratio, and drawdown tables |
| `alpha-nepal export-json` | Exports database state into `website/data/*.json` |
| `alpha-nepal report-monthly` | Generates permanent monthly CEO executive report |

---

## 6. GitHub Pages & Automated Actions

1. Push this repository to GitHub as a **public repository**.
2. Go to **Settings > Pages** and set source to **GitHub Actions**.
3. The `.github/workflows/daily_cycle.yml` workflow will automatically run every trading day (Sun–Thu at 3:15 PM NPT), execute the daily investment cycle, commit the updated `website/data/*.json`, and trigger a live GitHub Pages deployment.
