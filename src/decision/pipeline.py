"""Multi-Asset Strategic Asset Allocation (SAA) & Tactical Tilt Decision Pipeline."""
import logging
from typing import Dict, List, Tuple, Any
from datetime import datetime
import uuid

from src.strategy.policy import InvestmentPolicy
from src.strategy.scorer import StrategyScorer
from src.strategy.macro_delta import MacroDeltaEngine
from src.strategy.macro_regime import MacroRegimeEngine
from src.strategy.unified_risk import UnifiedRiskManager
from src.strategy.route_selector import RouteSelector
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
    """Master Multi-Asset Decision Cycle executing:
    Phase 1: Macro Regime Detection & SAA Calibration
    Phase 2: Cross-Silo Opportunity Screening
    Phase 3: Risk Override & Position Sizing (Unified)
    Phase 4: Unified Execution & Corporate Reporting
    """

    def __init__(self, policy: InvestmentPolicy, store):
        self.policy = policy
        self.store = store
        self.macro_engine = MacroRegimeEngine(policy)
        self.risk_manager = UnifiedRiskManager(policy)
        self.scorer = StrategyScorer(policy)
        self.macro_scorer = MacroDeltaEngine(policy)
        self.route_selector = RouteSelector(policy)
        self.position_sizer = PositionSizer(policy)
        self.explainer = DecisionExplainer()
        self.leverage_manager = LeverageManager(policy)

    def run_cycle(
        self,
        trade_date: str,
        universe: List[Stock],
        prices: Dict[str, PriceBar],
        funds: Dict[str, Fundamental],
        portfolios: Dict[str, PortfolioEngine]
    ) -> Tuple[List[Decision], Dict[str, Any]]:
        """Runs the 4-phase unified multi-asset decision cycle."""
        all_decisions = []
        
        # ----------------------------------------------------------------------
        # PHASE 1: MACRO REGIME DETECTION & SAA CALIBRATION
        # ----------------------------------------------------------------------
        macro_signals = self.macro_engine.fetch_macro_indicators()
        regime_info = self.macro_engine.detect_regime(macro_signals)
        
        # Calculate current consolidated NAV and asset class weights
        total_consolidated_assets = sum(p.get_total_assets() for p in portfolios.values())
        current_allocations = {}
        for p_id, p_eng in portfolios.items():
            val = p_eng.get_total_assets()
            pct = (val / max(1.0, total_consolidated_assets)) * 100.0
            current_allocations[p_id] = round(pct, 1)

        saa_calibration = self.macro_engine.calculate_saa_and_tilts(regime_info, current_allocations)
        logger.info(f"[Phase 1] Regime: {regime_info['regime']} | Tilts: {saa_calibration['tactical_tilts']}")

        # Currency Risk Evaluation (USD Exposure)
        usd_assets_total = sum(
            p.get_total_assets() for p_id, p in portfolios.items() 
            if p_id in ["P2_GLOBAL_EQUITY", "P3_COMMODITIES", "P4_CRYPTO"]
        )
        fx_eval = self.risk_manager.evaluate_currency_risk(usd_assets_total, total_consolidated_assets)

        # ----------------------------------------------------------------------
        # PHASE 2 & 3: CROSS-SILO SCREENING & UNIFIED RISK POSITION SIZING
        # ----------------------------------------------------------------------
        for profile in self.policy.company.profiles:
            portfolio = portfolios[profile.id]
            profile_universe = [s for s in universe if s.asset_class == profile.asset_class]
            
            for asset in profile_universe:
                if asset.symbol not in prices:
                    continue
                    
                bar = prices[asset.symbol]
                
                # 1. Valuation & Route Assignment
                if asset.asset_class == "EQUITY_DOMESTIC":
                    if asset.symbol not in funds:
                        continue
                    fund = funds[asset.symbol]
                    # Pass security metadata if available
                    sec_meta = {
                        "bottleneck_score": getattr(asset, "bottleneck_score", 85.0),
                        "elite_alignment": getattr(asset, "elite_alignment", 80.0),
                        "governance_score": getattr(asset, "governance_score", 85.0),
                        "route_eligibility": getattr(asset, "route_eligibility", ["Route Alpha"]),
                    }
                    score_result = self.scorer.evaluate_security(asset, bar, fund, [bar], sec_meta)
                    
                    # Extract delta and route from 3-Layer Scorer
                    delta_pct = 25.0
                    if isinstance(score_result, dict):
                        if "cognitive" in score_result and "delta_pct" in score_result["cognitive"]:
                            delta_pct = score_result["cognitive"]["delta_pct"]
                        elif "cognitive_delta" in score_result:
                            delta_pct = score_result["cognitive_delta"].get("delta_pct", 25.0)
                        elif "final_score" in score_result:
                            delta_pct = (score_result["final_score"] / 100.0) * 35.0
                        
                    route_val = score_result.get("route", StrategicRoute.ROUTE_ALPHA)
                    if isinstance(route_val, StrategicRoute):
                        route = route_val
                    elif isinstance(route_val, str):
                        if "Alpha" in route_val:
                            route = StrategicRoute.ROUTE_ALPHA
                        elif "Beta" in route_val:
                            route = StrategicRoute.ROUTE_BETA
                        elif "Gamma" in route_val:
                            route = StrategicRoute.ROUTE_GAMMA
                        else:
                            route = StrategicRoute.ROUTE_ALPHA
                    else:
                        route = StrategicRoute.ROUTE_ALPHA

                    confidence = score_result.get("final_score", 85.0) if isinstance(score_result, dict) else 85.0
                    vol_30d = 18.0
                else:
                    if asset.asset_class == "CRYPTO":
                        delta_pct = 20.0
                        route = StrategicRoute.ROUTE_GAMMA
                        confidence = 80.0
                        vol_30d = 65.0
                    elif asset.asset_class == "COMMODITY":
                        route = StrategicRoute.ROUTE_BETA
                        vol_30d = 14.0
                        delta_pct = 20.0
                        confidence = 80.0
                    else:
                        route = StrategicRoute.ROUTE_ALPHA
                        vol_30d = 16.0
                        delta_pct = 20.0
                        confidence = 80.0
                        
                    score_result = {
                        "composite_score": 82.0,
                        "structural": {"total_score": 85.0},
                        "literature": {"total_score": 80.0},
                        "cognitive_delta": {
                            "delta_pct": delta_pct,
                            "intrinsic_value": bar.close * (1 + delta_pct / 100.0)
                        }
                    }
                    confidence = 82.0

                # 2. Constitutional Threshold Check (Delta >= min threshold)
                min_threshold = self.policy.cognitive_delta.min_delta_threshold_pct
                
                if delta_pct >= min_threshold:
                    action = ActionType.BUY
                    
                    # Current values
                    current_position_value = portfolio.holdings[asset.symbol].current_value if asset.symbol in portfolio.holdings else 0.0
                    current_sector_value = sum(h.current_value for h in portfolio.holdings.values() if h.sector == asset.sector)
                    is_aggressive = delta_pct >= self.policy.cognitive_delta.aggressive_delta_threshold_pct
                    
                    # Sizer calculation
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
                    
                    target_allocation_npr = sizer_res.get("target_npr", 0.0)
                    
                    # Unified Risk Override 1: Volatility Override
                    vol_check = self.risk_manager.evaluate_volatility_override(asset.asset_class, vol_30d)
                    if vol_check["override_active"]:
                        target_allocation_npr *= vol_check["size_multiplier"]

                    # Unified Risk Override 2: Liquidity Override
                    liq_check = self.risk_manager.evaluate_liquidity_override(asset, target_allocation_npr, total_consolidated_assets)
                    if liq_check["override_active"]:
                        target_allocation_npr = liq_check["capped_allocation_npr"]

                    # Unified Risk Override 3: Concentration Limits
                    conc_check = self.risk_manager.evaluate_concentration_override(
                        asset.asset_class, target_allocation_npr, total_consolidated_assets, current_position_value
                    )
                    if conc_check["capped"]:
                        target_allocation_npr = conc_check["allowed_order_npr"]

                    target_qty = int(target_allocation_npr / max(1.0, bar.close))
                    
                    # Hard positions cap (max 25 globally across profiles)
                    if current_position_value <= 0 and len(portfolio.holdings) >= self.policy.constraints.max_positions:
                        action = ActionType.HOLD
                        target_qty = 0
                        executed = False
                        memo = f"Decision Pipeline: Max holdings cap reached ({self.policy.constraints.max_positions}). Position in {asset.symbol} skipped."
                    elif sizer_res["allowed"] and target_qty > 0:
                        executed = True
                        memo = f"Strategic Tilt ({regime_info['regime']}): Cognitive delta {delta_pct:.1f}% >= {min_threshold}%. {sizer_res['reason']}"
                    else:
                        action = ActionType.HOLD
                        target_qty = 0
                        executed = False
                        memo = f"Decision Pipeline: Sizing constraint. {sizer_res['reason']}"
                else:
                    action = ActionType.HOLD
                    target_qty = 0
                    executed = False
                    memo = f"Decision Pipeline: Cognitive delta {delta_pct:.1f}% below minimum threshold of {min_threshold}%."

                dec = Decision(
                    id=f"DEC-{uuid.uuid4().hex[:8].upper()}",
                    timestamp=datetime.now().isoformat(),
                    trade_date=trade_date,
                    symbol=asset.symbol,
                    action=action,
                    confidence_pct=confidence,
                    target_quantity=target_qty,
                    estimated_price=round(bar.close, 2),
                    capital_allocation_npr=round(target_qty * bar.close, 2),
                    route=route,
                    structural_score=score_result.get("structural", {}).get("structural_composite", 85.0) if isinstance(score_result, dict) else 85.0,
                    capital_velocity_score=score_result.get("structural", {}).get("capital_velocity", 80.0) if isinstance(score_result, dict) else 80.0,
                    physical_risk_score=score_result.get("structural", {}).get("physical_risk", 10.0) if isinstance(score_result, dict) else 10.0,
                    regulatory_risk_score=score_result.get("structural", {}).get("regulatory_risk", 15.0) if isinstance(score_result, dict) else 15.0,
                    bottleneck_score=score_result.get("structural", {}).get("bottleneck_asymmetry", 85.0) if isinstance(score_result, dict) else 85.0,
                    literature_score=score_result.get("literature", {}).get("literature_composite", 80.0) if isinstance(score_result, dict) else 80.0,
                    elite_alignment_score=score_result.get("literature", {}).get("elite_alignment", 85.0) if isinstance(score_result, dict) else 85.0,
                    sentiment_score=score_result.get("literature", {}).get("sentiment_position", 75.0) if isinstance(score_result, dict) else 75.0,
                    optionality_score=score_result.get("literature", {}).get("real_options", 80.0) if isinstance(score_result, dict) else 80.0,
                    golden_zone_score=score_result.get("literature", {}).get("golden_zone", 80.0) if isinstance(score_result, dict) else 80.0,
                    cognitive_delta_score=delta_pct,
                    narrative_bias_score=score_result.get("cognitive", {}).get("narrative_bias", 5.0) if isinstance(score_result, dict) else 5.0,
                    anchoring_bias_score=score_result.get("cognitive", {}).get("anchoring_bias", 5.0) if isinstance(score_result, dict) else 5.0,
                    recency_bias_score=score_result.get("cognitive", {}).get("recency_bias", 5.0) if isinstance(score_result, dict) else 5.0,
                    intrinsic_value_est=score_result.get("cognitive", {}).get("intrinsic_value", round(bar.close * (1.0 + delta_pct / 100.0), 2)) if isinstance(score_result, dict) else round(bar.close * (1.0 + delta_pct / 100.0), 2),
                    delta_pct=delta_pct,
                    final_score=confidence,
                    reason_summary=memo,
                    applied_rules=["ASA-V1.ethics", "Constitutional SAA", str(route.value if hasattr(route, 'value') else route)],
                    invalidation_condition="Exit if 30-day realized volatility exceeds 25% or fundamental thesis degrades by >15%.",
                    profile_id=profile.id,
                    executed=executed
                )
                
                # ----------------------------------------------------------------------
                # PHASE 4: UNIFIED VIRTUAL EXECUTION CALL
                # ----------------------------------------------------------------------
                if executed and action == ActionType.BUY:
                    executor = VirtualExecutor(self.policy, self.store, portfolio)
                    tx = executor.execute_decision(dec, asset, bar)
                    if tx:
                        logger.info(f"Executed Order: {action} {target_qty} {asset.symbol} @ {bar.close:,.2f} NPR")
                
                all_decisions.append(dec)

        cycle_metadata = {
            "macro_signals": macro_signals,
            "regime_info": regime_info,
            "saa_calibration": saa_calibration,
            "fx_eval": fx_eval,
            "timestamp": datetime.now().isoformat()
        }
        
        return all_decisions, cycle_metadata
