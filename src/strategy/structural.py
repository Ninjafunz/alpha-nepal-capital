"""Pillar 1: Structural Anchoring & 4 Structural Variables Scorer."""
from typing import Dict, Any, List
import numpy as np

from src.data.models import Stock, PriceBar, Fundamental
from src.strategy.policy import InvestmentPolicy


class StructuralScorer:
    """Calculates Layer 1 Structural Score from the 4 Structural Variables:
    1. Capital Velocity (liquidity flow, credit spreads, 90-day momentum)
    2. Physical/Operational Risk (supply chain resilience, NPL, hydro PPA/flow)
    3. Regulatory/Transition Risk (NRB directives, SEBON policy, tax tailwinds)
    4. Bottleneck Asymmetry (inelastic levers, steep marginal cost curve)
    """

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.weights = policy.structural_variables

    def score_security(
        self,
        stock: Stock,
        price_bar: PriceBar,
        fundamental: Fundamental,
        price_history: List[PriceBar],
        metadata: Dict[str, Any],
    ) -> Dict[str, float]:
        """Returns 0-100 scores for each variable and composite structural score."""
        
        # 1. Capital Velocity (Liquidity Flow & Momentum)
        if len(price_history) >= 20:
            returns = [p.pct_change for p in price_history[-20:]]
            momentum_20d = float(np.mean(returns) * 20.0)
            vol_trend = float(price_bar.volume / max(1, np.mean([p.volume for p in price_history[-20:]])))
            velocity_score = np.clip(50.0 + (momentum_20d * 2.5) + ((vol_trend - 1.0) * 15.0), 10.0, 95.0)
        else:
            velocity_score = 65.0

        # 2. Physical / Operational Risk (Higher = Safer / More Resilient)
        if stock.sector == "Commercial Bank":
            # For banks: lower debt-to-equity leverage & higher ROE = higher resilience
            risk_score = np.clip(100.0 - (fundamental.debt_to_equity * 4.5) + (fundamental.roe * 1.5), 20.0, 95.0)
        elif stock.sector == "Hydropower":
            # For hydro: low debt & high book value stability
            risk_score = np.clip(85.0 - (fundamental.debt_to_equity * 10.0) + (fundamental.roe * 1.2), 30.0, 95.0)
        else:
            risk_score = np.clip(75.0 + (fundamental.roe * 0.8) - (fundamental.debt_to_equity * 5.0), 20.0, 95.0)

        # 3. Regulatory / Transition Risk (Policy Tailwinds)
        # Priority sectors defined in Kondratiev mapping get structural tailwind
        priority_sectors = self.policy.kondratiev.priority_sectors
        base_reg_score = 80.0 if stock.sector in priority_sectors else 65.0
        # Ethics & Governance bonus (Ethics is a long-duration call option on regulatory goodwill)
        gov_score = metadata.get("governance_score", 85.0)
        reg_score = np.clip(base_reg_score * 0.5 + gov_score * 0.5, 20.0, 98.0)

        # 4. Bottleneck Asymmetry (Inelastic lever, steep marginal cost curve)
        bottleneck_raw = metadata.get("bottleneck_score", 75.0)
        # Market leader / high paid-up capital companies enjoy stronger bottleneck advantage
        capital_boost = min(10.0, stock.paid_up_capital_cr / 300.0)
        bottleneck_score = np.clip(bottleneck_raw + capital_boost, 20.0, 99.0)

        # Composite Layer 1 Structural Score
        composite = (
            velocity_score * self.weights.capital_velocity_weight
            + risk_score * self.weights.physical_operational_weight
            + reg_score * self.weights.regulatory_transition_weight
            + bottleneck_score * self.weights.bottleneck_asymmetry_weight
        )

        return {
            "structural_composite": round(float(composite), 2),
            "capital_velocity": round(float(velocity_score), 2),
            "physical_risk": round(float(risk_score), 2),
            "regulatory_risk": round(float(reg_score), 2),
            "bottleneck_asymmetry": round(float(bottleneck_score), 2),
        }
