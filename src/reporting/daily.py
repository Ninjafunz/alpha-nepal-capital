"""Daily Executive Performance Reporter."""
from typing import Dict, Any, List
from src.data.models import PortfolioSnapshot, BalanceSheet, IncomeStatement, Decision, Transaction
from src.strategy.policy import InvestmentPolicy


class DailyReporter:
    """Generates concise daily executive updates."""

    @staticmethod
    def generate_daily_markdown(
        snapshot: PortfolioSnapshot,
        balance_sheet: BalanceSheet,
        decisions: List[Decision],
        transactions: List[Transaction],
    ) -> str:
        buy_count = sum(1 for d in decisions if d.action.value == "BUY")
        sell_count = sum(1 for d in decisions if d.action.value == "SELL")
        hold_count = sum(1 for d in decisions if d.action.value == "HOLD")

        md = f"""# Alpha Nepal Capital — Daily Executive Briefing
**Trade Date:** {snapshot.trade_date} | **Generated:** {snapshot.timestamp}
**Company Status:** {snapshot.status.value} | **Market Regime:** {snapshot.market_regime.value}

---

## 1. Capital & NAV
* **Total Assets:** NPR {balance_sheet.total_assets:,.2f}
* **Cash Reserve:** NPR {balance_sheet.cash_and_equivalents:,.2f} ({snapshot.cash_weight_pct:.1f}%)
* **Current NAV per Share:** NPR {snapshot.nav_per_share:.4f}
* **Daily Return:** {snapshot.daily_return_pct:+.2f}%
* **Cumulative Return Since Inception:** {snapshot.cumulative_return_pct:+.2f}%
* **Max Drawdown from Peak:** {snapshot.drawdown_pct:.2f}%
* **Strategy Compliance Score:** {snapshot.compliance_score_pct:.1f}%

---

## 2. Autonomous AI Decisions
* **Total Decisions Today:** {len(decisions)} ({buy_count} BUY, {sell_count} SELL, {hold_count} HOLD)
* **Transactions Executed:** {len(transactions)}
"""
        if transactions:
            md += "\n### Executed Transactions:\n"
            for t in transactions:
                md += f"- **{t.action.value} {t.symbol}**: {t.quantity:,} shares @ NPR {t.price:,.2f} (Total: NPR {t.net_value:,.2f}) — *{t.reason}*\n"

        return md
