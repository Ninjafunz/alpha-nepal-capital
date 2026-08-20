"""CLI Application for Alpha Nepal Capital (Pure NEPSE Domestic Edition)."""
import argparse
import sys
import yaml
import json
import time
from pathlib import Path
from datetime import datetime, date
from typing import Optional, List, Dict, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.strategy.policy import InvestmentPolicy
from src.data.store import DataStore
from src.data.models import Stock, PriceBar, Fundamental, PortfolioSnapshot, CompanyStatus, MarketRegime
from src.data.nepse_client import NepseClient
from src.data.sharesansar import ShareSansarScraper
from src.portfolio.engine import PortfolioEngine
from src.governance.reflection import ReflectionEngine
from src.decision.pipeline import DecisionPipeline
from src.governance.compliance import ComplianceMonitor
from src.strategy.risk import RiskManager
from src.reporting.executive_memo import GlobalExecutiveMemo
from src.reporting.daily import DailyReporter
from src.reporting.monthly import MonthlyReporter
from src.benchmarks.tracker import BenchmarkTracker
from src.reporting.timeline import TimelineManager
from src.export.json_bridge import JsonBridge


BASE_DIR = Path(__file__).resolve().parent.parent
PROFILE_ID = "P1_DOMESTIC_EQUITY"


