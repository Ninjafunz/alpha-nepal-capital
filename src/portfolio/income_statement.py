"""Corporate Income Statement Accounting Engine."""
from typing import List
from src.data.models import IncomeStatement, Transaction, PortfolioHolding, ActionType


class IncomeStatementEngine:
    """Computes virtual company Income Statement across time periods:
    Gross Investment Income = Dividend Income + Realized Capital Gains + Unrealized Gains/Losses
    Net Profit = Gross Investment Income - Transaction Costs - Operating Expenses
    """

    def generate_income_statement(
        self,
        period: str,
        as_of_date: str,
        transactions: List[Transaction],
        holdings_dict: dict,
        dividend_income: float = 0.0,
        operating_expenses: float = 0.0,
    ) -> IncomeStatement:
        realized_gains = 0.0
        total_tx_costs = sum(t.total_cost for t in transactions)

        # Calculate realized P&L on sell transactions
        for tx in transactions:
            if tx.action == ActionType.SELL:
                # Approximate gain from sell
                realized_gains += (tx.price * 0.05 * tx.quantity)

        # Unrealized gains/losses from current open holdings
        unrealized_gains = sum(h.unrealized_pnl for h in holdings_dict.values())

        gross_income = round(dividend_income + realized_gains + unrealized_gains, 2)
        net_profit = round(gross_income - total_tx_costs - operating_expenses, 2)
        net_margin = round((net_profit / max(1.0, gross_income)) * 100.0, 2) if gross_income != 0 else 0.0

        return IncomeStatement(
            period=period,
            as_of_date=as_of_date,
            dividend_income=round(dividend_income, 2),
            realized_capital_gains=round(realized_gains, 2),
            unrealized_gains_losses=round(unrealized_gains, 2),
            gross_investment_income=gross_income,
            transaction_costs=round(total_tx_costs, 2),
            operating_expenses=round(operating_expenses, 2),
            net_profit=net_profit,
            net_margin_pct=net_margin,
        )
