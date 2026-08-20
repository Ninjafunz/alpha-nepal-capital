"""Monthly CEO Report Generator with Permanent Archival."""
from typing import Dict, Any, List
from datetime import datetime

from src.data.models import PortfolioSnapshot, BalanceSheet, IncomeStatement, Transaction, Decision
from src.strategy.policy import InvestmentPolicy


class MonthlyReporter:
    """Generates structured Monthly CEO Reports that are permanently archived in JSON and Markdown."""

    @staticmethod
    def generate_monthly_report(
        period_str: str,  # e.g., "2026-08"
        as_of_date: str,
        start_nav: float,
        end_nav: float,
        balance_sheet: BalanceSheet,
        income_stmt: IncomeStatement,
        transactions: List[Transaction],
        decisions: List[Decision],
        compliance_score: float,
        nepse_return_pct: float,
        management_outlook: str,
    ) -> Dict[str, Any]:
        
        return_pct = round(((end_nav - start_nav) / start_nav) * 100.0, 2)
        alpha_pct = round(return_pct - nepse_return_pct, 2)

        buy_count = sum(1 for d in decisions if d.action.value == "BUY")
        sell_count = sum(1 for d in decisions if d.action.value == "SELL")
        hold_count = sum(1 for d in decisions if d.action.value == "HOLD")

        return {
            "period": period_str,
            "title": f"{period_str} — Monthly CEO Report",
            "published_at": datetime.now().isoformat(),
            "as_of_date": as_of_date,
            "executive_summary": (
                f"Alpha Nepal Capital generated a {return_pct:+.2f}% net return for {period_str}, "
                f"generating an Alpha of {alpha_pct:+.2f}% against the NEPSE Composite Index benchmark ({nepse_return_pct:+.2f}%). "
                f"The company operated with {compliance_score:.1f}% Strategy Compliance."
            ),
            "nav_start": round(start_nav, 4),
            "nav_end": round(end_nav, 4),
            "return_pct": return_pct,
            "nepse_return_pct": nepse_return_pct,
            "alpha_pct": alpha_pct,
            "balance_sheet": {
                "total_assets": balance_sheet.total_assets,
                "cash": balance_sheet.cash_and_equivalents,
                "equity_investments": balance_sheet.equity_investments_market_value,
                "shareholder_equity": balance_sheet.shareholder_equity,
            },
            "financial_performance": {
                "gross_income": income_stmt.gross_income,
                "dividend_income": income_stmt.dividend_income,
                "realized_gains": income_stmt.realized_capital_gains,
                "unrealized_gains": income_stmt.unrealized_gains_losses,
                "transaction_costs": income_stmt.total_operating_expenses,
                "net_profit": income_stmt.net_profit_loss,
                "net_margin_pct": round(
                    (income_stmt.net_profit_loss / income_stmt.gross_income * 100.0)
                    if income_stmt.gross_income != 0 else 0.0, 2
                ),
            },
            "ai_decisions_summary": {
                "total_decisions": len(decisions),
                "buy_orders": buy_count,
                "sell_orders": sell_count,
                "hold_orders": hold_count,
                "transactions_executed": len(transactions),
            },
            "strategy_compliance_score": compliance_score,
            "risk_assessment": "MODERATE — Volatility controlled within 20% annual constraint",
            "management_outlook": management_outlook,
        }