def _load_universe_metadata() -> dict:
    universe_path = BASE_DIR / "config" / "universe.yaml"
    with open(universe_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {s["symbol"]: s for s in data.get("securities", [])}


def _get_universe_stocks() -> List[Stock]:
    meta = _load_universe_metadata()
    stocks = []
    for s in meta.values():
        stk = Stock(
            symbol=s["symbol"],
            name=s["name"],
            sector=s["sector"],
            category=s.get("category", "A"),
            paid_up_capital_cr=s.get("paid_up_capital_cr", 0.0),
            asset_class=s.get("asset_class", "EQUITY_DOMESTIC"),
            avg_daily_volume_usd=s.get("avg_daily_volume_usd", 500000.0)
        )
        # Attach metadata as attributes for scorer
        stk.bottleneck_score = s.get("bottleneck_score", 85.0)
        stk.elite_alignment = s.get("elite_alignment", 80.0)
        stk.governance_score = s.get("governance_score", 85.0)
        stk.route_eligibility = s.get("route_eligibility", ["Route Alpha"])
        stocks.append(stk)
    return stocks


def run_daily_command(trade_date: Optional[str] = None, use_live: bool = True, silent: bool = False):
    """Run full daily autonomous investment cycle for NEPSE."""
    if trade_date is None:
        trade_date = date.today().isoformat()

    if not silent:
        print("=" * 80)
        print(f"ALPHA NEPAL CAPITAL — Autonomous Daily Investment Cycle")
        print(f"Trade Date: {trade_date} | Mode: {'LIVE' if use_live else 'SIMULATION'}")
        print("=" * 80)

    policy = InvestmentPolicy()
    store = DataStore()
    timeline = TimelineManager(store)
    timeline.ensure_genesis_event()

    # 1. Load Universe (domestic NEPSE only)
    universe_stocks = _get_universe_stocks()
    store.save_stocks(universe_stocks)

    # 2. Ingest NEPSE Market Prices
    if not silent:
        print("\n[1/8] Fetching NEPSE market prices...")
    client = NepseClient(use_live=use_live)
    bars = client.fetch_today_prices(universe_stocks, trade_date)
    store.save_price_bars(bars)
    price_dict = {b.symbol: b for b in bars}

    # 3. Fetch Fundamentals
    if not silent:
        print("[2/8] Ingesting company fundamentals from ShareSansar...")
    scraper = ShareSansarScraper()
    funds = scraper.fetch_fundamentals(universe_stocks, trade_date)
    store.save_fundamentals(funds)
    fund_dict = {f.symbol: f for f in funds}

    # 4. Load portfolio state from ledger
    if not silent:
        print("[3/8] Loading portfolio state from immutable ledger...")
    portfolio = PortfolioEngine(policy, profile_id=PROFILE_ID)
    for tx in store.get_all_transactions():
        stk = next((s for s in universe_stocks if s.symbol == tx.symbol), None)
        portfolio.execute_transaction(tx, stk)
    portfolio.mark_to_market(price_dict, {s.symbol: s for s in universe_stocks})

    # 5. Run AI Decision Pipeline
    if not silent:
        print("[4/8] Running AI 3-Layer Scorer & Decision Pipeline...")
    pipeline = DecisionPipeline(policy, store)
    decisions, cycle_metadata = pipeline.run_cycle(
        trade_date, universe_stocks, price_dict, fund_dict,
        {PROFILE_ID: portfolio}
    )
    for d in decisions:
        store.record_decision(d)

    # 6. Financial Accounting
    if not silent:
        print("[5/8] Computing balance sheet and income statement...")
    balance_sheet = portfolio.get_balance_sheet(trade_date)
    all_txs = store.get_all_transactions()
    income_stmt = portfolio.get_income_statement("Daily", trade_date, all_txs)

    # 7. Reflection & Post-Mortems
    if not silent:
        print("[6/8] Generating self-reflection and post-mortem journal...")
    reflection_engine = ReflectionEngine(policy)
    reflections = reflection_engine.evaluate_holdings(portfolio.holdings)
    win_rate = reflection_engine.calculate_win_rate(all_txs)

    # 8. Compliance & Risk
    if not silent:
        print("[7/8] Running constitutional compliance audit...")
    compliance_mon = ComplianceMonitor(policy)
    checks, compliance_score = compliance_mon.check_compliance(trade_date, portfolio)
    store.record_compliance_checks(checks)

    index_data = client.fetch_nepse_index(trade_date)
    bm_tracker = BenchmarkTracker(store, 100000000.0)
    bm_tracker.update_daily_benchmarks(
        trade_date=trade_date,
        ai_current_nav=balance_sheet.nav_per_share,
        price_dict=price_dict,
        nepse_index_val=index_data["current_value"],
    )

    # NAV / Risk calculations
    snapshots = store.get_all_snapshots()
    nav_history = [s.total_nav for s in snapshots] + [balance_sheet.total_assets]
    risk_mgr = RiskManager(policy)
    dd_info = risk_mgr.calculate_drawdown(nav_history)
    vol_pct = risk_mgr.calculate_volatility([b.pct_change / 100.0 for b in bars])
    regime = risk_mgr.determine_regime([b.pct_change / 100.0 for b in bars])
    cum_ret = round(((balance_sheet.total_assets - 100000000.0) / 100000000.0) * 100.0, 2)
    alpha_vs_nepse = round(cum_ret - index_data.get("pct_change", 0.0), 2)
    status = risk_mgr.evaluate_company_status(cum_ret, alpha_vs_nepse, dd_info["drawdown_pct"])

    daily_ret = 0.0
    if snapshots:
        prev_nav = snapshots[-1].nav_per_share
        daily_ret = round(((balance_sheet.nav_per_share - prev_nav) / prev_nav) * 100.0, 2) if prev_nav else 0.0

    # Save snapshot
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
        cumulative_return_pct=cum_ret,
        high_water_mark=dd_info["high_water_mark"],
        drawdown_pct=dd_info["drawdown_pct"],
        annualized_volatility_pct=vol_pct,
        sharpe_ratio=round((cum_ret - 6.0) / max(1.0, vol_pct), 2),
        compliance_score_pct=compliance_score,
        status=status,
        market_regime=regime,
        holdings_count=len(portfolio.holdings),
    )
    store.save_snapshot(snapshot)

    # 9. Export JSON + Daily Report
    if not silent:
        print("[8/8] Exporting JSON data for GitHub Pages investor portal...")
    bridge = JsonBridge(policy, store)
    bridge.export_all(
        portfolio=portfolio,
        latest_snapshot=snapshot,
        balance_sheet=balance_sheet,
        income_statement=income_stmt,
        nepse_index_data=index_data,
        all_portfolios={PROFILE_ID: portfolio}
    )
    bridge.export_journal(reflections, win_rate)

    # Generate & save daily report
    _generate_and_save_daily_report(trade_date, snapshot, balance_sheet, decisions, all_txs, index_data)

    if not silent:
        _print_daily_summary(snapshot, balance_sheet, decisions, all_txs, index_data)


