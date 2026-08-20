import logging
from typing import Dict, List, Tuple
from datetime import datetime

from src.strategy.policy import InvestmentPolicy
from src.strategy.scorer import StrategyScorer
from src.strategy.macro_delta import MacroDeltaEngine
from src.portfolio.position_sizer import PositionSizer
from src.portfolio.engine import PortfolioEngine
from src.portfolio.leverage_manager import LeverageManager
from src.decision.explainer import DecisionExplainer
from src.decision.executor import VirtualExecutor
from src.data.models import (
    Stock, PriceBar, Fundamental, Decision, Transaction, 
    ActionType, StrategicRoute, PortfolioSnapshot, AssetClass
)

logger = logging.getLogger(__name__)

class DecisionPipeline:
    def __init__(self, policy: InvestmentPolicy, store):
        self.policy = policy
        self.store = store
        self.scorer = StrategyScorer(policy)
        self.macro_scorer = MacroDeltaEngine(policy)
        self.position_sizer = PositionSizer(policy)
        self.explainer = DecisionExplainer()
        self.leverage_manager = LeverageManager(policy)

    def run_cycle(self, trade_date: str, universe: List[Stock], prices: Dict[str, PriceBar], funds: Dict[str, Fundamental], portfolios: Dict[str, PortfolioEngine]) -> List[Decision]:
        all_decisions = []
        
        for profile in self.policy.company.profiles:
            portfolio = portfolios[profile.id]
            profile_universe = [s for s in universe if s.asset_class == profile.asset_class]
            
            logger.info(f"Running pipeline for {profile.name} ({len(profile_universe)} assets)")
            
            for asset in profile_universe:
                if asset.symbol not in prices:
                    continue
                    
                bar = prices[asset.symbol]
                
                # Valuation Routing
                if asset.asset_class == "EQUITY_DOMESTIC":
                    if asset.symbol not in funds:
                        continue
                    fund = funds[asset.symbol]
                    score_result = self.scorer.evaluate_security(asset, bar, fund, [bar], {})
                    delta_pct = 25.0
                    confidence = 85.0
                else:
                    # Global Equity, Crypto, Commodity
                    delta_pct = self.macro_scorer.calculate_gap(asset, bar)
                    score_result = {"composite_score": 80.0, "structural": {}, "literature": {}, "cognitive_delta": {"delta_pct": delta_pct, "intrinsic_value": bar.close * (1 + delta_pct/100)}}
                    confidence = 80.0
                
                # Borrowing Evaluation (Leverage)
                leverage_eval = self.leverage_manager.evaluate_borrowing(
                    expected_yield=delta_pct, 
                    asset_class=asset.asset_class,
                    current_equity=portfolio.get_equity(),
                    current_liabilities=portfolio.liabilities
                )
                
                if leverage_eval["action"] == "BORROW":
                    import uuid
                    borrow_tx = Transaction(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now().isoformat(),
                        trade_date=trade_date,
                        symbol="CASH_LOAN",
                        action=ActionType.BORROW,
                        quantity=1,
                        price=leverage_eval["amount"],
                        gross_value=leverage_eval["amount"],
                        broker_commission=0.0,
                        sebon_fee=0.0,
                        dp_charge=0.0,
                        slippage=0.0,
                        total_cost=0.0,
                        net_value=leverage_eval["amount"],
                        pre_trade_cash=portfolio.cash,
                        post_trade_cash=portfolio.cash + leverage_eval["amount"],
                        pre_trade_nav=0.0,
                        post_trade_nav=0.0,
                        route=StrategicRoute.UNASSIGNED,
                        reason=leverage_eval["reason"],
                        rule_ids=[],
                        confidence_pct=100.0,
                        decision_id="leverage",
                        profile_id=profile.id
                    )
                    portfolio.execute_transaction(borrow_tx)
                    self.store.record_transaction(borrow_tx)
                elif leverage_eval["action"] == "REPAY":
                    import uuid
                    repay_tx = Transaction(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.now().isoformat(),
                        trade_date=trade_date,
                        symbol="CASH_LOAN",
                        action=ActionType.REPAY,
                        quantity=1,
                        price=leverage_eval["amount"],
                        gross_value=leverage_eval["amount"],
                        broker_commission=0.0,
                        sebon_fee=0.0,
                        dp_charge=0.0,
                        slippage=0.0,
                        total_cost=0.0,
                        net_value=leverage_eval["amount"],
                        pre_trade_cash=portfolio.cash,
                        post_trade_cash=portfolio.cash - leverage_eval["amount"],
                        pre_trade_nav=0.0,
                        post_trade_nav=0.0,
                        route=StrategicRoute.UNASSIGNED,
                        reason=leverage_eval["reason"],
                        rule_ids=[],
                        confidence_pct=100.0,
                        decision_id="leverage",
                        profile_id=profile.id
                    )
                    portfolio.execute_transaction(repay_tx)
                    self.store.record_transaction(repay_tx)

                # Route Mapping
                route = StrategicRoute.UNASSIGNED
                if asset.asset_class == "CRYPTO": route = StrategicRoute.ROUTE_GAMMA
                elif asset.asset_class == "COMMODITY": route = StrategicRoute.ROUTE_BETA
                elif asset.asset_class == "EQUITY_GLOBAL": route = StrategicRoute.ROUTE_ALPHA
                
                action = ActionType.BUY
                memo = "Mocked reasoning memo"
                
                import uuid
                dec = Decision(
                    id=str(uuid.uuid4()),
                    symbol=asset.symbol,
                    trade_date=trade_date,
                    action=action,
                    target_quantity=100,
                    confidence_pct=confidence,
                    route=route,
                    reason_summary=memo,
                    structural_score=score_result.get("structural", {}).get("total_score", 0.0),
                    literature_score=score_result.get("literature", {}).get("total_score", 0.0),
                    cognitive_delta_score=delta_pct,
                    profile_id=profile.id
                )
                all_decisions.append(dec)
                
        return all_decisions
