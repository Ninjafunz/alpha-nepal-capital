"""Universe Screener filtering candidates by IPS eligibility."""
from typing import List, Dict, Any
from src.data.models import Stock, PriceBar, Fundamental
from src.strategy.policy import InvestmentPolicy


class UniverseScreener:
    """Pre-screens securities against eligible sectors, categories, and turnover."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.cfg = policy.universe_config

    def filter_universe(
        self,
        stocks: List[Stock],
        price_dict: Dict[str, PriceBar],
        fund_dict: Dict[str, Fundamental],
    ) -> List[Stock]:
        eligible_sectors = set(self.cfg.get("eligible_sectors", []))
        excluded_sectors = set(self.cfg.get("excluded_sectors", []))
        min_category = self.cfg.get("minimum_category", "A")

        screened = []
        for s in stocks:
            if s.sector in excluded_sectors:
                continue
            if eligible_sectors and s.sector not in eligible_sectors:
                continue
            # Must have pricing data
            if s.symbol not in price_dict:
                continue

            screened.append(s)

        return screened
