"""Decision Explainer producing institutional ASA-V1.ethics investment memos."""
from typing import Dict, Any, List
from src.data.models import Decision, ActionType, StrategicRoute


class DecisionExplainer:
    """Generates unhedged, highly structured rationale memos for all AI decisions."""

    @staticmethod
    def generate_explanation(dec: Decision) -> str:
        if dec.action == ActionType.BUY:
            return (
                f"BUY {dec.symbol} | {dec.route.value}\n"
                f"Capital Allocation: NPR {dec.capital_allocation_npr:,.2f} ({dec.target_quantity:,} shares @ NPR {dec.estimated_price:,.2f})\n"
                f"Structural Thesis: Velocity={dec.capital_velocity_score:.1f}, Physical Risk={dec.physical_risk_score:.1f}, "
                f"Regulatory Transition={dec.regulatory_risk_score:.1f}, Bottleneck Asymmetry={dec.bottleneck_score:.1f}\n"
                f"Cognitive Delta: Intrinsic Value=NPR {dec.intrinsic_value_est:,.2f} vs Market=NPR {dec.estimated_price:,.2f} (Delta: +{dec.delta_pct:.1f}%)\n"
                f"Literature Audit: Elite Alignment={dec.elite_alignment_score:.1f}, Prospect Sentiment={dec.sentiment_score:.1f}\n"
                f"Invalidation Condition: {dec.invalidation_condition}"
            )
        elif dec.action == ActionType.SELL:
            return (
                f"SELL {dec.symbol}\n"
                f"Reason: {dec.reason_summary}\n"
                f"Applied Rules: {', '.join(dec.applied_rules)}"
            )
        else:
            return (
                f"HOLD {dec.symbol}\n"
                f"Reason: {dec.reason_summary}"
            )
