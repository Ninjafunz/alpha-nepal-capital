"""CLI Application for Alpha Nepal Capital (zero-dependency argparse implementation)."""
import argparse
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List

from src.strategy.policy import InvestmentPolicy
from src.data.store import DataStore
from src.data.models import Stock, PriceBar, Fundamental, PortfolioSnapshot, CompanyStatus, MarketRegime
from src.data.nepse_client import NepseClient
from src.data.sharesansar import ShareSansarScraper
from src.portfolio.engine import PortfolioEngine
from src.decision.pipeline import DecisionPipeline
from src.governance.compliance import ComplianceMonitor
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
        )
        for s in meta.values()
    ]


def run_daily_command(trade_date: Optional[str] = None, use_live: bool = True):
    if trade_date is None:
        trade_date = date.today().isoformat()

    print("=" * 80)
    print(f"ALPHA NEPAL CAPITAL — Autonomous Daily Investment Cycle")
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
    print("\n[1/6] Ingesting NEPSE market prices and index...")
    client = NepseClient(use_live=use_live)
    bars = client.fetch_today_prices(universe_stocks, trade_date)
    store.save_price_bars(bars)
    price_dict = {b.symbol: b for b in bars}

    # Fetch Fundamentals
    print("[2/6] Ingesting audited company fundamentals...")
    scraper = ShareSansarScraper()
    funds = scraper.fetch_fundamentals(universe_stocks, trade_date)
    store.save_fundamentals(funds)
    fund_dict = {f.symbol: f for f in funds}

    # 3. Load Portfolio State (Economic Memory) - Replay from Genesis Capital
    portfolio = PortfolioEngine(policy, initial_cash=policy.company.starting_capital)

    # Restore holdings and cash from immutable transaction ledger
    all_txs = store.get_all_transactions()
    for tx in all_txs:
        stk = next((s for s in universe_stocks if s.symbol == tx.symbol), None)
        if stk:
            portfolio.execute_transaction(tx, stk)

    # Mark to market with today's price
    portfolio.mark_to_market(price_dict, {s.symbol: s for s in universe_stocks})

    # 4. Run Staged Decision Hierarchy Pipeline
    print("[3/6] Executing ASA-V1.ethics Decision Pipeline (Structural -> Literature -> Cognitive Delta -> Sizing)...")
    pipeline = DecisionPipeline(policy, store, portfolio)
    cycle_res = pipeline.run_cycle(trade_date, universe_stocks, price_dict, fund_dict, metadata_dict)

    # 5. Financial Accounting & Balance Sheet
    balance_sheet = portfolio.get_balance_sheet(trade_date)
    income_stmt = portfolio.get_income_statement("Daily", trade_date, cycle_res["transactions"])

    # 6. Compliance & Governance Verification
    print("[4/6] Verifying Constitutional Strategy Compliance...")
    compliance_mon = ComplianceMonitor(policy)
    checks, compliance_score = compliance_mon.check_compliance(trade_date, portfolio)
    store.record_compliance_checks(checks)

    # 7. Benchmark Portfolios Update
    print("[5/6] Calculating 4-Portfolio Comparative Benchmarks...")
    index_data = client.fetch_nepse_index(trade_date)
    bm_tracker = BenchmarkTracker(store, policy.company.starting_capital)
    bm_tracker.update_daily_benchmarks(
        trade_date=trade_date,
        ai_current_nav=balance_sheet.nav_per_share,
        price_dict=price_dict,
        nepse_index_val=index_data["current_value"],
    )

    # 8. Snapshot Portfolio State
    snapshots = store.get_all_snapshots()
    nav_calc = portfolio.nav_engine.calculate_nav(balance_sheet.total_assets)
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

    snapshot = PortfolioSnapshot(
        trade_date=trade_date,
        timestamp=datetime.now().isoformat(),
        total_assets=balance_sheet.total_assets,
        cash=balance_sheet.cash_and_equivalents,
        invested_value=balance_sheet.equity_investments_market_value,
        cash_weight_pct=round((balance_sheet.cash_and_equivalents / max(1.0, balance_sheet.total_assets)) * 100.0, 2),
        shares_outstanding=policy.company.shares_outstanding,
        nav_per_share=balance_sheet.nav_per_share,
        total_nav=balance_sheet.total_assets,
        daily_return_pct=daily_ret,
        cumulative_return_pct=nav_calc["total_return_pct"],
        high_water_mark=dd_info["high_water_mark"],
        drawdown_pct=dd_info["drawdown_pct"],
        annualized_volatility_pct=vol_pct,
        sharpe_ratio=round((nav_calc["total_return_pct"] - 6.0) / max(1.0, vol_pct), 2),
        compliance_score_pct=compliance_score,
        status=status,
        market_regime=regime,
        holdings_count=len(portfolio.holdings),
    )
    store.save_snapshot(snapshot)

    # 9. Export State to Static Website Bridge
    print("[6/6] Exporting system state to JSON bridge for GitHub Pages website...")
    bridge = JsonBridge(policy, store)
    bridge.export_all(portfolio, snapshot, balance_sheet, income_stmt, index_data)

    print("\n" + "=" * 80)
    print(f"[OK] Daily Simulation Cycle Complete for {trade_date}!")
    print(f"Company Status: {status.value} | NAV: NPR {snapshot.nav_per_share:.4f} | Total Assets: NPR {balance_sheet.total_assets:,.2f}")
    print(f"Cumulative Return: {snapshot.cumulative_return_pct:+.2f}% | Strategy Compliance: {compliance_score:.1f}%")
    print(f"Decisions Generated: {len(cycle_res['decisions'])} | Executed Orders: {len(cycle_res['transactions'])}")
    print("=" * 80)


