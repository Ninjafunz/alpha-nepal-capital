"""Pillar 3: Cognitive Delta Engine & Three-Bias Check."""
from typing import Dict, Any, List
import numpy as np

from src.data.models import Stock, PriceBar, Fundamental
from src.strategy.policy import InvestmentPolicy


class CognitiveDeltaEngine:
    """Calculates Layer 3 Cognitive Delta (Perception vs. Reality):
    Three-Bias Check:
    1. Narrative Bias: Management story vs. audited cash flow
    2. Anchoring Bias: Reliance on past ATH vs. structural replacement cost
    3. Recency Bias: Short-term noise vs. 5-year horizon

    Delta % = |Intrinsic Value - Market Price| / Market Price * 100
    - If Delta < 30% -> Reject / No Position
    - If Delta 30-50% -> Standard Position
    - If Delta > 50% -> Aggressive Allocation
    """

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.config = policy.cognitive_delta

    def evaluate_delta(
        self,
        stock: Stock,
        price_bar: PriceBar,
        fundamental: Fundamental,
        price_history: List[PriceBar],
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Calculates 3 biases, intrinsic value estimate, and Delta %."""
        
        # 1. Narrative Bias Check (0-100; Higher = Lower narrative inflation, more cash-flow backed)
        # Low P/E with positive EPS means solid cash earnings backing price
        if fundamental.pe_ratio > 0:
            pe_score = np.clip(100.0 - (fundamental.pe_ratio * 2.2), 20.0, 95.0)
        else:
            pe_score = 40.0
        narrative_score = float(pe_score)

        # 2. Anchoring Bias Check (0-100; Higher = Anchored in replacement book value)
        # Price-to-Book ratio evaluates anchoring to physical assets
        if fundamental.pb_ratio > 0:
            pb_score = np.clip(100.0 - (fundamental.pb_ratio * 18.0), 20.0, 95.0)
        else:
            pb_score = 45.0
        anchoring_score = float(pb_score)

        # 3. Recency Bias Check (0-100; Higher = Price not distorted by 90-day noise)
        if len(price_history) >= 60:
            vol_60 = float(np.std([p.pct_change for p in price_history[-60:]]))
            recency_score = np.clip(95.0 - (vol_60 * 12.0), 20.0, 95.0)
        else:
            recency_score = 75.0

        cognitive_score = (
            narrative_score * self.config.bias_penalty_narrative
            + anchoring_score * self.config.bias_penalty_anchoring
            + recency_score * self.config.bias_penalty_recency
        )

        # Estimate Intrinsic Value using ASA-V1.ethics Structural Valuation:
        # Intrinsic Value combines:
        # 1. Earnings Power Value (EPV) = Normalized EPS / Cost of Equity (WACC ~8.5%)
        # 2. 5-Year Structural Compounding Power = EPS * (1 + ROE/100)^5 discounted to present
        # 3. Franchise / Moat Multiplier = 1.0 + (Bottleneck Score / 100 * 0.45)
        # 4. Asset Replacement Value = Book Value * (1.0 + (ROE / 100 * 2.5))
        # 5. Governance Goodwill Bonus = +5% to +15% for ethical leadership
        if fundamental.eps > 0 and fundamental.book_value > 0:
            cost_of_equity = 0.085  # 8.5% structural discount rate
            epv = float(fundamental.eps / cost_of_equity)
            
            # 5-year compounding power of reinvested retained earnings
            growth_rate = min(0.20, (fundamental.roe / 100.0) * (1.0 - (fundamental.dividend_yield_pct / 100.0) if fundamental.dividend_yield_pct < 100 else 0.5))
            five_year_terminal = float(fundamental.eps * ((1.0 + growth_rate) ** 5) / cost_of_equity * (0.9 ** 5))
            
            bottleneck = metadata.get("bottleneck_score", 75.0)
            franchise_mult = 1.0 + (bottleneck / 100.0 * 0.35)
            
            asset_power_val = float(fundamental.book_value * (1.0 + (fundamental.roe / 100.0 * 2.8)))
            
            gov_score = metadata.get("governance_score", 85.0)
            gov_premium = 1.0 + (gov_score / 100.0 * 0.15)
            
            blended_power = (epv * 0.35 + five_year_terminal * 0.40 + asset_power_val * 0.25) * franchise_mult * gov_premium
            intrinsic_value = round(blended_power, 2)
        else:
            intrinsic_value = round(price_bar.close * 0.9, 2)

        # Calculate Cognitive Delta % (Perception vs Structural Reality)
        if price_bar.close > 0:
            delta_pct = round(((intrinsic_value - price_bar.close) / price_bar.close) * 100.0, 2)
        else:
            delta_pct = 0.0

        qualifies_for_investment = (delta_pct >= self.config.min_delta_threshold_pct)
        is_aggressive = (delta_pct >= self.config.aggressive_delta_threshold_pct)

        return {
            "cognitive_delta_score": round(float(cognitive_score), 2),
            "narrative_bias_score": round(float(narrative_score), 2),
            "anchoring_bias_score": round(float(anchoring_score), 2),
            "recency_bias_score": round(float(recency_score), 2),
            "intrinsic_value": intrinsic_value,
            "delta_pct": delta_pct,
            "qualifies": qualifies_for_investment,
            "is_aggressive": is_aggressive,
        }
