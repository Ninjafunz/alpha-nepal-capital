"""Domain data models for Alpha Nepal Capital."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum



class AssetClass(str, Enum):
    EQUITY_DOMESTIC = "EQUITY_DOMESTIC"
    EQUITY_GLOBAL = "EQUITY_GLOBAL"
    COMMODITY = "COMMODITY"
    CRYPTO = "CRYPTO"
    FOREX = "FOREX"

class ActionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    REBALANCE = "REBALANCE"
    BORROW = "BORROW"
    REPAY = "REPAY"


class StrategicRoute(str, Enum):
    ROUTE_ALPHA = "Route Alpha (Defensive Moat)"
    ROUTE_BETA = "Route Beta (Contra-Cyclical Raid)"
    ROUTE_GAMMA = "Route Gamma (Policy Hack)"
    UNASSIGNED = "Unassigned"


class CompanyStatus(str, Enum):
    FLOURISHING = "FLOURISHING"
    STABLE = "STABLE"
    DECLINING = "DECLINING"
    CRITICAL = "CRITICAL"


class MarketRegime(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"


@dataclass
class Stock:
    symbol: str
    name: str
    sector: str
    category: str = "A"
    paid_up_capital_cr: float = 0.0
    listed_shares: int = 0
    security_id: Optional[int] = None
    is_active: bool = True
    asset_class: AssetClass = AssetClass.EQUITY_DOMESTIC


@dataclass
class PriceBar:
    symbol: str
    trade_date: str  # YYYY-MM-DD
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: float
    prev_close: float = 0.0
    point_change: float = 0.0
    pct_change: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Fundamental:
    symbol: str
    as_of_date: str
    pe_ratio: float
    pb_ratio: float
    eps: float
    book_value: float
    roe: float
    dividend_yield_pct: float = 0.0
    debt_to_equity: float = 0.0
    promoter_holding_pct: float = 0.0
    public_holding_pct: float = 0.0


@dataclass
class Transaction:
    id: str
    timestamp: str
    trade_date: str
    symbol: str
    action: ActionType
    quantity: int
    price: float
    gross_value: float
    broker_commission: float
    sebon_fee: float
    dp_charge: float
    slippage: float
    total_cost: float
    net_value: float
    pre_trade_cash: float
    post_trade_cash: float
    pre_trade_nav: float
    post_trade_nav: float
    route: StrategicRoute
    reason: str
    rule_ids: List[str]
    confidence_pct: float
    decision_id: str

    profile_id: str = "P1_DOMESTIC_EQUITY"

@dataclass
class Decision:
    id: str = ""
    timestamp: str = ""
    trade_date: str = ""
    symbol: str = ""
    action: ActionType = ActionType.HOLD
    confidence_pct: float = 0.0
    target_quantity: int = 0
    estimated_price: float = 0.0
    capital_allocation_npr: float = 0.0
    route: StrategicRoute = StrategicRoute.UNASSIGNED
    
    # Layer 1: Structural
    structural_score: float = ""
    capital_velocity_score: float = 0.0
    physical_risk_score: float = 0.0
    regulatory_risk_score: float = 0.0
    bottleneck_score: float = 0.0
    
    # Layer 2: Literature Audit
    literature_score: float = 0.0
    elite_alignment_score: float = 0.0
    sentiment_score: float = 0.0
    optionality_score: float = 0.0
    golden_zone_score: float = 0.0
    
    # Layer 3: Cognitive Delta
    cognitive_delta_score: float = 0.0
    narrative_bias_score: float = 0.0
    anchoring_bias_score: float = 0.0
    recency_bias_score: float = 0.0
    intrinsic_value_est: float = 0.0
    delta_pct: float = 0.0
    
    # Combined Composite Score
    final_score: float = 0.0
    
    # Reasoning & Invalidation Condition
    reason_summary: str = ""
    applied_rules: List[str] = ""
    invalidation_condition: str = ""
    executed: bool = False

    profile_id: str = "P1_DOMESTIC_EQUITY"

@dataclass
class PortfolioHolding:
    symbol: str
    sector: str
    quantity: int
    avg_buy_price: float
    current_price: float
    cost_basis: float
    current_value: float
    weight_pct: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    route: StrategicRoute

    profile_id: str = "P1_DOMESTIC_EQUITY"

@dataclass
class BalanceSheet:
    as_of_date: str
    cash_and_equivalents: float
    equity_investments_market_value: float
    dividends_receivable: float
    total_assets: float
    total_liabilities: float
    shareholder_equity: float
    shares_outstanding: float
    nav_per_share: float

    profile_id: str = "P1_DOMESTIC_EQUITY"

@dataclass
class IncomeStatement:
    period: str
    as_of_date: str
    dividend_income: float
    realized_capital_gains: float
    unrealized_gains_losses: float
    gross_investment_income: float
    transaction_costs: float
    operating_expenses: float
    net_profit: float
    net_margin_pct: float

    profile_id: str = "P1_DOMESTIC_EQUITY"

@dataclass
class ComplianceRecord:
    id: str
    timestamp: str
    trade_date: str
    rule_id: str
    rule_name: str
    threshold_desc: str
    current_value: float
    limit_value: float
    passed: bool
    severity: str  # PASS, WARNING, BREACH, CRITICAL
    message: str


@dataclass
class PortfolioSnapshot:
    trade_date: str
    timestamp: str
    total_assets: float
    cash: float
    invested_value: float
    cash_weight_pct: float
    shares_outstanding: float
    nav_per_share: float
    total_nav: float
    daily_return_pct: float
    cumulative_return_pct: float
    high_water_mark: float
    drawdown_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float
    compliance_score_pct: float
    status: CompanyStatus
    market_regime: MarketRegime
    holdings_count: int


@dataclass
class BenchmarkRecord:
    trade_date: str
    ai_company_nav: float
    ai_company_return_pct: float
    human_strategy_nav: float
    human_strategy_return_pct: float
    nepse_index: float
    nepse_return_pct: float
    equal_weight_nav: float
    equal_weight_return_pct: float
