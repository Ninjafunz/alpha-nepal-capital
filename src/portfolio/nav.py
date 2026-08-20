"""Net Asset Value (NAV) Calculation and Time Series Engine."""
from typing import List, Dict, Any
from src.data.models import PortfolioSnapshot, PortfolioHolding
from src.strategy.policy import InvestmentPolicy


class NAVEngine:
    """Calculates NAV per share and historical performance returns."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.shares_outstanding = policy.company.shares_outstanding
        self.starting_capital = policy.company.starting_capital
        self.starting_nav = policy.company.starting_nav

    def calculate_nav(self, total_assets: float, liabilities: float = 0.0) -> Dict[str, float]:
        equity = total_assets - liabilities
        nav_per_share = round(equity / self.shares_outstanding, 4)
        total_return_pct = round(((equity - self.starting_capital) / self.starting_capital) * 100.0, 2)

        return {
            "total_assets": round(total_assets, 2),
            "shareholder_equity": round(equity, 2),
            "nav_per_share": nav_per_share,
            "total_return_pct": total_return_pct,
        }
