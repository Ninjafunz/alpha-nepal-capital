"""Tests for portfolio engine, balance sheet, and transaction costs."""
import pytest
from src.strategy.policy import InvestmentPolicy
from src.portfolio.engine import PortfolioEngine
from src.portfolio.transaction import TransactionEngine
from src.data.models import Stock, Transaction, ActionType, StrategicRoute


def test_balance_sheet_identity():
    policy = InvestmentPolicy()
    portfolio = PortfolioEngine(policy, initial_cash=100000000.0)
    
    bs = portfolio.get_balance_sheet("2026-08-20")
    # Total Assets = Liabilities + Shareholder Equity
    assert bs.total_assets == 100000000.0
    assert bs.total_liabilities == 0.0
    assert bs.shareholder_equity == 100000000.0
    assert bs.nav_per_share == 10.0


def test_realistic_nepse_transaction_costs():
    policy = InvestmentPolicy()
    tx_engine = TransactionEngine(policy)
    
    # Buy 1,000 shares @ NPR 500 = Gross NPR 500,000
    costs = tx_engine.calculate_trade_costs(ActionType.BUY, 1000, 500.0)
    assert costs["gross_value"] == 500000.0
    assert costs["broker_commission"] == 1800.0  # 0.36% of 500,000
    assert costs["sebon_fee"] == 75.0            # 0.015% of 500,000
    assert costs["dp_charge"] == 0.0             # Buy has zero DP charge
    assert costs["total_cost"] == 2375.0         # 1800 + 75 + 500 slippage (0.1%)
    assert costs["net_value"] == 502375.0

    # Sell 1,000 shares @ NPR 500
    costs_sell = tx_engine.calculate_trade_costs(ActionType.SELL, 1000, 500.0)
    assert costs_sell["dp_charge"] == 25.0       # NPR 25 DP fee on sell
    assert costs_sell["net_value"] < 500000.0
