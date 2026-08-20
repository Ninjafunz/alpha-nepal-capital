"""Tests for Constitutional Strategy Compliance Monitor."""
from src.strategy.policy import InvestmentPolicy
from src.portfolio.engine import PortfolioEngine
from src.governance.compliance import ComplianceMonitor


def test_compliance_fresh_portfolio():
    policy = InvestmentPolicy()
    portfolio = PortfolioEngine(policy, initial_cash=100000000.0)
    monitor = ComplianceMonitor(policy)

    checks, score = monitor.check_compliance("2026-08-20", portfolio)
    assert len(checks) >= 6
    assert score == 100.0
    for c in checks:
        assert c.passed is True
        assert c.severity == "PASS"
