import logging
from typing import Dict, List, Tuple
from datetime import datetime
import uuid

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
                
                # 1. Valuation Routing
                if asset.asset_class == "EQUITY_DOMESTIC":
                    if asset.symbol not in funds:
                        continue
                    fund = funds[asset.symbol]
                    score_result = self.scorer.evaluate_security(asset, bar, fund, [bar], {})
                    
                    # Compute actual cognitive delta if available, otherwise default to evaluate_security output
                    delta_pct = 25.0  # Fallback baseline
                    if isinstance(score_result, dict) and "cognitive_delta" in score_result:
                        delta_pct = score_result["cognitive_delta"].get("delta_pct", 25.0)
                    elif isinstance(score_result, dict) and "composite_score" in score_result:
                        # Map score to estimated delta for back-compatibility
                        delta_pct = (score_result["composite_score"] / 100.0) * 40.0
                    
                    confidence = score_result.get("composite_score", 85.0) if isinstance(score_result, dict) else 85.0
                else:
                    # Global Equity, Crypto, Commodity
                    delta_pct = self.macro_scorer.calculate_gap(asset, bar)
                    score_result = {
                        "composite_score": 80.0, 
                        "structural": {"total_score": 80.0}, 
                        "literature": {"total_score": 80.0}, 
                        "cognitive_delta": {
                            "delta_pct": delta_pct, 
                            "intrinsic_value": bar.close * (1 + delta_pct/100)
                        }
                    }
                    confidence = 80.0
                
                # 2. Borrowing Evaluation (Leverage)
                leverage_eval = self.leverage_manager.evaluate_borrowing(
                    expected_yield=delta_pct, 
                    asset_class=asset.asset_class,
                    current_equity=portfolio.get_equity(),
                    current_liabilities=portfolio.liabilities
                )
                
                if leverage_eval["action"] == "BORROW":
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

                # 3. Route Mapping
                route = StrategicRoute.UNASSIGNED
                if asset.asset_class == "CRYPTO": route = StrategicRoute.ROUTE_GAMMA
                elif asset.asset_class == "COMMODITY": route = StrategicRoute.ROUTE_BETA
                elif asset.asset_class == "EQUITY_GLOBAL": route = StrategicRoute.ROUTE_ALPHA

                # 4. Constitutional Threshold Triage
                min_threshold = self.policy.cognitive_delta.min_delta_threshold_pct
                
                if delta_pct >= min_threshold:
                    action = ActionType.BUY
                    
                    # 5. Position Sizing & Portfolio Constraint Audits
                    current_position_value = portfolio.holdings[asset.symbol].current_value if asset.symbol in portfolio.holdings else 0.0
                    current_sector_value = sum(h.current_value for h in portfolio.holdings.values() if h.sector == asset.sector)
                    is_aggressive = delta_pct >= self.policy.cognitive_delta.aggressive_delta_threshold_pct
                    
                    # Hard Constraint: Max active positions cap (15) check for new positions
                    if current_position_value <= 0 and len(portfolio.holdings) >= self.policy.constraints.max_positions:
                        action = ActionType.HOLD
                        target_qty = 0
                        executed = False
                        memo = f"Decision Pipeline: Max active positions cap of {self.policy.constraints.max_positions} reached. Skipping new position in {asset.symbol}."
                    else:
                        sizer_res = self.position_sizer.calculate_order_size(
                            symbol=asset.symbol,
                            price=bar.close,
                            score=confidence,
                            delta_pct=delta_pct,
                            route=route,
                            is_aggressive=is_aggressive,
                            current_cash=portfolio.cash,
                            total_assets=portfolio.get_total_assets(),
                            current_position_value=current_position_value,
                            current_sector_value=current_sector_value
                        )
                        
                        if sizer_res["allowed"] and sizer_res["quantity"] > 0:
                            target_qty = sizer_res["quantity"]
                            executed = True
                            memo = f"Decision Pipeline: Cognitive delta {delta_pct:.1f}% satisfies the minimum threshold of {min_threshold}%. Sizer allowed {target_qty} shares: {sizer_res['reason']}"
                        else:
                            action = ActionType.HOLD
                            target_qty = 0
                            executed = False
                            memo = f"Decision Pipeline: Sizing constraint. {sizer_res['reason']}"
                else:
                    action = ActionType.HOLD
                    target_qty = 0
                    executed = False
                    memo = f"Decision Pipeline: Cognitive delta {delta_pct:.1f}% below minimum strategy threshold of {min_threshold}%."

                dec = Decision(
                    id=str(uuid.uuid4()),
                    symbol=asset.symbol,
                    trade_date=trade_date,
                    action=action,
                    target_quantity=target_qty,
                    confidence_pct=confidence,
                    route=route,
                    reason_summary=memo,
                    structural_score=score_result.get("structural", {}).get("total_score", 0.0),
                    literature_score=score_result.get("literature", {}).get("total_score", 0.0),
                    cognitive_delta_score=delta_pct,
                    profile_id=profile.id,
                    executed=executed
                )
                
                # 6. Virtual Execution Call (Bridges Decisions to actual Portfolio Transactions)
                if executed and action == ActionType.BUY:
                    executor = VirtualExecutor(self.policy, self.store, portfolio)
                    tx = executor.execute_decision(dec, asset, bar)
                    if tx:
                        logger.info(f"Executed Order: {action} {target_qty} {asset.symbol} @ {bar.close}")
                
                all_decisions.append(dec)
                
        return all_decisions
