"""Virtual Trade Executor enforcing immutable ledger recording."""
from typing import Dict, Any, Optional
from src.data.models import Decision, Transaction, Stock, PriceBar, ActionType
from src.data.store import DataStore
from src.strategy.policy import InvestmentPolicy
from src.portfolio.engine import PortfolioEngine
from src.portfolio.transaction import TransactionEngine


class VirtualExecutor:
    """Executes validated AI decisions against the virtual portfolio and logs to immutable SQLite ledger."""

    def __init__(self, policy: InvestmentPolicy, store: DataStore, portfolio: PortfolioEngine):
        self.policy = policy
        self.store = store
        self.portfolio = portfolio
        self.tx_engine = TransactionEngine(policy)

    def execute_decision(
        self,
        decision: Decision,
        stock: Stock,
        price_bar: PriceBar,
    ) -> Optional[Transaction]:
        if not decision.executed or decision.action not in [ActionType.BUY, ActionType.SELL]:
            return None

        pre_cash = self.portfolio.cash
        total_assets = self.portfolio.get_total_assets()
        pre_nav = round(total_assets / self.policy.company.shares_outstanding, 4)

        tx = self.tx_engine.build_transaction(
            trade_date=decision.trade_date,
            symbol=decision.symbol,
            action=decision.action,
            quantity=decision.target_quantity,
            price=price_bar.close,
            pre_cash=pre_cash,
            pre_nav=pre_nav,
            route=decision.route,
            reason=decision.reason_summary,
            rule_ids=decision.applied_rules,
            confidence_pct=decision.confidence_pct,
            decision_id=decision.id,
        )

        # 1. Update Portfolio internal state
        self.portfolio.execute_transaction(tx, stock)

        # 2. Record to Immutable SQLite Ledger
        self.store.record_transaction(tx)

        return tx
