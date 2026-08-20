"""Kondratiev Macro Phase Mapping & Historical Twinning."""
from typing import Dict, Any
from src.strategy.policy import InvestmentPolicy


class KondratievMirror:
    """Matches macro-regimes to historical twins (1900, 1940, 1975, 2000, 2008)."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.config = policy.kondratiev

    def get_macro_state(self) -> Dict[str, Any]:
        return {
            "active_phase": self.config.active_phase,
            "twin_period": self.config.twin_period,
            "priority_sectors": self.config.priority_sectors,
            "strategic_implication": (
                "Post-war reconstruction twin matches infrastructure development. "
                "Priority allocated to hard generation assets (Hydropower), essential banking liquidity, "
                "and consumer manufacturing."
            ),
        }
