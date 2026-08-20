"""Portfolio Risk Manager and constraint validator."""
from typing import List, Dict, Any, Optional
import numpy as np

from src.data.models import PortfolioHolding, MarketRegime, CompanyStatus
from src.strategy.policy import InvestmentPolicy


class RiskManager:
    """Calculates portfolio-level risk metrics and validates against IPS risk constraints."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.constraints = policy.constraints

    def calculate_volatility(self, daily_returns: List[float]) -> float:
        """Returns annualized volatility percentage."""
        if len(daily_returns) < 5:
            return 12.5  # Baseline default annualized volatility
        std = float(np.std(daily_returns))
        annualized = std * np.sqrt(240) * 100.0  # Approx 240 trading days on NEPSE
        return round(float(annualized), 2)

    def calculate_drawdown(self, nav_history: List[float]) -> Dict[str, float]:
        """Calculates current drawdown percentage from high-water mark."""
        if not nav_history:
            return {"high_water_mark": 100000000.0, "drawdown_pct": 0.0}

        hwm = max(nav_history)
        current = nav_history[-1]
        dd = ((hwm - current) / hwm) * 100.0 if hwm > 0 else 0.0
        return {
            "high_water_mark": round(float(hwm), 2),
            "drawdown_pct": round(float(dd), 2),
        }

    def determine_regime(self, index_returns: List[float]) -> MarketRegime:
        """Detects current market regime from index return series."""
        if len(index_returns) < 10:
            return MarketRegime.BULL
        
        cum_ret = sum(index_returns[-20:])
        vol = float(np.std(index_returns[-20:])) * np.sqrt(240)

        if vol > 0.30:
            return MarketRegime.HIGH_VOLATILITY
        if cum_ret > 0.03:
            return MarketRegime.BULL
        elif cum_ret < -0.03:
            return MarketRegime.BEAR
        else:
            return MarketRegime.SIDEWAYS

    def evaluate_company_status(
        self,
        total_return_pct: float,
        alpha_pct: float,
        drawdown_pct: float,
    ) -> CompanyStatus:
        """Determines company status (FLOURISHING, STABLE, DECLINING, CRITICAL)."""
        if total_return_pct >= 3.0 and alpha_pct >= 0.0 and drawdown_pct <= 10.0:
            return CompanyStatus.FLOURISHING
        elif total_return_pct >= -3.0 and drawdown_pct <= 12.0:
            return CompanyStatus.STABLE
        elif total_return_pct < -10.0:
            return CompanyStatus.CRITICAL
        else:
            return CompanyStatus.DECLINING
