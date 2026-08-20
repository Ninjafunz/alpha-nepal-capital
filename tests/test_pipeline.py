"""Tests for DecisionPipeline and autonomous decision generation."""
from src.strategy.policy import InvestmentPolicy
from src.data.store import DataStore
from src.decision.pipeline import DecisionPipeline
from src.portfolio.engine import PortfolioEngine
from src.data.models import Stock, PriceBar, Fundamental, ActionType


def test_decision_pipeline_cycle(tmp_path):
    db_path = str(tmp_path / "test_sim.db")
    store = DataStore(db_path=db_path)
    policy = InvestmentPolicy()
    portfolio = PortfolioEngine(policy, profile_id="P1_DOMESTIC_EQUITY", initial_cash=100000000.0)

    stock = Stock(symbol="NABIL", name="Nabil Bank", sector="Commercial Bank", paid_up_capital_cr=2705.69)
    bar = PriceBar(
        symbol="NABIL",
        trade_date="2026-08-20",
        open=590.0,
        high=605.0,
        low=588.0,
        close=595.0,
        volume=25000,
        turnover=14875000.0,
        prev_close=590.0,
        pct_change=0.85,
    )
    fund = Fundamental(
        symbol="NABIL",
        as_of_date="2026-08-20",
        pe_ratio=14.0,
        pb_ratio=1.5,
        eps=45.0,
        book_value=350.0,
        roe=18.0,
        dividend_yield_pct=15.0,
        debt_to_equity=5.0,
    )

    pipeline = DecisionPipeline(policy, store)
    decisions, meta = pipeline.run_cycle(
        trade_date="2026-08-20",
        universe=[stock],
        prices={"NABIL": bar},
        funds={"NABIL": fund},
        portfolios={"P1_DOMESTIC_EQUITY": portfolio},
    )

    assert len(decisions) >= 1
    d = decisions[0]
    assert d.symbol == "NABIL"
    assert d.action in (ActionType.BUY, ActionType.HOLD)
    assert d.estimated_price > 0
    assert d.intrinsic_value_est > 0
