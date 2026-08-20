"""Compliance Monitor and Strategy Obedience Scorer."""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Tuple

from src.data.models import ComplianceRecord, PortfolioHolding
from src.strategy.policy import InvestmentPolicy
from src.portfolio.engine import PortfolioEngine


class ComplianceMonitor:
    """Evaluates portfolio state against the Investment Policy Statement (The Constitution).
    Produces Strategy Obedience Score: (Rules Followed / Total Applicable Rules) * 100.
    """

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.constraints = policy.constraints

    def check_compliance(
        self,
        trade_date: str,
        portfolio: PortfolioEngine,
        current_volatility_pct: float = 14.5,
        current_drawdown_pct: float = 0.0,
    ) -> Tuple[List[ComplianceRecord], float]:
        """Runs all constitutional rules and returns compliance records + aggregate obedience score."""
        
        checks: List[ComplianceRecord] = []
        total_assets = portfolio.get_total_assets()
        cash_pct = round((portfolio.cash / max(1.0, total_assets)) * 100.0, 2)
        sector_exposures = portfolio.get_sector_exposures()

        # Rule 1: Max Single Position Limit (25%)
        max_holding_pct = max([h.weight_pct for h in portfolio.holdings.values()]) if portfolio.holdings else 0.0
        r1_pass = (max_holding_pct <= self.constraints.max_single_position_pct)
        checks.append(ComplianceRecord(
            id=f"COMP-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now().isoformat(),
            trade_date=trade_date,
            rule_id="RULE-POS-01",
            rule_name="Max Single Position Exposure",
            threshold_desc=f"<= {self.constraints.max_single_position_pct}%",
            current_value=max_holding_pct,
            limit_value=self.constraints.max_single_position_pct,
            passed=r1_pass,
            severity="PASS" if r1_pass else "BREACH",
            message=f"Highest single stock weight is {max_holding_pct:.1f}% (Limit: {self.constraints.max_single_position_pct}%)",
        ))

        # Rule 2: Max Sector Exposure Limit (40%)
        max_sector_pct = max(sector_exposures.values()) if sector_exposures else 0.0
        r2_pass = (max_sector_pct <= self.constraints.max_sector_pct)
        checks.append(ComplianceRecord(
            id=f"COMP-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now().isoformat(),
            trade_date=trade_date,
            rule_id="RULE-SEC-02",
            rule_name="Max Sector Concentration",
            threshold_desc=f"<= {self.constraints.max_sector_pct}%",
            current_value=max_sector_pct,
            limit_value=self.constraints.max_sector_pct,
            passed=r2_pass,
            severity="PASS" if r2_pass else "BREACH",
            message=f"Highest sector concentration is {max_sector_pct:.1f}% (Limit: {self.constraints.max_sector_pct}%)",
        ))

        # Rule 3: Minimum Cash Buffer (5%)
        r3_pass = (cash_pct >= self.constraints.min_cash_pct)
        checks.append(ComplianceRecord(
            id=f"COMP-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now().isoformat(),
            trade_date=trade_date,
            rule_id="RULE-CASH-03",
            rule_name="Minimum Cash Liquidity Reserve",
            threshold_desc=f">= {self.constraints.min_cash_pct}%",
            current_value=cash_pct,
            limit_value=self.constraints.min_cash_pct,
            passed=r3_pass,
            severity="PASS" if r3_pass else "BREACH",
            message=f"Cash balance at {cash_pct:.1f}% of total assets (Floor: {self.constraints.min_cash_pct}%)",
        ))

        # Rule 4: Maximum Drawdown Defensive Trigger (15%)
        r4_pass = (current_drawdown_pct <= self.constraints.max_drawdown_defensive_pct)
        checks.append(ComplianceRecord(
            id=f"COMP-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now().isoformat(),
            trade_date=trade_date,
            rule_id="RULE-DD-04",
            rule_name="Maximum Drawdown Guardrail",
            threshold_desc=f"<= {self.constraints.max_drawdown_defensive_pct}%",
            current_value=current_drawdown_pct,
            limit_value=self.constraints.max_drawdown_defensive_pct,
            passed=r4_pass,
            severity="PASS" if r4_pass else "WARNING",
            message=f"Portfolio drawdown is {current_drawdown_pct:.1f}% (Defensive Trigger: {self.constraints.max_drawdown_defensive_pct}%)",
        ))

        # Rule 5: Maximum Annualized Volatility (20%)
        r5_pass = (current_volatility_pct <= self.constraints.max_portfolio_volatility_annual)
        checks.append(ComplianceRecord(
            id=f"COMP-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now().isoformat(),
            trade_date=trade_date,
            rule_id="RULE-VOL-05",
            rule_name="Portfolio Annualized Volatility",
            threshold_desc=f"<= {self.constraints.max_portfolio_volatility_annual}%",
            current_value=current_volatility_pct,
            limit_value=self.constraints.max_portfolio_volatility_annual,
            passed=r5_pass,
            severity="PASS" if r5_pass else "WARNING",
            message=f"Annualized volatility is {current_volatility_pct:.1f}% (Cap: {self.constraints.max_portfolio_volatility_annual}%)",
        ))

        # Rule 6: Maximum Concurrent Holdings Limit (15)
        pos_count = len(portfolio.holdings)
        r6_pass = (pos_count <= self.constraints.max_positions)
        checks.append(ComplianceRecord(
            id=f"COMP-{uuid.uuid4().hex[:6].upper()}",
            timestamp=datetime.now().isoformat(),
            trade_date=trade_date,
            rule_id="RULE-HOLD-06",
            rule_name="Max Position Diversification Cap",
            threshold_desc=f"<= {self.constraints.max_positions} holdings",
            current_value=float(pos_count),
            limit_value=float(self.constraints.max_positions),
            passed=r6_pass,
            severity="PASS" if r6_pass else "BREACH",
            message=f"Active holdings count is {pos_count} (Cap: {self.constraints.max_positions})",
        ))

        passed_count = sum(1 for c in checks if c.passed)
        compliance_score = round((passed_count / len(checks)) * 100.0, 1)

        return checks, compliance_score