def _generate_and_save_daily_report(
    trade_date: str,
    snapshot: PortfolioSnapshot,
    balance_sheet,
    decisions: list,
    transactions: list,
    index_data: dict,
):
    """Generate the daily executive report and save to website/data/reports/."""
    buys = [d for d in decisions if d.action.value == "BUY" and d.executed]
    holds = [d for d in decisions if d.action.value == "HOLD"]

    lines = []
    lines.append("=" * 80)
    lines.append(f"ALPHA NEPAL CAPITAL — DAILY EXECUTIVE REPORT")
    lines.append(f"Trade Date: {trade_date} | Status: {snapshot.status.value} | Regime: {snapshot.market_regime.value}")
    lines.append("=" * 80)
    lines.append(f"\n1. FINANCIAL POSITION")
    lines.append(f"   Total Assets:         NPR {snapshot.total_assets:>15,.2f}")
    lines.append(f"   Cash Reserve:         NPR {snapshot.cash:>15,.2f}  ({snapshot.cash_weight_pct:.1f}%)")
    lines.append(f"   Invested Portfolio:   NPR {snapshot.invested_value:>15,.2f}")
    lines.append(f"   NAV / Share:          NPR {snapshot.nav_per_share:>15.4f}")
    lines.append(f"   Daily Return:         {snapshot.daily_return_pct:>+.2f}%")
    lines.append(f"   Cumulative Return:    {snapshot.cumulative_return_pct:>+.2f}%")
    lines.append(f"   NEPSE Index Change:   {index_data.get('pct_change', 0.0):>+.2f}%")
    lines.append(f"   Alpha Generated:      {snapshot.cumulative_return_pct - index_data.get('pct_change', 0.0):>+.2f}%")
    lines.append(f"   Drawdown from Peak:   {snapshot.drawdown_pct:.2f}%")
    lines.append(f"   Compliance Score:     {snapshot.compliance_score_pct:.1f}%")

    lines.append(f"\n2. WHY THE AI DID WHAT IT DID TODAY")
    lines.append(f"   Total Decisions Evaluated: {len(decisions)}")
    lines.append(f"   BUY Orders Executed:       {len(buys)}")
    lines.append(f"   HOLD Decisions:            {len(holds)}")

    if buys:
        lines.append(f"\n   EXECUTED BUY ORDERS:")
        for d in buys:
            lines.append(f"   ▶ BUY {d.symbol} @ NPR {d.estimated_price:,.2f}")
            lines.append(f"     Route:         {d.route.value}")
            lines.append(f"     Cognitive Delta: {d.delta_pct:.1f}%  |  Intrinsic Value Est: NPR {d.intrinsic_value_est:,.2f}")
            lines.append(f"     Structural Score: {d.structural_score:.1f}  |  Literature Score: {d.literature_score:.1f}")
            lines.append(f"     Reason: {d.reason_summary}")
            lines.append(f"     Invalidation: {d.invalidation_condition}")

    if holds:
        lines.append(f"\n   HOLD DECISIONS (Delta below 20% threshold or sizing constraint):")
        for d in holds[:5]:
            lines.append(f"   ○ HOLD {d.symbol} — Delta: {d.delta_pct:.1f}% — {d.reason_summary}")

    lines.append(f"\n3. AI INVESTMENT PHILOSOPHY APPLIED TODAY")
    lines.append(f"   - Layer 1 (Structural): Screened for capital velocity, PPA coverage, bottleneck asymmetry")
    lines.append(f"   - Layer 2 (Literature): Checked elite alignment, prospect theory 'mispriced middle'")
    lines.append(f"   - Layer 3 (Cognitive Delta): Only bought where intrinsic value gap >= 20%")
    lines.append(f"   - Constitutional Guardrails: Max 10% single stock, 40% sector, 5% min cash enforced")
    lines.append("=" * 80)

    report_text = "\n".join(lines)

    # Save as .txt and .json
    reports_dir = BASE_DIR / "website" / "data" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    txt_path = reports_dir / f"{trade_date}-daily.txt"
    txt_path.write_text(report_text, encoding="utf-8")

    json_path = reports_dir / f"{trade_date}-daily.json"
    json_path.write_text(json.dumps({
        "trade_date": trade_date,
        "status": snapshot.status.value,
        "regime": snapshot.market_regime.value,
        "nav_per_share": snapshot.nav_per_share,
        "daily_return_pct": snapshot.daily_return_pct,
        "cumulative_return_pct": snapshot.cumulative_return_pct,
        "nepse_pct_change": index_data.get("pct_change", 0.0),
        "alpha_pct": round(snapshot.cumulative_return_pct - index_data.get("pct_change", 0.0), 2),
        "compliance_score_pct": snapshot.compliance_score_pct,
        "decisions": [
            {
                "symbol": d.symbol,
                "action": d.action.value,
                "route": d.route.value,
                "delta_pct": d.delta_pct,
                "structural_score": d.structural_score,
                "literature_score": d.literature_score,
                "intrinsic_value_est": d.intrinsic_value_est,
                "reason": d.reason_summary,
                "executed": d.executed,
            }
            for d in decisions
        ]
    }, indent=2), encoding="utf-8")

    # Always write latest-daily.json for website to pick up
    latest_path = BASE_DIR / "website" / "data" / "daily_report.json"
    import shutil
    shutil.copy(json_path, latest_path)


