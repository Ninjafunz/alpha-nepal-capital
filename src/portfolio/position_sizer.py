"""Position Sizing Engine respecting route allocation and portfolio limits."""
from typing import Dict, Any, Optional
from src.data.models import Stock, PriceBar, StrategicRoute
from src.strategy.policy import InvestmentPolicy


class PositionSizer:
    """Calculates permissible capital allocation and share quantity per trade."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.constraints = policy.constraints

    def calculate_order_size(
        self,
        symbol: str,
        price: float,
        score: float,
        delta_pct: float,
        route: StrategicRoute,
        is_aggressive: bool,
        current_cash: float,
        total_assets: float,
        current_position_value: float,
        current_sector_value: float,
    ) -> Dict[str, Any]:
        """Determines target NPR allocation and share count within hard constraint limits."""
        
        # 1. Check Cash Availability (must preserve 5% min cash)
        min_cash_buffer = total_assets * (self.constraints.min_cash_pct / 100.0)
        available_cash = max(0.0, current_cash - min_cash_buffer)
        if available_cash <= 0:
            return {"allowed": False, "target_npr": 0.0, "quantity": 0, "reason": "Cash buffer breached"}

        # 2. Check Single Stock Headroom (Max 25%)
        max_stock_val = total_assets * (self.constraints.max_single_position_pct / 100.0)
        stock_headroom = max(0.0, max_stock_val - current_position_value)

        # 3. Check Sector Headroom (Max 40%)
        max_sector_val = total_assets * (self.constraints.max_sector_pct / 100.0)
        sector_headroom = max(0.0, max_sector_val - current_sector_value)

        # 4. Desired Allocation based on Route and Cognitive Delta
        if is_aggressive:
            desired_pct = 0.15  # 15% allocation for Delta > 50%
        elif route == StrategicRoute.ROUTE_ALPHA:
            desired_pct = 0.10  # 10% allocation for Route Alpha
        elif route == StrategicRoute.ROUTE_BETA:
            desired_pct = 0.07  # 7% allocation for Route Beta
        elif route == StrategicRoute.ROUTE_GAMMA:
            desired_pct = 0.08  # 8% allocation for Route Gamma
        else:
            desired_pct = 0.05

        desired_npr = total_assets * desired_pct

        # Apply hard constraints (min of desired, available cash, stock headroom, sector headroom)
        allocated_npr = min(desired_npr, available_cash, stock_headroom, sector_headroom)

        # Minimum position threshold check (2% of total assets)
        min_pos_npr = total_assets * (self.constraints.min_position_size_pct / 100.0)
        if allocated_npr < min_pos_npr:
            return {"allowed": False, "target_npr": 0.0, "quantity": 0, "reason": "Below minimum 2% position size"}

        quantity = int(allocated_npr // price)
        if quantity <= 0:
            return {"allowed": False, "target_npr": 0.0, "quantity": 0, "reason": "Insufficient capital for 1 share"}

        actual_npr = round(quantity * price, 2)

        return {
            "allowed": True,
            "target_npr": actual_npr,
            "quantity": quantity,
            "reason": "Passed all headroom and cash constraint checks",
        }