def status_command():
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No daily snapshots recorded yet. Run `python -m src.cli run-daily` first.")
        return

    latest = snapshots[-1]
    policy = InvestmentPolicy()
    
    print("\n" + "=" * 80)
    print(f"ALPHA NEPAL CAPITAL - {latest.status.value}")
    print(f"Total Assets: NPR {latest.total_assets:,.2f} | NAV/Share: NPR {latest.nav_per_share:.4f}")
    print(f"Cumulative Return: {latest.cumulative_return_pct:+.2f}% | Strategy Compliance: {latest.compliance_score_pct:.1f}% | Regime: {latest.market_regime.value}")
    print("=" * 80)

    portfolio = PortfolioEngine(policy, initial_cash=latest.cash)
    universe_stocks = _get_universe_stocks()
    for tx in store.get_all_transactions():
        stk = next((s for s in universe_stocks if s.symbol == tx.symbol), None)
        if stk:
            portfolio.execute_transaction(tx, stk)

    prices = store.get_latest_prices()
    portfolio.mark_to_market(prices, {s.symbol: s for s in universe_stocks})

    print(f"\n{'Symbol':<8} {'Sector':<20} {'Quantity':>10} {'Avg Price':>12} {'Current':>12} {'Market Val (NPR)':>18} {'Weight':>8} {'P&L %':>10}")
    print("-" * 102)
    for h in portfolio.holdings.values():
        print(f"{h.symbol:<8} {h.sector[:19]:<20} {h.quantity:>10,d} {h.avg_buy_price:>12,.2f} {h.current_price:>12,.2f} {h.current_value:>18,.2f} {h.weight_pct:>7.1f}% {h.unrealized_pnl_pct:>+9.1f}%")
    print("-" * 102)


def balance_sheet_command():
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No snapshots available.")
        return
    s = snapshots[-1]

    print("\n" + "=" * 60)
    print(f"ALPHA NEPAL CAPITAL - BALANCE SHEET (as of {s.trade_date})")
    print("=" * 60)
    print(f"{'Line Item':<40} {'Amount (NPR)':>18}")
    print("-" * 60)
    print(f"{'ASSETS':<40}")
    print(f"{'  Cash & Cash Equivalents':<40} {s.cash:>18,.2f}")
    print(f"{'  Equity Investments (Market Value)':<40} {s.invested_value:>18,.2f}")
    print(f"{'  Dividends Receivable':<40} {'0.00':>18}")
    print(f"{'TOTAL ASSETS':<40} {s.total_assets:>18,.2f}")
    print("-" * 60)
    print(f"{'LIABILITIES':<40}")
    print(f"{'  Total Debt / Borrowings':<40} {'0.00':>18}")
    print("-" * 60)
    print(f"{'SHAREHOLDER EQUITY':<40}")
    print(f"{'  Share Capital (10M Shares @ NPR 10)':<40} {100000000.0:>18,.2f}")
    print(f"{'  Retained Profit / (Loss)':<40} {(s.total_assets - 100000000.0):>+18,.2f}")
    print(f"{'TOTAL LIABILITIES & EQUITY':<40} {s.total_assets:>18,.2f}")
    print("=" * 60)
    print(f"{'NET ASSET VALUE (NAV) PER SHARE':<40} {f'NPR {s.nav_per_share:.4f}':>18}")
    print("=" * 60 + "\n")


def compliance_command():
    store = DataStore()
    records = store.get_latest_compliance()
    if not records:
        print("No compliance records found.")
        return

    print("\n" + "=" * 90)
    print("INVESTMENT POLICY STATEMENT (IPS) STRATEGY OBEDIENCE AUDIT")
    print("=" * 90)
    print(f"{'Rule ID':<14} {'Rule Description':<32} {'Limit':<12} {'Current':<10} {'Status':<8} {'Message'}")
    print("-" * 90)
    for r in records:
        status_str = "PASS" if r.passed else r.severity
        print(f"{r.rule_id:<14} {r.rule_name[:30]:<32} {r.threshold_desc:<12} {r.current_value:<10.1f} {status_str:<8} {r.message}")
    print("-" * 90 + "\n")


