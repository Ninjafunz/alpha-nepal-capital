"""Core Portfolio State Engine ('Economic Memory') for Alpha Global Capital."""
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.data.models import (
    Stock,
    PriceBar,
    PortfolioHolding,
    Transaction,
    ActionType,
    StrategicRoute,
    BalanceSheet,
    IncomeStatement,
    PortfolioSnapshot,
)
from src.strategy.policy import InvestmentPolicy
from src.portfolio.balance_sheet import BalanceSheetEngine
from src.portfolio.income_statement import IncomeStatementEngine
from src.portfolio.nav import NAVEngine


class PortfolioEngine:
    """Maintains active economic memory of a single investment profile."""

    def __init__(self, policy: InvestmentPolicy, profile_id: str, initial_cash: Optional[float] = None):
        self.policy = policy
        self.profile_id = profile_id
        
        # Find the starting capital for this profile
        profile = next((p for p in policy.company.profiles if p.id == profile_id), None)
        default_cash = profile.starting_capital if profile else 0.0
        
        self.cash = initial_cash if initial_cash is not None else default_cash
        self.liabilities = 0.0
        self.holdings: Dict[str, PortfolioHolding] = {}
        self.balance_sheet_engine = BalanceSheetEngine(policy)
        self.income_statement_engine = IncomeStatementEngine()
        self.nav_engine = NAVEngine(policy)

    def mark_to_market(self, latest_prices: Dict[str, PriceBar], stock_meta: Dict[str, Stock]):
        """Updates portfolio valuation, weights, and unrealized P&L from latest market prices."""
        total_invested = 0.0
        
        for symbol, holding in list(self.holdings.items()):
            if symbol in latest_prices:
                bar = latest_prices[symbol]
                holding.current_price = bar.close
                holding.current_value = round(holding.quantity * bar.close, 2)
                holding.unrealized_pnl = round(holding.current_value - holding.cost_basis, 2)
                holding.unrealized_pnl_pct = round((holding.unrealized_pnl / holding.cost_basis) * 100.0, 2) if holding.cost_basis > 0 else 0.0
                total_invested += holding.current_value

        total_assets = self.cash + total_invested
        for holding in self.holdings.values():
            holding.weight_pct = round((holding.current_value / max(1.0, total_assets)) * 100.0, 2)

    def execute_transaction(self, tx: Transaction, stock: Optional[Stock] = None):
        """Applies an executed transaction to the internal cash, liabilities, and holdings state."""
        if tx.action == ActionType.BUY:
            self.cash = round(self.cash - tx.net_value, 2)
            if tx.symbol in self.holdings:
                h = self.holdings[tx.symbol]
                new_qty = h.quantity + tx.quantity
                new_cost = round(h.cost_basis + tx.net_value, 2)
                h.quantity = new_qty
                h.cost_basis = new_cost
                h.avg_buy_price = round(new_cost / new_qty, 2)
            else:
                sector = stock.sector if stock else "Unknown"
                self.holdings[tx.symbol] = PortfolioHolding(
                    symbol=tx.symbol,
                    sector=sector,
                    quantity=tx.quantity,
                    avg_buy_price=tx.price,
                    current_price=tx.price,
                    cost_basis=tx.net_value,
                    current_value=tx.gross_value,
                    weight_pct=0.0,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0,
                    route=tx.route,
                    profile_id=self.profile_id
                )
        elif tx.action == ActionType.SELL:
            self.cash = round(self.cash + tx.net_value, 2)
            if tx.symbol in self.holdings:
                h = self.holdings[tx.symbol]
                if tx.quantity >= h.quantity:
                    del self.holdings[tx.symbol]
                else:
                    portion = tx.quantity / h.quantity
                    h.quantity -= tx.quantity
                    h.cost_basis = round(h.cost_basis * (1.0 - portion), 2)
        elif tx.action == "BORROW":
            self.cash = round(self.cash + tx.gross_value, 2)
            self.liabilities = round(self.liabilities + tx.gross_value, 2)
        elif tx.action == "REPAY":
            self.cash = round(self.cash - tx.gross_value, 2)
            self.liabilities = round(max(0.0, self.liabilities - tx.gross_value), 2)

    def get_total_assets(self) -> float:
        invested = sum(h.current_value for h in self.holdings.values())
        return round(self.cash + invested, 2)
        
    def get_equity(self) -> float:
        return round(self.get_total_assets() - self.liabilities, 2)

    def get_sector_exposures(self) -> Dict[str, float]:
        total_assets = self.get_total_assets()
        exposures: Dict[str, float] = {}
        for h in self.holdings.values():
            exposures[h.sector] = exposures.get(h.sector, 0.0) + h.current_value
        return {sec: round((val / max(1.0, total_assets)) * 100.0, 2) for sec, val in exposures.items()}

    def get_balance_sheet(self, as_of_date: str) -> BalanceSheet:
        # Override BalanceSheetEngine to inject liabilities
        bs = self.balance_sheet_engine.generate_balance_sheet(as_of_date, self.cash, self.holdings)
        bs.profile_id = self.profile_id
        bs.total_liabilities = self.liabilities
        bs.shareholder_equity = round(bs.total_assets - self.liabilities, 2)
        
        profile = next((p for p in self.policy.company.profiles if p.id == self.profile_id), None)
        starting_cap = profile.starting_capital if profile else 0.0
        bs.retained_earnings = round(bs.shareholder_equity - starting_cap, 2)
        return bs

    def get_income_statement(self, period: str, as_of_date: str, tx_list: List[Transaction]) -> IncomeStatement:
        iso = self.income_statement_engine.generate_income_statement(period, as_of_date, tx_list, self.holdings)
        iso.profile_id = self.profile_id
        return iso
