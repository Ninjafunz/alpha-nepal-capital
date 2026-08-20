"""Investment Policy Statement (IPS) loader and typed configuration."""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class CompanyConfig(BaseModel):
    name: str = "Alpha Nepal Capital"
    founded: str = "2026-08-20"
    starting_capital: float = 100000000.0
    shares_outstanding: float = 10000000.0
    starting_nav: float = 10.0
    currency: str = "NPR"
    autonomy_level: int = 3


class StructuralWeights(BaseModel):
    capital_velocity_weight: float = 0.25
    physical_operational_weight: float = 0.25
    regulatory_transition_weight: float = 0.25
    bottleneck_asymmetry_weight: float = 0.25


class KondratievConfig(BaseModel):
    active_phase: str = "Reflationary"
    twin_period: str = "1945-1950"
    priority_sectors: List[str] = Field(default_factory=list)


class LiteratureAuditConfig(BaseModel):
    elite_alignment_weight: float = 0.25
    sentiment_position_weight: float = 0.25
    real_options_weight: float = 0.25
    golden_zone_weight: float = 0.25
    max_fair_value_sigma: float = 1.5


class CognitiveDeltaConfig(BaseModel):
    min_delta_threshold_pct: float = 30.0
    aggressive_delta_threshold_pct: float = 50.0
    bias_penalty_narrative: float = 0.35
    bias_penalty_anchoring: float = 0.35
    bias_penalty_recency: float = 0.30


class PortfolioConstraints(BaseModel):
    max_single_position_pct: float = 25.0
    max_sector_pct: float = 40.0
    min_cash_pct: float = 5.0
    max_cash_pct: float = 50.0
    defensive_cash_pct: float = 30.0
    max_positions: int = 15
    min_position_size_pct: float = 2.0
    max_portfolio_volatility_annual: float = 20.0
    max_drawdown_warning_pct: float = 10.0
    max_drawdown_defensive_pct: float = 15.0
    max_drawdown_halt_pct: float = 25.0


class TransactionCosts(BaseModel):
    broker_commission_pct: float = 0.36
    sebon_fee_pct: float = 0.015
    dp_charge_npr: float = 25.0
    slippage_pct: float = 0.10


class InvestmentPolicy:
    """Loads, validates, and provides access to the Investment Policy Statement."""

    def __init__(self, policy_path: Optional[str] = None):
        if policy_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.policy_path = str(base_dir / "config" / "investment_policy.yaml")
        else:
            self.policy_path = policy_path

        self._load_policy()

    def _load_policy(self):
        with open(self.policy_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.raw_data = data
        self.company = CompanyConfig(**data.get("company", {}))
        self.investment_objective = data.get("investment_objective", "")
        self.structural_variables = StructuralWeights(**data.get("structural_variables", {}))
        self.kondratiev = KondratievConfig(**data.get("kondratiev_macro_mapping", {}))
        self.literature_audit = LiteratureAuditConfig(**data.get("literature_audit", {}))
        self.cognitive_delta = CognitiveDeltaConfig(**data.get("cognitive_delta", {}))
        self.constraints = PortfolioConstraints(**data.get("portfolio_constraints", {}))
        self.transaction_costs = TransactionCosts(**data.get("transaction_costs", {}))
        self.routes_config = data.get("strategic_routes", {})
        self.universe_config = data.get("investment_universe", {})
        self.status_thresholds = data.get("company_status_thresholds", {})
