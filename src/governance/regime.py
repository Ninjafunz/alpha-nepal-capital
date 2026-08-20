"""Market Regime and Kondratiev Phase Monitor."""
from typing import Dict, Any, List
from src.data.models import MarketRegime
from src.strategy.policy import InvestmentPolicy
from src.strategy.kondratiev import KondratievMirror


class RegimeManager:
    """Combines short-term technical regimes with long-term Kondratiev macro alignment."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.mirror = KondratievMirror(policy)

    def get_regime_summary(self, current_regime: MarketRegime) -> Dict[str, Any]:
        macro = self.mirror.get_macro_state()
        return {
            "current_technical_regime": current_regime.value,
            "kondratiev_macro_phase": macro["active_phase"],
            "historical_twin": macro["twin_period"],
            "priority_sectors": macro["priority_sectors"],
            "strategic_implication": macro["strategic_implication"],
        }
