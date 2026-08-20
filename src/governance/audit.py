"""Audit Trail Inspector & Query Engine."""
from typing import List, Dict, Any, Optional
from src.data.store import DataStore
from src.data.models import Transaction, Decision


class AuditTrail:
    """Provides structured search & inspection over the immutable transaction and decision ledgers."""

    def __init__(self, store: DataStore):
        self.store = store

    def get_full_decision_ledger(self, symbol: Optional[str] = None) -> List[Decision]:
        decisions = self.store.get_recent_decisions(limit=200)
        if symbol:
            return [d for d in decisions if d.symbol.upper() == symbol.upper()]
        return decisions

    def get_full_transaction_ledger(self, symbol: Optional[str] = None) -> List[Transaction]:
        transactions = self.store.get_all_transactions()
        if symbol:
            return [t for t in transactions if t.symbol.upper() == symbol.upper()]
        return transactions
