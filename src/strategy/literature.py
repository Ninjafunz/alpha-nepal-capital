"""Pillar 2: Theoretical Literature Audit & Litmus Test."""
from typing import Dict, Any, List
import numpy as np

from src.data.models import Stock, PriceBar, Fundamental
from src.strategy.policy import InvestmentPolicy


class LiteratureAuditScorer:
    """Calculates Layer 2 Literature Audit Score across 4 domains:
    1. Sociology: Kondratiev / Elite Theory (political alignment)
    2. Psychology: Prospect Theory (mispriced middle vs extreme greed/fear)
    3. Economics: Real Options & Modern Portfolio Theory (unpriced optionality)
    4. Law: Regulatory Capture Theory ('Golden Zone' dynamics)
    """

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.weights = policy.literature_audit

    def score_security(
        self,
        stock: Stock,
        price_bar: PriceBar,
        fundamental: Fundamental,
        price_history: List[PriceBar],
        metadata: Dict[str, Any],
    ) -> Dict[str, float]:
        """Calculates literature audit scores normalized to 0-100."""
        
        # 1. Sociology: Kondratiev / Elite Theory Alignment
        elite_score = float(metadata.get("elite_alignment", 80.0))

        # 2. Psychology: Prospect Theory (The Mispriced Middle)
        # Check if trading in the rational 25th-75th percentile range rather than extreme retail frenzy
        if len(price_history) >= 30:
            closes = [p.close for p in price_history[-30:]]
            min_c = min(closes)
            max_c = max(closes)
            range_span = max_c - min_c
            if range_span > 0:
                pos = (price_bar.close - min_c) / range_span
                # Alpha sits in the mispriced middle (0.25 to 0.75)
                distance_from_middle = abs(pos - 0.50)
                sentiment_score = np.clip(95.0 - (distance_from_middle * 70.0), 20.0, 95.0)
            else:
                sentiment_score = 75.0
        else:
            sentiment_score = 75.0

        # 3. Economics: Real Options (Unpriced optionality)
        # Companies with low P/B and high ROE have latent unpriced asset optionality
        if fundamental.pb_ratio > 0:
            optionality_base = (fundamental.roe / fundamental.pb_ratio) * 10.0
            optionality_score = np.clip(40.0 + optionality_base, 20.0, 95.0)
        else:
            optionality_score = 65.0

        # 4. Law: Regulatory Capture ("Golden Zone" Sweet Spot)
        # In NEPSE, top Class A companies with strong market cap hold institutional capture
        golden_zone_score = float(metadata.get("governance_score", 85.0))

        composite = (
            elite_score * self.weights.elite_alignment_weight
            + sentiment_score * self.weights.sentiment_position_weight
            + optionality_score * self.weights.real_options_weight
            + golden_zone_score * self.weights.golden_zone_weight
        )

        return {
            "literature_composite": round(float(composite), 2),
            "elite_alignment": round(float(elite_score), 2),
            "sentiment_position": round(float(sentiment_score), 2),
            "real_options": round(float(optionality_score), 2),
            "golden_zone": round(float(golden_zone_score), 2),
        }