def _print_daily_summary(snapshot, balance_sheet, decisions, transactions, index_data):
    """Print brief daily summary to terminal."""
    print("\n" + "=" * 80)
    print(f"ALPHA NEPAL CAPITAL — {snapshot.status.value}")
    print(f"NAV: NPR {snapshot.nav_per_share:.4f} | Daily: {snapshot.daily_return_pct:+.2f}% | Cumulative: {snapshot.cumulative_return_pct:+.2f}%")
    print(f"NEPSE Index: {index_data.get('pct_change', 0.0):+.2f}% | Alpha: {snapshot.cumulative_return_pct - index_data.get('pct_change', 0.0):+.2f}%")
    print(f"Compliance: {snapshot.compliance_score_pct:.1f}% | Holdings: {snapshot.holdings_count}")
    executed = [d for d in decisions if d.executed]
    print(f"Decisions: {len(decisions)} evaluated, {len(executed)} executed today.")
    print("=" * 80)
    print(f"[OK] Daily report saved to website/data/reports/{snapshot.trade_date}-daily.json")


def backfill_week_command():
    """Simulate the full 7-day autonomous history starting from one week ago."""
    from datetime import date, timedelta
    today = date.today()
    # Generate last 7 calendar days, skip weekends (Sat=5, Sun=6 in Western — NEPSE trades Sun-Thu)
    # NEPSE trading days: Sunday=6, Monday=0, Tuesday=1, Wednesday=2, Thursday=3
    trading_days = []
    d = today - timedelta(days=7)
    while d <= today:
        if d.weekday() in (0, 1, 2, 3, 6):  # Mon-Thu + Sun = NEPSE trading days
            trading_days.append(d.isoformat())
        d += timedelta(days=1)

    print("=" * 80)
    print(f"ALPHA NEPAL CAPITAL — 7-Day Autonomous Backfill Simulation")
    print(f"Simulating {len(trading_days)} NEPSE trading days: {trading_days[0]} → {trading_days[-1]}")
    print("=" * 80)

    for td in trading_days:
        print(f"\n[*] Running autonomous cycle for {td}...")
        run_daily_command(trade_date=td, use_live=False, silent=True)
        print(f"    ✓ {td} complete.")

    print("\n" + "=" * 80)
    print("[OK] 7-day backfill complete! Run `python -m src.cli status` to view portfolio.")
    print("=" * 80)


