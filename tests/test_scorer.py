"""Tests for the 3-Layer ASA-V1.ethics Strategy Scorer."""
from src.strategy.policy import InvestmentPolicy
from src.strategy.scorer import StrategyScorer
from src.data.models import Stock, PriceBar, Fundamental, StrategicRoute


def test_scorer_all_layers():
    policy = InvestmentPolicy()
    scorer = StrategyScorer(policy)

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
        pct_change=0.85
    )
    fund = Fundamental(
        symbol="NABIL",
        as_of_date="2026-08-20",
        pe_ratio=16.4,
        pb_ratio=1.82,
        eps=36.2,
        book_value=326.5,
        roe=12.8,
        dividend_yield_pct=10.5,
        debt_to_equity=6.8,
    )
    meta = {
        "bottleneck_score": 88.0,
        "elite_alignment": 85.0,
        "governance_score": 92.0,
        "route_eligibility": ["Route Alpha", "Route Gamma"]
    }

    result = scorer.evaluate_security(stock, bar, fund, [bar], meta)

    assert result["symbol"] == "NABIL"
    assert 0.0 <= result["final_score"] <= 100.0
    assert result["structural"]["structural_composite"] > 0.0
    assert result["literature"]["literature_composite"] > 0.0
    assert result["cognitive"]["cognitive_delta_score"] > 0.0
    assert result["intrinsic_value"] > 0.0
    assert isinstance(result["route"], StrategicRoute)
