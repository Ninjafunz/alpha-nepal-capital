"""Pillar 4: Strategic Route Assignment (Alpha, Beta, Gamma)."""
from typing import Dict, Any, List
from src.data.models import Stock, PriceBar, Fundamental, StrategicRoute
from src.strategy.policy import InvestmentPolicy


class RouteSelector:
    """Classifies candidate securities into the 3 Strategic Execution Routes:
    1. Route Alpha (Defensive Moat): Insulated infrastructure, recurring sovereign revenue, high dividend
    2. Route Beta (Contra-Cyclical Raid): Deep value turnaround, beaten-down high leverage (D/E > 2x, 30%+ drawdown)
    3. Route Gamma (Policy Hack): 20%+ compliance superiority, regulatory-first moat
    """

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.routes_cfg = policy.routes_config

    def assign_route(
        self,
        stock: Stock,
        price_bar: PriceBar,
        fundamental: Fundamental,
        price_history: List[PriceBar],
        metadata: Dict[str, Any],
    ) -> StrategicRoute:
        """Assigns the most fitting strategic route based on stock characteristics."""
        
        gov_score = metadata.get("governance_score", 80.0)
        eligible_routes = metadata.get("route_eligibility", ["Route Alpha"])

        # Check Route Gamma first (Regulatory compliance leader)
        if "Route Gamma" in eligible_routes and gov_score >= 90.0:
            return StrategicRoute.ROUTE_GAMMA

        # Check Route Beta (Contra-Cyclical Raid)
        if "Route Beta" in eligible_routes:
            if fundamental.debt_to_equity >= 2.0 or fundamental.pe_ratio < 15.0:
                return StrategicRoute.ROUTE_BETA

        # Default to Route Alpha (Defensive Moat)
        return StrategicRoute.ROUTE_ALPHA
