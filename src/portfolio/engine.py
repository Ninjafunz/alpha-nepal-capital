"""Core Portfolio State Engine ('Economic Memory') for Alpha Nepal Capital."""
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
    """Maintains active economic memory of the virtual investment company."""

    def __init__(self, policy: InvestmentPolicy, initial_cash: Optional[float] = None):
        self.policy = policy
        self.cash = initial_cash if initial_cash is not None else policy.company.starting_capital
        self.holdings: Dict[str, PortfolioHolding] = {}
        self.balance_sheet_engine = BalanceSheetEngine(policy)
        self.income_statement_engine = IncomeStatementEngine()
        self.nav_engine = NAVEngine(policy)

    def mark_to_market(self, latest_prices: Dict[str, PriceBar], stock_meta: Dict[str, Stock]):
        """Updates portfolio valuation, weights, and unrealized P&L from latest market prices."""
        total_invested = 0.0
        
        # Update each holding
        for symbol, holding in list(self.holdings.items()):
            if symbol in latest_prices:
                bar = latest_prices[symbol]
                holding.current_price = bar.close
                holding.current_value = round(holding.quantity * bar.close, 2)
                holding.unrealized_pnl = round(holding.current_value - holding.cost_basis, 2)
                holding.unrealized_pnl_pct = round((holding.unrealized_pnl / holding.cost_basis) * 100.0, 2) if holding.cost_basis > 0 else 0.0
                total_invested += holding.current_value

        total_assets = self.cash + total_invested
        # Re-compute portfolio weights
        for holding in self.holdings.values():
            holding.weight_pct = round((holding.current_value / max(1.0, total_assets)) * 100.0, 2)

    def execute_transaction(self, tx: Transaction, stock: Stock):
        """Applies an executed transaction to the internal cash and holdings state."""
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
                self.holdings[tx.symbol] = PortfolioHolding(
                    symbol=tx.symbol,
                    sector=stock.sector,
                    quantity=tx.quantity,
                    avg_buy_price=tx.price,
                    current_price=tx.price,
                    cost_basis=tx.net_value,
                    current_value=tx.gross_value,
                    weight_pct=0.0,
                    unrealized_pnl=0.0,
                    unrealized_pnl_pct=0.0,
                    route=tx.route,
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

    def get_total_assets(self) -> float:
        invested = sum(h.current_value for h in self.holdings.values())
        return round(self.cash + invested, 2)

    def get_sector_exposures(self) -> Dict[str, float]:
        total_assets = self.get_total_assets()
        exposures: Dict[str, float] = {}
        for h in self.holdings.values():
            exposures[h.sector] = exposures.get(h.sector, 0.0) + h.current_value
        return {sec: round((val / max(1.0, total_assets)) * 100.0, 2) for sec, val in exposures.items()}

    def get_balance_sheet(self, as_of_date: str) -> BalanceSheet:
        return self.balance_sheet_engine.generate_balance_sheet(as_of_date, self.cash, self.holdings)

    def get_income_statement(self, period: str, as_of_date: str, tx_list: List[Transaction]) -> IncomeStatement:
        return self.income_statement_engine.generate_income_statement(period, as_of_date, tx_list, self.holdings)
