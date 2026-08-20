"""Corporate Balance Sheet Accounting Engine."""
from typing import Dict, List
from src.data.models import BalanceSheet, PortfolioHolding
from src.strategy.policy import InvestmentPolicy


class BalanceSheetEngine:
    """Computes virtual company Balance Sheet:
    Total Assets = Cash + Equity Investments (Market Value) + Dividends Receivable
    Total Liabilities = 0.0 (Zero initial borrowing)
    Shareholder Equity = Total Assets - Total Liabilities
    NAV per Share = Shareholder Equity / Shares Outstanding
    """

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.shares_outstanding = policy.company.company.total_shares_issued

    def generate_balance_sheet(
        self,
        as_of_date: str,
        cash: float,
        holdings: Dict[str, PortfolioHolding],
        dividends_receivable: float = 0.0,
    ) -> BalanceSheet:
        equity_investments = sum(h.current_value for h in holdings.values())
        total_assets = round(cash + equity_investments + dividends_receivable, 2)
        total_liabilities = 0.0  # Zero initial debt
        shareholder_equity = round(total_assets - total_liabilities, 2)
        nav_per_share = round(shareholder_equity / self.shares_outstanding, 4)

        return BalanceSheet(
            as_of_date=as_of_date,
            cash_and_equivalents=round(cash, 2),
            equity_investments_market_value=round(equity_investments, 2),
            dividends_receivable=round(dividends_receivable, 2),
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            shareholder_equity=shareholder_equity,
            shares_outstanding=self.shares_outstanding,
            nav_per_share=nav_per_share,
        )