def status_command():
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No snapshots yet. Run `python -m src.cli run-daily` first.")
        return

    latest = snapshots[-1]
    policy = InvestmentPolicy()
    universe_stocks = _get_universe_stocks()
    prices = store.get_latest_prices()

    portfolio = PortfolioEngine(policy, profile_id=PROFILE_ID)
    for tx in store.get_all_transactions():
        stk = next((s for s in universe_stocks if s.symbol == tx.symbol), None)
        portfolio.execute_transaction(tx, stk)
    portfolio.mark_to_market(prices, {s.symbol: s for s in universe_stocks})

    print("\n" + "=" * 80)
    print(f"ALPHA NEPAL CAPITAL — {latest.status.value}")
    print(f"Total Assets: NPR {latest.total_assets:,.2f} | NAV/Share: NPR {latest.nav_per_share:.4f}")
    print(f"Cumulative Return: {latest.cumulative_return_pct:+.2f}% | Compliance: {latest.compliance_score_pct:.1f}%")
    print("=" * 80)
    print(f"\n--- {PROFILE_ID} Holdings (Total: NPR {portfolio.get_total_assets():,.2f}) ---")
    print(f"{'Symbol':<10} {'Sector':<24} {'Qty':>8} {'Price':>10} {'Market Val (NPR)':>18} {'Unreal. P&L':>14} {'Route':<25}")
    print("-" * 108)
    for h in portfolio.holdings.values():
        pnl_str = f"NPR {h.unrealized_pnl:+,.0f} ({h.unrealized_pnl_pct:+.1f}%)"
        route_str = h.route.value if hasattr(h.route, "value") else str(h.route)
        print(f"{h.symbol:<10} {h.sector[:23]:<24} {h.quantity:>8,d} {h.current_price:>10,.2f} {h.current_value:>18,.2f} {pnl_str:>14} {route_str:<25}")
    print(f"\nCash: NPR {portfolio.cash:,.2f} ({latest.cash_weight_pct:.1f}% of assets)")


def balance_sheet_command():
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No snapshots available. Run `python -m src.cli run-daily` first.")
        return
    latest = snapshots[-1]
    policy = InvestmentPolicy()
    portfolio = PortfolioEngine(policy, profile_id=PROFILE_ID)
    for tx in store.get_all_transactions():
        portfolio.execute_transaction(tx, None)
    portfolio.cash = latest.cash
    bs = portfolio.get_balance_sheet(latest.trade_date)
    bs.total_assets = latest.total_assets
    bs.equity_investments_market_value = latest.invested_value
    bs.nav_per_share = latest.nav_per_share

    print("\n" + "=" * 60)
    print(f"AUDITED BALANCE SHEET — {latest.trade_date}")
    print("=" * 60)
    print(f"  Cash & Equivalents:         NPR {latest.cash:>15,.2f}")
    print(f"  Equity Investments (MTM):   NPR {latest.invested_value:>15,.2f}")
    print(f"  Total Assets:               NPR {latest.total_assets:>15,.2f}")
    print(f"  Total Liabilities:          NPR {'0.00':>15}")
    print(f"  Shareholder Equity:         NPR {latest.total_assets:>15,.2f}")
    print(f"  Shares Outstanding:                {'10,000,000':>15}")
    print(f"  Net Asset Value (NAV)/Share: NPR {latest.nav_per_share:>14.4f}")
    print("=" * 60)


def compliance_command():
    store = DataStore()
    checks = store.get_latest_compliance()
    if not checks:
        print("No compliance data yet. Run `python -m src.cli run-daily` first.")
        return
    passed = sum(1 for c in checks if c.passed)
    print("\n" + "=" * 80)
    print("CONSTITUTIONAL COMPLIANCE AUDIT")
    print("=" * 80)
    for c in checks:
        badge = "PASS" if c.passed else "BREACH"
        print(f"[{badge}] {c.rule_id} — {c.rule_name}: Actual={c.current_value:.1f} (Limit: {c.threshold_desc})")
    print(f"\nOverall Compliance Score: {passed}/{len(checks)} rules passed ({100.0*passed/len(checks):.1f}%)")
    print("=" * 80)


def decisions_command():
    store = DataStore()
    decs = store.get_recent_decisions(limit=15)
    if not decs:
        print("No decisions yet. Run `python -m src.cli run-daily` first.")
        return
    print("\n" + "=" * 80)
    print("RECENT AI DECISIONS — WHY THE AI DID WHAT IT DID")
    print("=" * 80)
    for d in decs:
        route_str = d.route.value if hasattr(d.route, "value") else str(d.route)
        print(f"[{d.trade_date}] {d.action.value} {d.symbol} | Route: {route_str} | Delta: {d.delta_pct:.1f}% | Executed: {d.executed}")
        print(f"  Reason: {d.reason_summary}")
    print("=" * 80)


