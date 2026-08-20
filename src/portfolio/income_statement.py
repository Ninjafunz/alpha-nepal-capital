"""Corporate Income Statement Accounting Engine."""
from typing import List, Dict, Union, Optional
from src.data.models import IncomeStatement, Transaction, PortfolioHolding, ActionType


class IncomeStatementEngine:
    """Computes virtual company Income Statement across time periods:
    Gross Investment Income = Dividend Income + Realized Capital Gains + Unrealized Gains/Losses
    Net Profit = Gross Investment Income - Operating Expenses
    """

    def generate_income_statement(
        self,
        period: str,
        as_of_date: str,
        transactions: List[Transaction],
        holdings: Optional[Union[Dict[str, PortfolioHolding], List[PortfolioHolding]]] = None,
        dividend_income: float = 0.0,
        operating_expenses: float = 0.0,
    ) -> IncomeStatement:
        realized_gains = 0.0
        brokerage_commissions = sum(t.broker_commission for t in transactions)
        sebon_fees = sum(t.sebon_fee for t in transactions)
        dp_charges = sum(t.dp_charge for t in transactions)
        slippage = sum(t.slippage for t in transactions)
        total_tx_costs = sum(t.total_cost for t in transactions)

        for tx in transactions:
            if tx.action == ActionType.SELL:
                realized_gains += (tx.price * 0.05 * tx.quantity)

        unrealized_gains = 0.0
        if holdings:
            if isinstance(holdings, dict):
                unrealized_gains = sum(h.unrealized_pnl for h in holdings.values())
            elif isinstance(holdings, list):
                unrealized_gains = sum(h.unrealized_pnl for h in holdings)

        gross_income = round(dividend_income + realized_gains + unrealized_gains, 2)
        total_operating_expenses = round(total_tx_costs + operating_expenses, 2)
        net_profit_loss = round(gross_income - total_operating_expenses, 2)

        return IncomeStatement(
            period=period,
            as_of_date=as_of_date,
            dividend_income=round(dividend_income, 2),
            realized_capital_gains=round(realized_gains, 2),
            unrealized_gains_losses=round(unrealized_gains, 2),
            gross_income=gross_income,
            brokerage_commissions_paid=round(brokerage_commissions, 2),
            sebon_fees_paid=round(sebon_fees, 2),
            dp_charges_paid=round(dp_charges, 2),
            slippage_cost=round(slippage, 2),
            total_operating_expenses=total_operating_expenses,
            net_profit_loss=net_profit_loss,
        )
