"""Staged Decision Pipeline orchestrating the ASA-V1.ethics Decision Hierarchy."""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.data.models import (
    Stock,
    PriceBar,
    Fundamental,
    Decision,
    ActionType,
    StrategicRoute,
    Transaction,
)
from src.data.store import DataStore
from src.strategy.policy import InvestmentPolicy
from src.strategy.screener import UniverseScreener
from src.strategy.scorer import StrategyScorer
from src.portfolio.engine import PortfolioEngine
from src.portfolio.position_sizer import PositionSizer
from src.decision.executor import VirtualExecutor
from src.decision.explainer import DecisionExplainer


class DecisionPipeline:
    """Orchestrates the 8-stage Decision Hierarchy:
    1. Market Data Ingestion
    2. Opportunity Scan & Screening
    3. 3-Layer Scoring (Structural, Literature, Cognitive Delta)
    4. Risk & Limit Filtering
    5. Route-Aware Position Sizing
    6. Decision Formulation (BUY/HOLD/SELL)
    7. Pre-Trade Risk Verification
    8. Immutable Ledger Logging & Execution
    """

    def __init__(
        self,
        policy: InvestmentPolicy,
        store: DataStore,
        portfolio: PortfolioEngine,
    ):
        self.policy = policy
        self.store = store
        self.portfolio = portfolio
        self.screener = UniverseScreener(policy)
        self.scorer = StrategyScorer(policy)
        self.position_sizer = PositionSizer(policy)
        self.executor = VirtualExecutor(policy, store, portfolio)

    def run_cycle(
        self,
        trade_date: str,
        universe_stocks: List[Stock],
        price_dict: Dict[str, PriceBar],
        fund_dict: Dict[str, Fundamental],
        metadata_dict: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Executes full daily decision pipeline for all securities."""
        
        # Stage 1 & 2: Screening
        screened_stocks = self.screener.filter_universe(universe_stocks, price_dict, fund_dict)
        
        decisions: List[Decision] = []
        executed_transactions: List[Transaction] = []

        total_assets = self.portfolio.get_total_assets()
        current_cash = self.portfolio.cash
        sector_exposures = self.portfolio.get_sector_exposures()

        # Check existing holdings first (Evaluate for HOLD vs SELL)
        for symbol, holding in list(self.portfolio.holdings.items()):
            bar = price_dict.get(symbol)
            fund = fund_dict.get(symbol)
            meta = metadata_dict.get(symbol, {})
            stock_obj = next((s for s in universe_stocks if s.symbol == symbol), None)
            
            if not bar or not fund or not stock_obj:
                continue

            eval_res = self.scorer.evaluate_security(
                stock_obj, bar, fund, self.store.get_price_history_series(symbol, 60), meta
            )

            # Check sell conditions:
            # 1. Delta no longer positive / score severely degraded
            # 2. Sector or position limit breach
            if eval_res["final_score"] < 40.0 or eval_res["delta_pct"] < 0:
                # Sell candidate
                dec_id = f"DEC-{trade_date.replace('-', '')}-{uuid.uuid4().hex[:6].upper()}"
                decision = Decision(
                    id=dec_id,
                    timestamp=datetime.now().isoformat(),
                    trade_date=trade_date,
                    symbol=symbol,
                    action=ActionType.SELL,
                    confidence_pct=85.0,
                    target_quantity=holding.quantity,
                    estimated_price=bar.close,
                    capital_allocation_npr=holding.current_value,
                    route=holding.route,
                    structural_score=eval_res["structural"]["structural_composite"],
                    capital_velocity_score=eval_res["structural"]["capital_velocity"],
                    physical_risk_score=eval_res["structural"]["physical_risk"],
                    regulatory_risk_score=eval_res["structural"]["regulatory_risk"],
                    bottleneck_score=eval_res["structural"]["bottleneck_asymmetry"],
                    literature_score=eval_res["literature"]["literature_composite"],
                    elite_alignment_score=eval_res["literature"]["elite_alignment"],
                    sentiment_score=eval_res["literature"]["sentiment_position"],
                    optionality_score=eval_res["literature"]["real_options"],
                    golden_zone_score=eval_res["literature"]["golden_zone"],
                    cognitive_delta_score=eval_res["cognitive"]["cognitive_delta_score"],
                    narrative_bias_score=eval_res["cognitive"]["narrative_bias_score"],
                    anchoring_bias_score=eval_res["cognitive"]["anchoring_bias_score"],
                    recency_bias_score=eval_res["cognitive"]["recency_bias_score"],
                    intrinsic_value_est=eval_res["intrinsic_value"],
                    delta_pct=eval_res["delta_pct"],
                    final_score=eval_res["final_score"],
                    reason_summary=f"Cognitive delta fell below 0% (Score: {eval_res['final_score']:.1f}). Reallocating capital.",
                    applied_rules=["R-SELL-SCORE-DEGRADED"],
                    invalidation_condition="Immediate execution",
                    executed=True,
                )
                self.store.record_decision(decision)
                decisions.append(decision)
                tx = self.executor.execute_decision(decision, stock_obj, bar)
                if tx:
                    executed_transactions.append(tx)

        # Stage 3, 4, 5, 6, 7: Score Candidate Buys & Evaluate New Positions
        candidate_scores = []
        for stock in screened_stocks:
            bar = price_dict.get(stock.symbol)
            fund = fund_dict.get(stock.symbol)
            meta = metadata_dict.get(stock.symbol, {})
            if not bar or not fund:
                continue

            hist = self.store.get_price_history_series(stock.symbol, 60)
            eval_res = self.scorer.evaluate_security(stock, bar, fund, hist, meta)
            candidate_scores.append((stock, bar, fund, meta, eval_res))

        # Rank candidates by final score descending
        candidate_scores.sort(key=lambda x: x[4]["final_score"], reverse=True)

        # Check buy candidates
        for stock, bar, fund, meta, eval_res in candidate_scores:
            if len(self.portfolio.holdings) >= self.policy.constraints.max_positions:
                break  # Max positions reached

            # Must satisfy Cognitive Delta threshold (>30%)
            if not eval_res["qualifies"]:
                # Log non-qualifying candidate (HOLD/PASS)
                dec_id = f"DEC-{trade_date.replace('-', '')}-{uuid.uuid4().hex[:6].upper()}"
                decision = Decision(
                    id=dec_id,
                    timestamp=datetime.now().isoformat(),
                    trade_date=trade_date,
                    symbol=stock.symbol,
                    action=ActionType.HOLD,
                    confidence_pct=eval_res["final_score"],
                    target_quantity=0,
                    estimated_price=bar.close,
                    capital_allocation_npr=0.0,
                    route=eval_res["route"],
                    structural_score=eval_res["structural"]["structural_composite"],
                    capital_velocity_score=eval_res["structural"]["capital_velocity"],
                    physical_risk_score=eval_res["structural"]["physical_risk"],
                    regulatory_risk_score=eval_res["structural"]["regulatory_risk"],
                    bottleneck_score=eval_res["structural"]["bottleneck_asymmetry"],
                    literature_score=eval_res["literature"]["literature_composite"],
                    elite_alignment_score=eval_res["literature"]["elite_alignment"],
                    sentiment_score=eval_res["literature"]["sentiment_position"],
                    optionality_score=eval_res["literature"]["real_options"],
                    golden_zone_score=eval_res["literature"]["golden_zone"],
                    cognitive_delta_score=eval_res["cognitive"]["cognitive_delta_score"],
                    narrative_bias_score=eval_res["cognitive"]["narrative_bias_score"],
                    anchoring_bias_score=eval_res["cognitive"]["anchoring_bias_score"],
                    recency_bias_score=eval_res["cognitive"]["recency_bias_score"],
                    intrinsic_value_est=eval_res["intrinsic_value"],
                    delta_pct=eval_res["delta_pct"],
                    final_score=eval_res["final_score"],
                    reason_summary=f"Evaluated (Score: {eval_res['final_score']:.1f}). Cognitive delta (+{eval_res['delta_pct']:.1f}%) below 30% threshold for capital deployment.",
                    applied_rules=["R-HOLD-DELTA-INSUFFICIENT"],
                    invalidation_condition="Wait for cognitive delta > 30%",
                    executed=False,
                )
                self.store.record_decision(decision)
                decisions.append(decision)
                continue

            # Position Sizing Check
            curr_pos_val = self.portfolio.holdings[stock.symbol].current_value if stock.symbol in self.portfolio.holdings else 0.0
            curr_sec_val = (self.portfolio.get_sector_exposures().get(stock.sector, 0.0) / 100.0) * self.portfolio.get_total_assets()

            size_res = self.position_sizer.calculate_order_size(
                symbol=stock.symbol,
                price=bar.close,
                score=eval_res["final_score"],
                delta_pct=eval_res["delta_pct"],
                route=eval_res["route"],
                is_aggressive=eval_res["is_aggressive"],
                current_cash=self.portfolio.cash,
                total_assets=self.portfolio.get_total_assets(),
                current_position_value=curr_pos_val,
                current_sector_value=curr_sec_val,
            )

            if size_res["allowed"] and size_res["quantity"] > 0:
                dec_id = f"DEC-{trade_date.replace('-', '')}-{uuid.uuid4().hex[:6].upper()}"
                
                applied_rules = ["R-BUY-DELTA-QUALIFIED", "R-RISK-HEADROOM-PASS"]
                if eval_res["is_aggressive"]:
                    applied_rules.append("R-AGGRESSIVE-ALLOCATION")

                inv_cond = "15% drawdown or 2 consecutive quarters of negative operating cash flow"

                decision = Decision(
                    id=dec_id,
                    timestamp=datetime.now().isoformat(),
                    trade_date=trade_date,
                    symbol=stock.symbol,
                    action=ActionType.BUY,
                    confidence_pct=round(min(96.0, eval_res["final_score"] * 1.1), 1),
                    target_quantity=size_res["quantity"],
                    estimated_price=bar.close,
                    capital_allocation_npr=size_res["target_npr"],
                    route=eval_res["route"],
                    structural_score=eval_res["structural"]["structural_composite"],
                    capital_velocity_score=eval_res["structural"]["capital_velocity"],
                    physical_risk_score=eval_res["structural"]["physical_risk"],
                    regulatory_risk_score=eval_res["structural"]["regulatory_risk"],
                    bottleneck_score=eval_res["structural"]["bottleneck_asymmetry"],
                    literature_score=eval_res["literature"]["literature_composite"],
                    elite_alignment_score=eval_res["literature"]["elite_alignment"],
                    sentiment_score=eval_res["literature"]["sentiment_position"],
                    optionality_score=eval_res["literature"]["real_options"],
                    golden_zone_score=eval_res["literature"]["golden_zone"],
                    cognitive_delta_score=eval_res["cognitive"]["cognitive_delta_score"],
                    narrative_bias_score=eval_res["cognitive"]["narrative_bias_score"],
                    anchoring_bias_score=eval_res["cognitive"]["anchoring_bias_score"],
                    recency_bias_score=eval_res["cognitive"]["recency_bias_score"],
                    intrinsic_value_est=eval_res["intrinsic_value"],
                    delta_pct=eval_res["delta_pct"],
                    final_score=eval_res["final_score"],
                    reason_summary=(
                        f"Structural Score: {eval_res['structural']['structural_composite']:.1f} | "
                        f"Cognitive Delta: +{eval_res['delta_pct']:.1f}% (Intrinsic: NPR {eval_res['intrinsic_value']:,.2f} vs Market: NPR {bar.close:,.2f}) | "
                        f"Route: {eval_res['route'].value}"
                    ),
                    applied_rules=applied_rules,
                    invalidation_condition=inv_cond,
                    executed=True,
                )
                self.store.record_decision(decision)
                decisions.append(decision)

                tx = self.executor.execute_decision(decision, stock, bar)
                if tx:
                    executed_transactions.append(tx)

        # Mark portfolio to market with latest updated positions
        self.portfolio.mark_to_market(price_dict, {s.symbol: s for s in universe_stocks})

        return {
            "decisions": decisions,
            "transactions": executed_transactions,
            "portfolio_assets": self.portfolio.get_total_assets(),
            "cash": self.portfolio.cash,
        }
