"""CLI Application for Alpha Nepal Capital (Institutional Multi-Asset Edition)."""
import argparse
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from src.strategy.policy import InvestmentPolicy
from src.data.store import DataStore
from src.data.models import Stock, PriceBar, Fundamental, PortfolioSnapshot, CompanyStatus, MarketRegime
from src.data.nepse_client import NepseClient
from src.data.sharesansar import ShareSansarScraper
from src.portfolio.engine import PortfolioEngine
from src.data.global_markets import GlobalMarketsAPI
from src.governance.reflection import ReflectionEngine
from src.decision.pipeline import DecisionPipeline
from src.governance.compliance import ComplianceMonitor
from src.strategy.unified_risk import UnifiedRiskManager
from src.reporting.executive_memo import GlobalExecutiveMemo
from src.benchmarks.tracker import BenchmarkTracker
from src.reporting.daily import DailyReporter
from src.reporting.monthly import MonthlyReporter
from src.reporting.timeline import TimelineManager
from src.export.json_bridge import JsonBridge


def _load_universe_metadata() -> dict:
    base_dir = Path(__file__).resolve().parent.parent
    universe_path = base_dir / "config" / "universe.yaml"
    with open(universe_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {s["symbol"]: s for s in data.get("securities", [])}


def _get_universe_stocks() -> List[Stock]:
    meta = _load_universe_metadata()
    return [
        Stock(
            symbol=s["symbol"],
            name=s["name"],
            sector=s["sector"],
            category=s.get("category", "A"),
            paid_up_capital_cr=s.get("paid_up_capital_cr", 0.0),
            asset_class=s.get("asset_class", "EQUITY_DOMESTIC"),
            avg_daily_volume_usd=s.get("avg_daily_volume_usd", 15000000.0)
        )
        for s in meta.values()
    ]


def run_daily_command(trade_date: Optional[str] = None, use_live: bool = True):
    if trade_date is None:
        trade_date = date.today().isoformat()

    print("=" * 80)
    print(f"ALPHA NEPAL CAPITAL — Global Multi-Asset Investment Cycle")
    print(f"Trade Date: {trade_date} | Autonomy Level: Level 3 (Autonomous)")
    print("=" * 80)

    policy = InvestmentPolicy()
    store = DataStore()
    timeline = TimelineManager(store)
    timeline.ensure_genesis_event()

    # 1. Load Universe
    universe_stocks = _get_universe_stocks()
    store.save_stocks(universe_stocks)
    metadata_dict = _load_universe_metadata()

    # 2. Ingest Market Data
    print("\n[1/7] Ingesting NEPSE and Global Multi-Asset market prices...")
    client = NepseClient(use_live=use_live)
    bars = client.fetch_today_prices(universe_stocks, trade_date)
    
    # Global Prices via yfinance
    global_api = GlobalMarketsAPI()
    global_bars = global_api.fetch_global_prices(universe_stocks)
    bars.extend(global_bars)
    
    store.save_price_bars(bars)
    price_dict = {b.symbol: b for b in bars}

    # Fetch Fundamentals (Domestic Equities)
    print("[2/7] Ingesting audited company fundamentals...")
    scraper = ShareSansarScraper()
    domestic_stocks = [s for s in universe_stocks if s.asset_class == "EQUITY_DOMESTIC"]
    funds = scraper.fetch_fundamentals(domestic_stocks, trade_date)
    store.save_fundamentals(funds)
    fund_dict = {f.symbol: f for f in funds}

    # 3. Load Portfolio State for 4 Profiles
    portfolios = {}
    for p in policy.company.profiles:
        portfolios[p.id] = PortfolioEngine(policy, profile_id=p.id)
        
    all_txs = store.get_all_transactions()
    for tx in all_txs:
        p_id = getattr(tx, 'profile_id', 'P1_DOMESTIC_EQUITY')
        if p_id in portfolios:
            stk = next((s for s in universe_stocks if s.symbol == tx.symbol), None)
            portfolios[p_id].execute_transaction(tx, stk)
            
    for p_id, p_engine in portfolios.items():
        p_engine.mark_to_market(price_dict, {s.symbol: s for s in universe_stocks})

    # 4. Run Master Multi-Asset SAA & Tactical Tilt Pipeline
    print("[3/7] Executing AI Pipeline (Regime Detection, SAA Tilts, Unified Risk Overrides)...")
    pipeline = DecisionPipeline(policy, store)
    decisions, cycle_metadata = pipeline.run_cycle(trade_date, universe_stocks, price_dict, fund_dict, portfolios)
    for d in decisions:
        store.record_decision(d)
    
    # 5. Financial Accounting & Consolidated Valuation
    total_assets = sum(p.get_total_assets() for p in portfolios.values())
    balance_sheet = portfolios['P1_DOMESTIC_EQUITY'].get_balance_sheet(trade_date)
    balance_sheet.total_assets = total_assets
    balance_sheet.equity_investments_market_value = sum(
        sum(h.current_value for h in p.holdings.values()) for p in portfolios.values()
    )
    balance_sheet.cash_and_equivalents = sum(p.cash for p in portfolios.values())
    balance_sheet.nav_per_share = round(total_assets / policy.company.company.total_shares_issued, 4)

    income_stmt = portfolios["P1_DOMESTIC_EQUITY"].get_income_statement("Daily", trade_date, [])
    
    # 5.5 Reflection & Journaling
    print("[4/7] Generating Self-Reflection Post-Mortems and Win-Rate analytics...")
    reflection_engine = ReflectionEngine(policy)
    reflections = []
    for p_engine in portfolios.values():
        reflections.extend(reflection_engine.evaluate_holdings(p_engine.holdings))
    
    # 6. Comprehensive Multi-Asset Governance Audit
    print("[5/7] Verifying Constitutional Strategy Compliance & Global Risk Overrides...")
    holdings_by_class = {}
    holdings_by_sym = {}
    for p in portfolios.values():
        for h in p.holdings.values():
            stk = next((s for s in universe_stocks if s.symbol == h.symbol), None)
            ac = stk.asset_class if stk else "EQUITY_DOMESTIC"
            holdings_by_class[ac] = holdings_by_class.get(ac, 0.0) + h.current_value
            holdings_by_sym[h.symbol] = holdings_by_sym.get(h.symbol, 0.0) + h.current_value

    risk_mgr_unified = UnifiedRiskManager(policy)
    fx_hedge_active = cycle_metadata.get("fx_eval", {}).get("hedge_triggered", False)
    governance_audit = risk_mgr_unified.run_full_governance_audit(
        total_nav_npr=total_assets,
        holdings_by_class=holdings_by_class,
        holdings_by_symbol=holdings_by_sym,
        fx_hedge_active=fx_hedge_active
    )

    compliance_mon = ComplianceMonitor(policy)
    checks, compliance_score = compliance_mon.check_compliance(trade_date, portfolios["P1_DOMESTIC_EQUITY"])
    store.record_compliance_checks(checks)

    # 7. Benchmark Portfolios Update
    print("[6/7] Calculating Comparative Multi-Asset Benchmarks...")
    index_data = client.fetch_nepse_index(trade_date)
    bm_tracker = BenchmarkTracker(store, 100000000.0)
    bm_tracker.update_daily_benchmarks(
        trade_date=trade_date,
        ai_current_nav=balance_sheet.nav_per_share,
        price_dict=price_dict,
        nepse_index_val=index_data["current_value"],
    )

    # 8. Snapshot Portfolio State
    snapshots = store.get_all_snapshots()
    nav_calc = portfolios["P1_DOMESTIC_EQUITY"].nav_engine.calculate_nav(balance_sheet.total_assets)
    prev_nav_history = [s.total_nav for s in snapshots] + [balance_sheet.total_assets]
    from src.strategy.risk import RiskManager
    risk_mgr = RiskManager(policy)
    dd_info = risk_mgr.calculate_drawdown(prev_nav_history)
    vol_pct = risk_mgr.calculate_volatility([b.pct_change / 100.0 for b in bars])
    regime = risk_mgr.determine_regime([b.pct_change / 100.0 for b in bars])
    status = risk_mgr.evaluate_company_status(
        nav_calc["total_return_pct"],
        nav_calc["total_return_pct"] - index_data["pct_change"],
        dd_info["drawdown_pct"],
    )

    daily_ret = 0.0
    if snapshots:
        daily_ret = round(((balance_sheet.nav_per_share - snapshots[-1].nav_per_share) / snapshots[-1].nav_per_share) * 100.0, 2)

    total_holdings_count = sum(len(p.holdings) for p in portfolios.values())
    snapshot = PortfolioSnapshot(
        trade_date=trade_date,
        timestamp=datetime.now().isoformat(),
        total_assets=balance_sheet.total_assets,
        cash=balance_sheet.cash_and_equivalents,
        invested_value=balance_sheet.equity_investments_market_value,
        cash_weight_pct=round((balance_sheet.cash_and_equivalents / max(1.0, balance_sheet.total_assets)) * 100.0, 2),
        shares_outstanding=policy.company.company.total_shares_issued,
        nav_per_share=balance_sheet.nav_per_share,
        total_nav=balance_sheet.total_assets,
        daily_return_pct=daily_ret,
        cumulative_return_pct=nav_calc["total_return_pct"],
        high_water_mark=dd_info["high_water_mark"],
        drawdown_pct=dd_info["drawdown_pct"],
        annualized_volatility_pct=vol_pct,
        sharpe_ratio=round((nav_calc["total_return_pct"] - 6.0) / max(1.0, vol_pct), 2),
        compliance_score_pct=governance_audit["compliance_score_pct"],
        status=status,
        market_regime=regime,
        holdings_count=total_holdings_count,
    )
    store.save_snapshot(snapshot)

    # 9. Generate Global Executive Memo
    all_holdings_list = []
    for p in portfolios.values():
        for h in p.holdings.values():
            stk = next((s for s in universe_stocks if s.symbol == h.symbol), None)
            all_holdings_list.append({
                "symbol": h.symbol,
                "asset_class": stk.asset_class if stk else "EQUITY_DOMESTIC",
                "current_value": h.current_value,
                "quantity": h.quantity,
                "current_price": h.current_price,
                "unrealized_pnl": h.unrealized_pnl,
                "route": h.route.value if hasattr(h.route, "value") else str(h.route)
            })

    fx_rate = cycle_metadata.get("macro_signals", {}).get("usd_npr_rate", 135.20)
    cash_npr_amt = portfolios["P1_DOMESTIC_EQUITY"].cash
    cash_usd_amt = sum(p.cash for p_id, p in portfolios.items() if p_id != "P1_DOMESTIC_EQUITY") / fx_rate

    memo_dict = GlobalExecutiveMemo.generate_memo(
        trade_date=trade_date,
        total_nav_npr=total_assets,
        cash_npr=cash_npr_amt,
        cash_usd=cash_usd_amt,
        fx_rate=fx_rate,
        total_return_pct=nav_calc["total_return_pct"],
        benchmark_return_pct=index_data.get("pct_change", 0.0),
        company_status=status.value,
        regime_info=cycle_metadata.get("regime_info", {}),
        saa_calibration=cycle_metadata.get("saa_calibration", {}),
        governance_audit=governance_audit,
        decisions=decisions,
        holdings=all_holdings_list,
        fx_hedge_active=fx_hedge_active
    )

    # 10. Export State to Static Website Bridge
    print("[7/7] Exporting state to JSON bridge for GitHub Pages website...")
    bridge = JsonBridge(policy, store)
    bridge.export_all(
        portfolio=portfolios["P1_DOMESTIC_EQUITY"],
        latest_snapshot=snapshot,
        balance_sheet=balance_sheet,
        income_statement=income_stmt,
        nepse_index_data=index_data,
        all_portfolios=portfolios
    )
    bridge.export_global_memo(memo_dict)
    bridge.export_macro(cycle_metadata)
    
    # Export Journal and Profile Race
    all_txs_for_wr = store.get_all_transactions()
    win_rate = reflection_engine.calculate_win_rate(all_txs_for_wr)
    bridge.export_journal(reflections, win_rate)
    bridge.export_profile_race(portfolios, policy.company.profiles)

    # Print Executive Memo to Terminal
    print("\n" + GlobalExecutiveMemo.format_cli_memo(memo_dict))


def memo_command():
    base_dir = Path(__file__).resolve().parent.parent
    memo_path = base_dir / "website" / "data" / "global_memo.json"
    if not memo_path.exists():
        print("No Global Executive Memo generated yet. Run `python -m src.cli run-daily` first.")
        return
    with open(memo_path, "r", encoding="utf-8") as f:
        memo = json.load(f)
    print(GlobalExecutiveMemo.format_cli_memo(memo))


def status_command():
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No daily snapshots recorded yet. Run `python -m src.cli run-daily` first.")
        return

    latest = snapshots[-1]
    policy = InvestmentPolicy()
    
    print("\n" + "=" * 80)
    print(f"ALPHA NEPAL CAPITAL — {latest.status.value}")
    print(f"Total Consolidated Assets: NPR {latest.total_assets:,.2f} | NAV/Share: NPR {latest.nav_per_share:.4f}")
    print(f"Cumulative Return: {latest.cumulative_return_pct:+.2f}% | Strategy Compliance: {latest.compliance_score_pct:.1f}%")
    print("=" * 80)

    universe_stocks = _get_universe_stocks()
    prices = store.get_latest_prices()
    
    portfolios = {}
    for p in policy.company.profiles:
        portfolios[p.id] = PortfolioEngine(policy, profile_id=p.id)
        
    for tx in store.get_all_transactions():
        p_id = getattr(tx, 'profile_id', 'P1_DOMESTIC_EQUITY')
        if p_id in portfolios:
            stk = next((s for s in universe_stocks if s.symbol == tx.symbol), None)
            portfolios[p_id].execute_transaction(tx, stk)
            
    for p_id, p_eng in portfolios.items():
        p_eng.mark_to_market(prices, {s.symbol: s for s in universe_stocks})
        print(f"\n--- {p_id} Holdings (Total: NPR {p_eng.get_total_assets():,.2f}) ---")
        print(f"{'Symbol':<10} {'Sector':<22} {'Qty':>10} {'Price':>12} {'Market Val (NPR)':>18} {'Route':<15}")
        print("-" * 92)
        for h in p_eng.holdings.values():
            route_str = h.route.value if hasattr(h.route, "value") else str(h.route)
            print(f"{h.symbol:<10} {h.sector[:21]:<22} {h.quantity:>10,d} {h.current_price:>12,.2f} {h.current_value:>18,.2f} {route_str:<15}")


def balance_sheet_command():
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No snapshots available.")
        return
    latest = snapshots[-1]
    policy = InvestmentPolicy()
    portfolio = PortfolioEngine(policy, initial_cash=latest.cash)
    bs = portfolio.get_balance_sheet(latest.trade_date)
    bs.total_assets = latest.total_assets
    print("\n" + "=" * 60)
    print(f"CONSOLIDATED BALANCE SHEET — {latest.trade_date}")
    print("=" * 60)
    print(f"Cash & Equivalents:          NPR {latest.cash:,.2f}")
    print(f"Invested Market Value:       NPR {latest.invested_value:,.2f}")
    print(f"Total Assets:                NPR {latest.total_assets:,.2f}")
    print(f"Net Asset Value (NAV)/Share: NPR {latest.nav_per_share:.4f}")
    print("=" * 60)


def compliance_command():
    store = DataStore()
    checks = store.get_latest_compliance()
    if not checks:
        print("No compliance checks recorded.")
        return
    print("\n" + "=" * 80)
    print("CONSTITUTIONAL COMPLIANCE AUDIT")
    print("=" * 80)
    for c in checks:
        status = "PASS" if c.passed else "BREACH"
        print(f"[{status}] {c.rule_id} — {c.rule_name}: Actual={c.current_value:.1f}% (Limit: {c.threshold_desc})")
    print("=" * 80)


def decisions_command():
    store = DataStore()
    decs = store.get_recent_decisions(limit=15)
    if not decs:
        print("No decisions recorded yet.")
        return
    print("\n" + "=" * 80)
    print("RECENT AI DECISIONS & TACTICAL TILTS")
    print("=" * 80)
    for d in decs:
        route_str = d.route.value if hasattr(d.route, "value") else str(d.route)
        print(f"[{d.trade_date}] {d.action.value} {d.symbol} | Route: {route_str} | Delta: {d.cognitive_delta_score:.1f}% | Executed: {d.executed}")
        print(f"  Memo: {d.reason_summary}")
    print("=" * 80)


def benchmark_command():
    store = DataStore()
    bms = store.get_all_benchmarks()
    if not bms:
        print("No benchmark records found.")
        return
    print("\n" + "=" * 80)
    print(f"{'Date':<12} {'AI Return':<12} {'Human Static':<15} {'NEPSE Index':<15} {'Equal-Weight':<15}")
    print("-" * 80)
    for b in bms[-10:]:
        print(f"{b.trade_date:<12} {b.ai_company_return_pct:>+10.2f}% {b.human_strategy_return_pct:>+13.2f}% {b.nepse_return_pct:>+13.2f}% {b.equal_weight_return_pct:>+13.2f}%")
    print("=" * 80)


def report_monthly_command(period_str: str = "2026-08"):
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No snapshots available.")
        return
    latest = snapshots[-1]
    policy = InvestmentPolicy()
    portfolio = PortfolioEngine(policy, initial_cash=latest.cash)
    bs = portfolio.get_balance_sheet(latest.trade_date)
    bs.total_assets = latest.total_assets
    income_stmt = portfolio.get_income_statement(period_str, latest.trade_date, store.get_all_transactions())

    report_dict = MonthlyReporter.generate_monthly_report(
        period_str=period_str,
        as_of_date=latest.trade_date,
        start_nav=10.0,
        end_nav=latest.nav_per_share,
        balance_sheet=bs,
        income_stmt=income_stmt,
        transactions=store.get_all_transactions(),
        decisions=store.get_recent_decisions(100),
        compliance_score=latest.compliance_score_pct,
        nepse_return_pct=1.45,
        management_outlook="Operating with disciplined multi-asset SAA and regime-adaptive tactical tilts.",
    )

    base_dir = Path(__file__).resolve().parent.parent
    report_file = base_dir / "website" / "data" / "reports" / f"{period_str}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    print(f"[OK] Monthly CEO report for {period_str} generated and archived in {report_file}!")


def main():
    parser = argparse.ArgumentParser(description="Alpha Nepal Capital CLI — Institutional Multi-Asset Edition")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run-daily
    run_daily_parser = subparsers.add_parser("run-daily", help="Run full daily multi-asset simulation cycle")
    run_daily_parser.add_argument("--date", type=str, default=None, help="Trade date (YYYY-MM-DD)")
    run_daily_parser.add_argument("--no-live", action="store_true", help="Bypass live API requests")

    # memo
    subparsers.add_parser("memo", help="Print the latest Global Executive Memo")

    # status
    subparsers.add_parser("status", help="View multi-asset holdings across all portfolios")

    # balance-sheet
    subparsers.add_parser("balance-sheet", help="Print consolidated balance sheet")

    # compliance
    subparsers.add_parser("compliance", help="View strategy compliance checklist")

    # decisions
    subparsers.add_parser("decisions", help="View recent AI decisions and tactical tilts")

    # benchmark
    subparsers.add_parser("benchmark", help="Compare performance against 4 benchmarks")

    # report-monthly
    monthly_parser = subparsers.add_parser("report-monthly", help="Generate monthly CEO report")
    monthly_parser.add_argument("--period", type=str, default="2026-08", help="Month in YYYY-MM")

    args = parser.parse_args()

    if args.command == "run-daily":
        run_daily_command(trade_date=args.date, use_live=not args.no_live)
    elif args.command == "memo":
        memo_command()
    elif args.command == "status":
        status_command()
    elif args.command == "balance-sheet":
        balance_sheet_command()
    elif args.command == "compliance":
        compliance_command()
    elif args.command == "decisions":
        decisions_command()
    elif args.command == "benchmark":
        benchmark_command()
    elif args.command == "report-monthly":
        report_monthly_command(period_str=args.period)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
