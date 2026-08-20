"""Tests for JSON Bridge static file generation."""
import tempfile
import json
from pathlib import Path
from src.strategy.policy import InvestmentPolicy
from src.data.store import DataStore
from src.portfolio.engine import PortfolioEngine
from src.export.json_bridge import JsonBridge
from src.data.models import PortfolioSnapshot, CompanyStatus, MarketRegime


def test_json_bridge_export(tmp_path):
    policy = InvestmentPolicy()
    db_file = tmp_path / "test.db"
    store = DataStore(db_path=str(db_file))
    portfolio = PortfolioEngine(policy, profile_id="P1_DOMESTIC_EQUITY", initial_cash=100000000.0)
    
    bs = portfolio.get_balance_sheet("2026-08-20")
    inc = portfolio.get_income_statement("Daily", "2026-08-20", [])
    snap = PortfolioSnapshot(
        trade_date="2026-08-20",
        timestamp="2026-08-20T11:00:00",
        total_assets=100000000.0,
        cash=100000000.0,
        invested_value=0.0,
        cash_weight_pct=100.0,
        shares_outstanding=10000000.0,
        nav_per_share=10.0,
        total_nav=100000000.0,
        daily_return_pct=0.0,
        cumulative_return_pct=0.0,
        high_water_mark=100000000.0,
        drawdown_pct=0.0,
        annualized_volatility_pct=12.5,
        sharpe_ratio=1.2,
        compliance_score_pct=100.0,
        status=CompanyStatus.FLOURISHING,
        market_regime=MarketRegime.BULL,
        holdings_count=0,
    )
    store.save_snapshot(snap)

    export_dir = tmp_path / "website_data"
    bridge = JsonBridge(policy, store, output_dir=str(export_dir))
    bridge.export_all(portfolio, snap, bs, inc, {"timestamp": "2026-08-20T11:00:00", "pct_change": 0.5})

    assert (export_dir / "company.json").exists()
    assert (export_dir / "portfolio.json").exists()
    assert (export_dir / "performance.json").exists()
    assert (export_dir / "financials.json").exists()
    assert (export_dir / "clocks.json").exists()

    with open(export_dir / "company.json", "r", encoding="utf-8") as f:
        comp_data = json.load(f)
        assert comp_data["name"] == "Alpha Global Capital"
        assert comp_data["status"] == "FLOURISHING"
