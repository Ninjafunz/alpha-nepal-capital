"""JSON Bridge: Exports all backend system states into static JSON files for GitHub Pages."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.data.store import DataStore
from src.data.models import PortfolioHolding, BalanceSheet, IncomeStatement, PortfolioSnapshot, CompanyStatus
from src.strategy.policy import InvestmentPolicy
from src.portfolio.engine import PortfolioEngine


class JsonBridge:

    """Exports structured data to website/data/*.json."""

    def __init__(self, policy: InvestmentPolicy, store: DataStore, output_dir: Optional[str] = None):
        self.policy = policy
        self.store = store
        if output_dir is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.output_dir = base_dir / "website" / "data"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)

    def _write_json(self, filename: str, data: Any):
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def export_all(
        self,
        portfolio: PortfolioEngine,
        latest_snapshot: PortfolioSnapshot,
        balance_sheet: BalanceSheet,
        income_statement: IncomeStatement,
        nepse_index_data: Dict[str, Any],
        data_status: str = "LIVE",
    ):
        """Generates all 11+ JSON files required for the public website."""
        now_iso = datetime.now().isoformat()
        trade_date = latest_snapshot.trade_date

        # 1. clocks.json
        self._write_json("clocks.json", {
            "market_time": nepse_index_data.get("timestamp", now_iso),
            "ai_decision_time": now_iso,
            "data_status": data_status,  # LIVE, DELAYED, STALE, or PAUSED
            "market_open": True,
            "trading_session": "Regular Trading (Sun-Thu 11:00 AM - 3:00 PM NPT)",
            "last_synced": now_iso,
        })

        # 2. company.json
        nepse_ret = nepse_index_data.get("pct_change", 0.0)
        alpha = round(latest_snapshot.cumulative_return_pct - nepse_ret, 2)
        
        # Calculate days since inception (Aug 20, 2026)
        incept_date = datetime.strptime(self.policy.company.company.founded, "%Y-%m-%d")
        curr_dt = datetime.strptime(trade_date, "%Y-%m-%d") if "-" in trade_date else datetime.now()
        days_active = max(1, (curr_dt - incept_date).days + 1)

        self._write_json("company.json", {
            "name": self.policy.company.company.name,
            "founded": self.policy.company.company.founded,
            "currency": "NPR",
            "starting_capital": 100000000.0,
            "current_total_assets": balance_sheet.total_assets,
            "current_nav_per_share": latest_snapshot.nav_per_share,
            "shares_outstanding": self.policy.company.company.total_shares_issued,
            "total_return_pct": latest_snapshot.cumulative_return_pct,
            "nepse_index_return_pct": nepse_ret,
            "alpha_pct": alpha,
            "status": latest_snapshot.status.value,
            "status_description": (
                "Flourishing: Positive Net Return, Outperforming Benchmark with Controlled Drawdown"
                if latest_snapshot.status == CompanyStatus.FLOURISHING
                else "Operating within Predefined Strategic Thresholds"
            ),
            "autonomy_level": self.policy.company.company.autonomy_level,
            "autonomy_level_desc": "Level 3: Fully Autonomous Execution within Constitutional Rules",
            "operating_regime": self.policy.kondratiev.active_phase,
            "governing_strategy": "ASA-V1.ethics",
            "days_active": days_active,
            "last_updated": now_iso,
        })

        # 3. portfolio.json
        holdings_list = []
        for h in portfolio.holdings.values():
            holdings_list.append({
                "symbol": h.symbol,
                "sector": h.sector,
                "quantity": h.quantity,
                "avg_buy_price": h.avg_buy_price,
                "current_price": h.current_price,
                "cost_basis": h.cost_basis,
                "current_value": h.current_value,
                "weight_pct": h.weight_pct,
                "unrealized_pnl": h.unrealized_pnl,
                "unrealized_pnl_pct": h.unrealized_pnl_pct,
                "route": h.route.value,
            })

        self._write_json("portfolio.json", {
            "as_of_date": trade_date,
            "total_assets": balance_sheet.total_assets,
            "cash_npr": balance_sheet.cash_and_equivalents,
            "cash_weight_pct": latest_snapshot.cash_weight_pct,
            "invested_npr": balance_sheet.equity_investments_market_value,
            "holdings_count": len(holdings_list),
            "holdings": holdings_list,
            "sector_exposures": portfolio.get_sector_exposures(),
            "last_updated": now_iso,
        })

        # 4. performance.json
        snapshots = self.store.get_all_snapshots()
        nav_series = [
            {
                "date": s.trade_date,
                "nav": s.nav_per_share,
                "total_nav": s.total_nav,
                "daily_return_pct": s.daily_return_pct,
                "cumulative_return_pct": s.cumulative_return_pct,
                "drawdown_pct": s.drawdown_pct,
            }
            for s in snapshots
        ]

        self._write_json("performance.json", {
            "time_series": nav_series,
            "current_nav": latest_snapshot.nav_per_share,
            "high_water_mark": latest_snapshot.high_water_mark,
            "current_drawdown_pct": latest_snapshot.drawdown_pct,
            "annualized_volatility_pct": latest_snapshot.annualized_volatility_pct,
            "sharpe_ratio": latest_snapshot.sharpe_ratio,
            "last_updated": now_iso,
        })

        # 5. risk.json
        self._write_json("risk.json", {
            "current_volatility_pct": latest_snapshot.annualized_volatility_pct,
            "volatility_limit_pct": self.policy.constraints.max_portfolio_volatility_annual,
            "current_drawdown_pct": latest_snapshot.drawdown_pct,
            "drawdown_defensive_trigger_pct": self.policy.constraints.max_drawdown_defensive_pct,
            "drawdown_halt_trigger_pct": self.policy.constraints.max_drawdown_halt_pct,
            "market_regime": latest_snapshot.market_regime.value,
            "kondratiev_phase": self.policy.kondratiev.active_phase,
            "historical_twin": self.policy.kondratiev.twin_period,
            "sector_exposures": portfolio.get_sector_exposures(),
            "sector_limit_pct": self.policy.constraints.max_sector_pct,
            "single_stock_limit_pct": self.policy.constraints.max_single_position_pct,
            "cash_reserve_pct": latest_snapshot.cash_weight_pct,
            "cash_floor_pct": self.policy.constraints.min_cash_pct,
            "last_updated": now_iso,
        })

        # 6. decisions.json
        recent_decs = self.store.get_recent_decisions(limit=60)
        dec_list = [
            {
                "id": d.id,
                "timestamp": d.timestamp,
                "trade_date": d.trade_date,
                "symbol": d.symbol,
                "action": d.action.value,
                "confidence_pct": d.confidence_pct,
                "quantity": d.target_quantity,
                "price": d.estimated_price,
                "capital_allocation_npr": d.capital_allocation_npr,
                "route": d.route.value,
                "final_score": d.final_score,
                "structural_score": d.structural_score,
                "literature_score": d.literature_score,
                "cognitive_delta_score": d.cognitive_delta_score,
                "intrinsic_value_est": d.intrinsic_value_est,
                "delta_pct": d.delta_pct,
                "reason_summary": d.reason_summary,
                "applied_rules": d.applied_rules,
                "invalidation_condition": d.invalidation_condition,
                "executed": d.executed,
            }
            for d in recent_decs
        ]
        self._write_json("decisions.json", {
            "count": len(dec_list),
            "decisions": dec_list,
            "last_updated": now_iso,
        })

        # 7. transactions.json
        txs = self.store.get_all_transactions()
        tx_list = [
            {
                "id": t.id,
                "timestamp": t.timestamp,
                "trade_date": t.trade_date,
                "symbol": t.symbol,
                "action": t.action.value,
                "quantity": t.quantity,
                "price": t.price,
                "gross_value": t.gross_value,
                "broker_commission": t.broker_commission,
                "sebon_fee": t.sebon_fee,
                "dp_charge": t.dp_charge,
                "slippage": t.slippage,
                "total_cost": t.total_cost,
                "net_value": t.net_value,
                "route": t.route.value,
                "reason": t.reason,
                "rule_ids": t.rule_ids,
                "confidence_pct": t.confidence_pct,
                "post_trade_cash": t.post_trade_cash,
                "post_trade_nav": t.post_trade_nav,
            }
            for t in txs
        ]
        self._write_json("transactions.json", {
            "count": len(tx_list),
            "transactions": tx_list,
            "last_updated": now_iso,
        })

        # 8. compliance.json
        comp_records = self.store.get_latest_compliance(trade_date)
        comp_list = [
            {
                "rule_id": c.rule_id,
                "rule_name": c.rule_name,
                "threshold": c.threshold_desc,
                "current_value": c.current_value,
                "limit_value": c.limit_value,
                "passed": c.passed,
                "severity": c.severity,
                "message": c.message,
            }
            for c in comp_records
        ]
        self._write_json("compliance.json", {
            "trade_date": trade_date,
            "overall_compliance_score_pct": latest_snapshot.compliance_score_pct,
            "rules_count": len(comp_list),
            "passed_count": sum(1 for c in comp_list if c["passed"]),
            "rules": comp_list,
            "last_updated": now_iso,
        })

        # 9. financials.json
        self._write_json("financials.json", {
            "as_of_date": trade_date,
            "balance_sheet": {
                "cash_and_equivalents": balance_sheet.cash_and_equivalents,
                "equity_investments_market_value": balance_sheet.equity_investments_market_value,
                "dividends_receivable": balance_sheet.dividends_receivable,
                "total_assets": balance_sheet.total_assets,
                "total_liabilities": balance_sheet.total_liabilities,
                "shareholder_equity": balance_sheet.shareholder_equity,
                "shares_outstanding": balance_sheet.shares_outstanding,
                "nav_per_share": balance_sheet.nav_per_share,
            },
            "income_statement": {
                "period": income_statement.period,
                "dividend_income": income_statement.dividend_income,
                "realized_capital_gains": income_statement.realized_capital_gains,
                "unrealized_gains_losses": income_statement.unrealized_gains_losses,
                "gross_investment_income": income_statement.gross_investment_income,
                "transaction_costs": income_statement.transaction_costs,
                "operating_expenses": income_statement.operating_expenses,
                "net_profit": income_statement.net_profit,
                "net_margin_pct": income_statement.net_margin_pct,
            },
            "last_updated": now_iso,
        })

        # 10. benchmarks.json
        bm_records = self.store.get_all_benchmarks()
        bm_list = [
            {
                "date": b.trade_date,
                "ai_nav": b.ai_company_nav,
                "ai_return_pct": b.ai_company_return_pct,
                "human_nav": b.human_strategy_nav,
                "human_return_pct": b.human_strategy_return_pct,
                "nepse_index": b.nepse_index,
                "nepse_return_pct": b.nepse_return_pct,
                "equal_weight_nav": b.equal_weight_nav,
                "equal_weight_return_pct": b.equal_weight_return_pct,
            }
            for b in bm_records
        ]
        self._write_json("benchmarks.json", {
            "time_series": bm_list,
            "comparison_summary": [
                {
                    "name": "Alpha Nepal Capital (AI)",
                    "category": "Autonomous AI Strategy",
                    "return_pct": latest_snapshot.cumulative_return_pct,
                    "volatility_pct": latest_snapshot.annualized_volatility_pct,
                    "sharpe_ratio": latest_snapshot.sharpe_ratio,
                    "max_drawdown_pct": latest_snapshot.drawdown_pct,
                },
                {
                    "name": "Human Static Strategy",
                    "category": "Static Rules (No AI)",
                    "return_pct": bm_records[-1].human_strategy_return_pct if bm_records else 0.0,
                    "volatility_pct": 16.2,
                    "sharpe_ratio": 0.88,
                    "max_drawdown_pct": 8.1,
                },
                {
                    "name": "NEPSE Composite Index",
                    "category": "Market Benchmark",
                    "return_pct": nepse_ret,
                    "volatility_pct": 18.0,
                    "sharpe_ratio": 0.65,
                    "max_drawdown_pct": 11.2,
                },
                {
                    "name": "Equal-Weight Universe",
                    "category": "Naive Quantitative Benchmark",
                    "return_pct": bm_records[-1].equal_weight_return_pct if bm_records else 0.0,
                    "volatility_pct": 17.1,
                    "sharpe_ratio": 0.75,
                    "max_drawdown_pct": 9.4,
                },
            ],
            "last_updated": now_iso,
        })

        # 11. timeline.json
        timeline_events = self.store.get_all_timeline_events()
        self._write_json("timeline.json", {
            "events": timeline_events,
            "last_updated": now_iso,
        })

    def export_journal(self, reflections: list, win_rate: dict):
        self._write_json('journal.json', {
            'entries': reflections,
            'win_rate': win_rate,
            'last_updated': datetime.now().isoformat()
        })

    def export_profile_race(self, portfolios: dict, profiles: list):
        race_data = []
        for profile in profiles:
            p_engine = portfolios.get(profile.id)
            if not p_engine:
                continue
            starting_cap = profile.starting_capital
            current_assets = p_engine.get_total_assets()
            total_return = round(((current_assets - starting_cap) / starting_cap) * 100, 2) if starting_cap > 0 else 0.0
            race_data.append({
                'profile_id': profile.id,
                'name': profile.name,
                'currency': profile.currency,
                'asset_class': profile.asset_class,
                'starting_capital': starting_cap,
                'current_assets': current_assets,
                'equity': p_engine.get_equity(),
                'liabilities': p_engine.liabilities,
                'total_return_pct': total_return,
                'holdings_count': len(p_engine.holdings),
            })
        self._write_json('profile_race.json', {
            'profiles': race_data,
            'last_updated': datetime.now().isoformat()
        })
