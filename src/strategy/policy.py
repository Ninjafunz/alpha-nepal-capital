"""Investment Policy Statement (IPS) loader and typed configuration."""
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ProfileConfig(BaseModel):
    id: str
    name: str
    currency: str
    starting_capital: float
    asset_class: str


class CompanyData(BaseModel):
    name: str = "Alpha Nepal Capital"
    founded: str = "2026-08-20"
    autonomy_level: int = 3
    total_shares_issued: float = 10000000.0


class CompanyConfig(BaseModel):
    company: CompanyData = CompanyData()
    profiles: List[ProfileConfig] = []


class EquitiesSAA(BaseModel):
    total_pct: float = 40.0
    domestic_nepse_pct: float = 20.0
    global_etfs_pct: float = 20.0


class GoldSAA(BaseModel):
    total_pct: float = 20.0
    physical_proxy_target_pct: float = 65.0


class DigitalAssetsSAA(BaseModel):
    total_pct: float = 15.0
    btc_target_pct: float = 10.0
    eth_target_pct: float = 5.0


class FXAndCashSAA(BaseModel):
    total_pct: float = 25.0
    npr_cash_pct: float = 15.0
    usd_cash_pct: float = 10.0


class SAAConfig(BaseModel):
    equities: EquitiesSAA = EquitiesSAA()
    gold_and_metals: GoldSAA = GoldSAA()
    digital_assets: DigitalAssetsSAA = DigitalAssetsSAA()
    fx_and_cash: FXAndCashSAA = FXAndCashSAA()


class CurrencyRiskConfig(BaseModel):
    max_usd_exposure_pct: float = 40.0
    auto_hedge_ratio_pct: float = 50.0
    npr_appreciation_hedge_trigger_pct: float = 5.0


class VolatilityOverrideConfig(BaseModel):
    crypto_vol_threshold_pct: float = 80.0
    crypto_size_reduction_pct: float = 50.0
    crypto_vol_target_band: List[float] = [30.0, 60.0]
    max_portfolio_volatility_ex_crypto_pct: float = 15.0


class LiquidityOverrideConfig(BaseModel):
    min_global_daily_volume_usd: float = 10000000.0
    illiquid_max_nav_pct: float = 5.0


class ConcentrationLimitsConfig(BaseModel):
    max_single_equity_pct: float = 5.0
    max_single_crypto_pct: float = 3.0
    max_single_commodity_pct: float = 15.0


class UnifiedRiskOverridesConfig(BaseModel):
    currency_risk: CurrencyRiskConfig = CurrencyRiskConfig()
    volatility_override: VolatilityOverrideConfig = VolatilityOverrideConfig()
    liquidity_override: LiquidityOverrideConfig = LiquidityOverrideConfig()
    concentration_limits: ConcentrationLimitsConfig = ConcentrationLimitsConfig()


class CryptoProtocolConfig(BaseModel):
    absolute_hard_cap_pct: float = 20.0
    max_unregulated_exchange_pct: float = 5.0
    max_unclear_sec_tokens_pct: float = 3.0
    kyc_aml_auto_liquidate_hours: int = 24


class GoldProtocolConfig(BaseModel):
    absolute_hard_cap_pct: float = 30.0
    min_physical_custody_audit_pct: float = 50.0
    allow_leveraged_derivatives: bool = False


class GlobalEquitiesProtocolConfig(BaseModel):
    max_single_non_us_country_pct: float = 25.0
    max_defense_weapons_pct: float = 5.0
    esg_thermal_coal_revenue_cutoff_pct: float = 10.0


class FXProtocolConfig(BaseModel):
    max_usd_allocation_pct: float = 50.0
    min_cash_reserve_pct: float = 5.0


class SpecialGovernanceProtocolsConfig(BaseModel):
    crypto: CryptoProtocolConfig = CryptoProtocolConfig()
    gold: GoldProtocolConfig = GoldProtocolConfig()
    global_equities: GlobalEquitiesProtocolConfig = GlobalEquitiesProtocolConfig()
    fx_cash: FXProtocolConfig = FXProtocolConfig()


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
    min_delta_threshold_pct: float = 20.0
    aggressive_delta_threshold_pct: float = 40.0
    bias_penalty_narrative: float = 0.35
    bias_penalty_anchoring: float = 0.35
    bias_penalty_recency: float = 0.30


class PortfolioConstraints(BaseModel):
    max_single_position_pct: float = 5.0
    max_sector_pct: float = 40.0
    min_cash_pct: float = 5.0
    max_cash_pct: float = 50.0
    defensive_cash_pct: float = 30.0
    max_positions: int = 25
    min_position_size_pct: float = 1.0
    max_portfolio_volatility_annual: float = 15.0
    max_drawdown_warning_pct: float = 10.0
    max_drawdown_defensive_pct: float = 15.0
    max_drawdown_halt_pct: float = 20.0


class TransactionCosts(BaseModel):
    broker_commission_pct: float = 0.36
    sebon_fee_pct: float = 0.015
    dp_charge_npr: float = 25.0
    slippage_pct: float = 0.10


class LeverageConfig(BaseModel):
    enabled: bool = False
    max_leverage_ratio: float = 1.0
    margin_call_trigger_pct: float = -10.0
    borrowing_rate_spread_pct: float = 2.0


class InvestmentPolicy:
    """Loads, validates, and provides access to the Investment Policy Statement."""

    def __init__(self, policy_path: Optional[str] = None, company_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.policy_path = policy_path or str(base_dir / "config" / "investment_policy.yaml")
        self.company_path = company_path or str(base_dir / "config" / "company_profile.yaml")

        self._load_policy()

    def _load_policy(self):
        with open(self.company_path, "r", encoding="utf-8") as f:
            company_data = yaml.safe_load(f)
            
        with open(self.policy_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.raw_data = data
        self.company = CompanyConfig(**company_data)
        
        self.investment_objective = data.get("investment_objective", "")
        self.saa = SAAConfig(**data.get("strategic_asset_allocation", {}))
        self.unified_risk = UnifiedRiskOverridesConfig(**data.get("unified_risk_overrides", {}))
        self.special_governance = SpecialGovernanceProtocolsConfig(**data.get("special_governance_protocols", {}))
        self.macro_framework = data.get("macro_regime_framework", {})
        
        self.structural_variables = StructuralWeights(**data.get("structural_variables", {}))
        self.kondratiev = KondratievConfig(**data.get("kondratiev_macro_mapping", {}))
        self.literature_audit = LiteratureAuditConfig(**data.get("literature_audit", {}))
        self.cognitive_delta = CognitiveDeltaConfig(**data.get("cognitive_delta", {}))
        self.constraints = PortfolioConstraints(**data.get("portfolio_constraints", {}))
        self.transaction_costs = TransactionCosts(**data.get("transaction_costs", {}))
        self.routes_config = data.get("strategic_routes", {})
        self.universe_config = data.get("investment_universe", {})
        self.status_thresholds = data.get("company_status_thresholds", {})
        self.leverage = LeverageConfig(**data.get("leverage", {}))