def benchmark_command():
    store = DataStore()
    bms = store.get_all_benchmarks()
    if not bms:
        print("No benchmark data yet. Run `python -m src.cli run-daily` first.")
        return
    print("\n" + "=" * 80)
    print(f"{'Date':<12} {'AI Return':>12} {'NEPSE Index':>14} {'Alpha':>10}")
    print("-" * 80)
    for b in bms[-10:]:
        alpha = round(b.ai_company_return_pct - b.nepse_return_pct, 2)
        print(f"{b.trade_date:<12} {b.ai_company_return_pct:>+11.2f}% {b.nepse_return_pct:>+13.2f}% {alpha:>+9.2f}%")
    print("=" * 80)


def report_monthly_command(period_str: str = None):
    if period_str is None:
        period_str = date.today().strftime("%Y-%m")
    store = DataStore()
    snapshots = store.get_all_snapshots()
    if not snapshots:
        print("No data available. Run `python -m src.cli run-daily` first.")
        return
    latest = snapshots[-1]
    policy = InvestmentPolicy()
    portfolio = PortfolioEngine(policy, profile_id=PROFILE_ID)
    for tx in store.get_all_transactions():
        portfolio.execute_transaction(tx, None)
    portfolio.cash = latest.cash
    bs = portfolio.get_balance_sheet(latest.trade_date)
    bs.total_assets = latest.total_assets
    bs.equity_investments_market_value = latest.invested_value
    bs.nav_per_share = latest.nav_per_share

    all_txs = store.get_all_transactions()
    income_stmt = portfolio.get_income_statement(period_str, latest.trade_date, all_txs)

    bms = store.get_all_benchmarks()
    nepse_ret = bms[-1].nepse_return_pct if bms else 0.0

    report_dict = MonthlyReporter.generate_monthly_report(
        period_str=period_str,
        as_of_date=latest.trade_date,
        start_nav=10.0,
        end_nav=latest.nav_per_share,
        balance_sheet=bs,
        income_stmt=income_stmt,
        transactions=all_txs,
        decisions=store.get_recent_decisions(200),
        compliance_score=latest.compliance_score_pct,
        nepse_return_pct=nepse_ret,
        management_outlook="Operating with disciplined 3-Layer fundamental scoring and regime-adaptive tactical tilts across the NEPSE universe.",
    )

    report_file = BASE_DIR / "website" / "data" / "reports" / f"{period_str}.json"
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_dict, f, indent=2)
    print(f"[OK] Monthly CEO report for {period_str} generated → {report_file}")


def poll_nepse_command(interval: int = 10):
    """Start continuous live NEPSE data polling loop."""
    client = NepseClient(use_live=True)
    client.start_polling_loop(poll_interval=interval)


def main():
    parser = argparse.ArgumentParser(
        description="Alpha Nepal Capital CLI — Pure NEPSE Autonomous Investment System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run-daily
    run_p = subparsers.add_parser("run-daily", help="Run full autonomous daily cycle")
    run_p.add_argument("--date", type=str, default=None, help="Trade date (YYYY-MM-DD)")
    run_p.add_argument("--no-live", action="store_true", help="Use simulation (no live API calls)")

    # backfill-week
    subparsers.add_parser("backfill-week", help="Run 7-day autonomous simulation warm-up from one week ago")

    # poll-nepse
    poll_p = subparsers.add_parser("poll-nepse", help="Start continuous live NEPSE price feed polling")
    poll_p.add_argument("--interval", type=int, default=10, help="Polling interval in seconds (min: 3s)")

    # status
    subparsers.add_parser("status", help="View current portfolio holdings and NAV")

    # balance-sheet
    subparsers.add_parser("balance-sheet", help="Print audited balance sheet")

    # compliance
    subparsers.add_parser("compliance", help="View constitutional strategy compliance audit")

    # decisions
    subparsers.add_parser("decisions", help="View recent AI decisions and reasoning")

    # benchmark
    subparsers.add_parser("benchmark", help="Compare performance vs NEPSE index")

    # report-monthly
    monthly_p = subparsers.add_parser("report-monthly", help="Generate monthly CEO report")
    monthly_p.add_argument("--period", type=str, default=None, help="Month in YYYY-MM format")

    args = parser.parse_args()

    if args.command == "run-daily":
        run_daily_command(trade_date=args.date, use_live=not args.no_live)
    elif args.command == "backfill-week":
        backfill_week_command()
    elif args.command == "poll-nepse":
        poll_nepse_command(interval=args.interval)
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