def decisions_command(limit: int = 15):
    store = DataStore()
    decs = store.get_recent_decisions(limit=limit)
    if not decs:
        print("No decisions recorded yet.")
        return

    print("\n" + "=" * 90)
    print("AI AUTONOMOUS DECISION STREAM (ASA-V1.ethics)")
    print("=" * 90)
    for d in decs:
        print(f"[{d.action.value}] {d.symbol} | Route: {d.route.value} | Confidence: {d.confidence_pct:.0f}%")
        print(f"  Target: {d.target_quantity:,} shares @ NPR {d.estimated_price:,.2f} (Alloc: NPR {d.capital_allocation_npr:,.2f})")
        print(f"  Structural: {d.structural_score:.1f} | Literature: {d.literature_score:.1f} | Cognitive Delta: +{d.delta_pct:.1f}% (Intrinsic: NPR {d.intrinsic_value_est:,.2f})")
        print(f"  Reason: {d.reason_summary}")
        print(f"  Invalidation: {d.invalidation_condition}")
        print("-" * 90)
    print()


def benchmark_command():
    store = DataStore()
    tracker = BenchmarkTracker(store)
    comp = tracker.get_summary_comparison()
    if not comp:
        print("No benchmark records available.")
        return

    print("\n" + "=" * 90)
    print("FOUR-PORTFOLIO COMPARATIVE EXPERIMENTAL BENCHMARK")
    print("=" * 90)
    print(f"{'Portfolio':<28} {'Strategy Type':<30} {'Return':>10} {'Volatility':>12} {'Sharpe':>8}")
    print("-" * 90)
    for c in comp:
        print(f"{c['name']:<28} {c['type']:<30} {c['return_pct']:>+9.2f}% {c['volatility_pct']:>11.1f}% {c['sharpe_ratio']:>8.2f}")
    print("-" * 90 + "\n")


def report_monthly_command(period_str: str = "2026-08"):
    policy = InvestmentPolicy()
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No snapshots available.")
        return

    latest = snapshots[-1]
    portfolio = PortfolioEngine(policy, initial_cash=latest.cash)
    universe_stocks = _get_universe_stocks()
    for tx in store.get_all_transactions():
        stk = next((s for s in universe_stocks if s.symbol == tx.symbol), None)
        if stk:
            portfolio.execute_transaction(tx, stk)

    prices = store.get_latest_prices()
    portfolio.mark_to_market(prices, {s.symbol: s for s in universe_stocks})
    balance_sheet = portfolio.get_balance_sheet(latest.trade_date)
    income_stmt = portfolio.get_income_statement(period_str, latest.trade_date, store.get_all_transactions())

    report_dict = MonthlyReporter.generate_monthly_report(
        period_str=period_str,
        as_of_date=latest.trade_date,
        start_nav=10.0,
        end_nav=latest.nav_per_share,
        balance_sheet=balance_sheet,
        income_stmt=income_stmt,
        transactions=store.get_all_transactions(),
        decisions=store.get_recent_decisions(100),
        compliance_score=latest.compliance_score_pct,
        nepse_return_pct=1.45,
        management_outlook="Operating with disciplined cash buffers and targeting undervalued essential infrastructure.",
    )

    base_dir = Path(__file__).resolve().parent.parent
    report_file = base_dir / "website" / "data" / "reports" / f"{period_str}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)

    print(f"[OK] Monthly CEO report for {period_str} generated and archived in {report_file}!")


def main():
    parser = argparse.ArgumentParser(description="Alpha Nepal Capital CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run-daily
    run_daily_parser = subparsers.add_parser("run-daily", help="Run full daily simulation cycle")
    run_daily_parser.add_argument("--date", type=str, default=None, help="Trade date (YYYY-MM-DD)")
    run_daily_parser.add_argument("--no-live", action="store_true", help="Bypass live API requests")

    # status
    subparsers.add_parser("status", help="View company overview and holdings")

    # balance-sheet
    subparsers.add_parser("balance-sheet", help="Print company balance sheet")

    # compliance
    subparsers.add_parser("compliance", help="View strategy compliance checklist")

    # decisions
    subparsers.add_parser("decisions", help="View recent AI decisions and memos")

    # benchmark
    subparsers.add_parser("benchmark", help="Compare performance against 4 benchmarks")

    # report-monthly
    monthly_parser = subparsers.add_parser("report-monthly", help="Generate monthly CEO report")
    monthly_parser.add_argument("--period", type=str, default="2026-08", help="Month in YYYY-MM")

    args = parser.parse_args()

    if args.command == "run-daily":
        run_daily_command(trade_date=args.date, use_live=not args.no_live)
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
