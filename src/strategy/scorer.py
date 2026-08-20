"""Composite 3-Layer Scoring Engine for ASA-V1.ethics."""
from typing import Dict, Any, List
from src.data.models import Stock, PriceBar, Fundamental, StrategicRoute
from src.strategy.policy import InvestmentPolicy
from src.strategy.structural import StructuralScorer
from src.strategy.literature import LiteratureAuditScorer
from src.strategy.cognitive_delta import CognitiveDeltaEngine
from src.strategy.route_selector import RouteSelector


class StrategyScorer:
    """Master Scorer orchestrating the 3-Layer Evaluation:
    Layer 1: Structural Score (35% weight)
    Layer 2: Literature Audit Score (30% weight)
    Layer 3: Cognitive Delta Score (35% weight)
    """

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.structural_scorer = StructuralScorer(policy)
        self.literature_scorer = LiteratureAuditScorer(policy)
        self.cognitive_engine = CognitiveDeltaEngine(policy)
        self.route_selector = RouteSelector(policy)

    def evaluate_security(
        self,
        stock: Stock,
        price_bar: PriceBar,
        fundamental: Fundamental,
        price_history: List[PriceBar],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculates all 3 layer scores, assigns route, and produces unified verdict."""
        
        # 1. Structural
        struct_res = self.structural_scorer.score_security(
            stock, price_bar, fundamental, price_history, metadata
        )

        # 2. Literature Audit
        lit_res = self.literature_scorer.score_security(
            stock, price_bar, fundamental, price_history, metadata
        )

        # 3. Cognitive Delta
        cog_res = self.cognitive_engine.evaluate_delta(
            stock, price_bar, fundamental, price_history, metadata
        )

        # Route
        assigned_route = self.route_selector.assign_route(
            stock, price_bar, fundamental, price_history, metadata
        )

        # Final Weighted Composite Score
        final_score = (
            struct_res["structural_composite"] * 0.35
            + lit_res["literature_composite"] * 0.30
            + cog_res["cognitive_delta_score"] * 0.35
        )

        return {
            "symbol": stock.symbol,
            "final_score": round(float(final_score), 2),
            "route": assigned_route,
            "structural": struct_res,
            "literature": lit_res,
            "cognitive": cog_res,
            "intrinsic_value": cog_res["intrinsic_value"],
            "delta_pct": cog_res["delta_pct"],
            "qualifies": cog_res["qualifies"],
            "is_aggressive": cog_res["is_aggressive"],
        }
