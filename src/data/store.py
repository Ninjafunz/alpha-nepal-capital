"""SQLite Data Access Layer with Immutable Ledger enforcement for Alpha Nepal Capital."""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from src.data.models import (
    Stock,
    PriceBar,
    Fundamental,
    Transaction,
    Decision,
    PortfolioSnapshot,
    ComplianceRecord,
    BenchmarkRecord,
    ActionType,
    StrategicRoute,
    CompanyStatus,
    MarketRegime,
)


class DataStore:
    """Manages SQLite database with strictly immutable transaction & decision ledgers."""

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            self.db_path = str(base_dir / "data" / "alpha_nepal_capital.db")
        else:
            self.db_path = db_path

        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Stocks master
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS stocks (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                sector TEXT NOT NULL,
                category TEXT DEFAULT 'A',
                paid_up_capital_cr REAL DEFAULT 0.0,
                listed_shares INTEGER DEFAULT 0,
                security_id INTEGER,
                is_active INTEGER DEFAULT 1
            );
            """)

            # Price History (EOD OHLCV)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS price_history (
                symbol TEXT,
                trade_date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume INTEGER,
                turnover REAL,
                prev_close REAL,
                point_change REAL,
                pct_change REAL,
                timestamp TEXT,
                PRIMARY KEY (symbol, trade_date)
            );
            """)

            # Fundamentals
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS fundamentals (
                symbol TEXT,
                as_of_date TEXT,
                pe_ratio REAL,
                pb_ratio REAL,
                eps REAL,
                book_value REAL,
                roe REAL,
                dividend_yield_pct REAL DEFAULT 0.0,
                debt_to_equity REAL DEFAULT 0.0,
                promoter_holding_pct REAL DEFAULT 0.0,
                public_holding_pct REAL DEFAULT 0.0,
                PRIMARY KEY (symbol, as_of_date)
            );
            """)

            # IMMUTABLE Transactions Ledger
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                gross_value REAL NOT NULL,
                broker_commission REAL NOT NULL,
                sebon_fee REAL NOT NULL,
                dp_charge REAL NOT NULL,
                slippage REAL NOT NULL,
                total_cost REAL NOT NULL,
                net_value REAL NOT NULL,
                pre_trade_cash REAL NOT NULL,
                post_trade_cash REAL NOT NULL,
                pre_trade_nav REAL NOT NULL,
                post_trade_nav REAL NOT NULL,
                route TEXT NOT NULL,
                reason TEXT NOT NULL,
                rule_ids TEXT NOT NULL,
                confidence_pct REAL NOT NULL,
                decision_id TEXT NOT NULL
            );
            """)

            # IMMUTABLE Decisions Ledger
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence_pct REAL NOT NULL,
                target_quantity INTEGER NOT NULL,
                estimated_price REAL NOT NULL,
                capital_allocation_npr REAL NOT NULL,
                route TEXT NOT NULL,
                structural_score REAL,
                capital_velocity_score REAL,
                physical_risk_score REAL,
                regulatory_risk_score REAL,
                bottleneck_score REAL,
                literature_score REAL,
                elite_alignment_score REAL,
                sentiment_score REAL,
                optionality_score REAL,
                golden_zone_score REAL,
                cognitive_delta_score REAL,
                narrative_bias_score REAL,
                anchoring_bias_score REAL,
                recency_bias_score REAL,
                intrinsic_value_est REAL,
                delta_pct REAL,
                final_score REAL,
                reason_summary TEXT NOT NULL,
                applied_rules TEXT NOT NULL,
                invalidation_condition TEXT NOT NULL,
                executed INTEGER DEFAULT 0
            );
            """)

            # Daily Portfolio Snapshots
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                trade_date TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                total_assets REAL NOT NULL,
                cash REAL NOT NULL,
                invested_value REAL NOT NULL,
                cash_weight_pct REAL NOT NULL,
                shares_outstanding REAL NOT NULL,
                nav_per_share REAL NOT NULL,
                total_nav REAL NOT NULL,
                daily_return_pct REAL NOT NULL,
                cumulative_return_pct REAL NOT NULL,
                high_water_mark REAL NOT NULL,
                drawdown_pct REAL NOT NULL,
                annualized_volatility_pct REAL NOT NULL,
                sharpe_ratio REAL NOT NULL,
                compliance_score_pct REAL NOT NULL,
                status TEXT NOT NULL,
                market_regime TEXT NOT NULL,
                holdings_count INTEGER NOT NULL
            );
            """)

            # Compliance Records
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_checks (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                rule_id TEXT NOT NULL,
                rule_name TEXT NOT NULL,
                threshold_desc TEXT NOT NULL,
                current_value REAL NOT NULL,
                limit_value REAL NOT NULL,
                passed INTEGER NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL
            );
            """)

            # Benchmark Records
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmarks (
                trade_date TEXT PRIMARY KEY,
                ai_company_nav REAL NOT NULL,
                ai_company_return_pct REAL NOT NULL,
                human_strategy_nav REAL NOT NULL,
                human_strategy_return_pct REAL NOT NULL,
                nepse_index REAL NOT NULL,
                nepse_return_pct REAL NOT NULL,
                equal_weight_nav REAL NOT NULL,
                equal_weight_return_pct REAL NOT NULL
            );
            """)

            # Company Timeline Milestones
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_date TEXT NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                nav_at_event REAL,
                meta_json TEXT
            );
            """)

            conn.commit()

    # --- Stock Master Operations ---
    def save_stocks(self, stocks: List[Stock]):
        with self._get_connection() as conn:
            for s in stocks:
                conn.execute("""
                INSERT INTO stocks (symbol, name, sector, category, paid_up_capital_cr, listed_shares, security_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol) DO UPDATE SET
                    name=excluded.name,
                    sector=excluded.sector,
                    category=excluded.category,
                    paid_up_capital_cr=excluded.paid_up_capital_cr,
                    listed_shares=excluded.listed_shares,
                    security_id=excluded.security_id,
                    is_active=excluded.is_active;
                """, (s.symbol, s.name, s.sector, s.category, s.paid_up_capital_cr, s.listed_shares, s.security_id, int(s.is_active)))
            conn.commit()

    def get_all_stocks(self) -> List[Stock]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM stocks WHERE is_active=1;").fetchall()
            return [
                Stock(
                    symbol=r["symbol"],
                    name=r["name"],
                    sector=r["sector"],
                    category=r["category"],
                    paid_up_capital_cr=r["paid_up_capital_cr"],
                    listed_shares=r["listed_shares"],
                    security_id=r["security_id"],
                    is_active=bool(r["is_active"]),
                )
                for r in rows
            ]

    # --- Price History Operations ---
    def save_price_bars(self, bars: List[PriceBar]):
        with self._get_connection() as conn:
            for b in bars:
                conn.execute("""
                INSERT INTO price_history (symbol, trade_date, open, high, low, close, volume, turnover, prev_close, point_change, pct_change, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, trade_date) DO UPDATE SET
                    open=excluded.open,
                    high=excluded.high,
                    low=excluded.low,
                    close=excluded.close,
                    volume=excluded.volume,
                    turnover=excluded.turnover,
                    prev_close=excluded.prev_close,
                    point_change=excluded.point_change,
                    pct_change=excluded.pct_change,
                    timestamp=excluded.timestamp;
                """, (b.symbol, b.trade_date, b.open, b.high, b.low, b.close, b.volume, b.turnover, b.prev_close, b.point_change, b.pct_change, b.timestamp))
            conn.commit()

    def get_latest_prices(self, trade_date: Optional[str] = None) -> Dict[str, PriceBar]:
        with self._get_connection() as conn:
            if trade_date:
                query = "SELECT * FROM price_history WHERE trade_date = ?;"
                rows = conn.execute(query, (trade_date,)).fetchall()
            else:
                query = """
                SELECT p.* FROM price_history p
                INNER JOIN (
                    SELECT symbol, MAX(trade_date) as max_date
                    FROM price_history
                    GROUP BY symbol
                ) latest ON p.symbol = latest.symbol AND p.trade_date = latest.max_date;
                """
                rows = conn.execute(query).fetchall()

            res = {}
            for r in rows:
                res[r["symbol"]] = PriceBar(
                    symbol=r["symbol"],
                    trade_date=r["trade_date"],
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    volume=r["volume"],
                    turnover=r["turnover"],
                    prev_close=r["prev_close"],
                    point_change=r["point_change"],
                    pct_change=r["pct_change"],
                    timestamp=r["timestamp"],
                )
            return res

    def get_price_history_series(self, symbol: str, limit: int = 120) -> List[PriceBar]:
        with self._get_connection() as conn:
            rows = conn.execute("""
            SELECT * FROM price_history
            WHERE symbol = ?
            ORDER BY trade_date ASC;
            """, (symbol,)).fetchall()
            return [
                PriceBar(
                    symbol=r["symbol"],
                    trade_date=r["trade_date"],
                    open=r["open"],
                    high=r["high"],
                    low=r["low"],
                    close=r["close"],
                    volume=r["volume"],
                    turnover=r["turnover"],
                    prev_close=r["prev_close"],
                    point_change=r["point_change"],
                    pct_change=r["pct_change"],
                    timestamp=r["timestamp"],
                )
                for r in rows[-limit:]
            ]

    # --- Fundamentals Operations ---
    def save_fundamentals(self, funcs: List[Fundamental]):
        with self._get_connection() as conn:
            for f in funcs:
                conn.execute("""
                INSERT INTO fundamentals (symbol, as_of_date, pe_ratio, pb_ratio, eps, book_value, roe, dividend_yield_pct, debt_to_equity, promoter_holding_pct, public_holding_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(symbol, as_of_date) DO UPDATE SET
                    pe_ratio=excluded.pe_ratio,
                    pb_ratio=excluded.pb_ratio,
                    eps=excluded.eps,
                    book_value=excluded.book_value,
                    roe=excluded.roe,
                    dividend_yield_pct=excluded.dividend_yield_pct,
                    debt_to_equity=excluded.debt_to_equity,
                    promoter_holding_pct=excluded.promoter_holding_pct,
                    public_holding_pct=excluded.public_holding_pct;
                """, (f.symbol, f.as_of_date, f.pe_ratio, f.pb_ratio, f.eps, f.book_value, f.roe, f.dividend_yield_pct, f.debt_to_equity, f.promoter_holding_pct, f.public_holding_pct))
            conn.commit()

    def get_latest_fundamentals(self) -> Dict[str, Fundamental]:
        with self._get_connection() as conn:
            query = """
            SELECT f.* FROM fundamentals f
            INNER JOIN (
                SELECT symbol, MAX(as_of_date) as max_date
                FROM fundamentals
                GROUP BY symbol
            ) latest ON f.symbol = latest.symbol AND f.as_of_date = latest.max_date;
            """
            rows = conn.execute(query).fetchall()
            return {
                r["symbol"]: Fundamental(
                    symbol=r["symbol"],
                    as_of_date=r["as_of_date"],
                    pe_ratio=r["pe_ratio"],
                    pb_ratio=r["pb_ratio"],
                    eps=r["eps"],
                    book_value=r["book_value"],
                    roe=r["roe"],
                    dividend_yield_pct=r["dividend_yield_pct"],
                    debt_to_equity=r["debt_to_equity"],
                    promoter_holding_pct=r["promoter_holding_pct"],
                    public_holding_pct=r["public_holding_pct"],
                )
                for r in rows
            }

    # --- IMMUTABLE Transactions ---
    def record_transaction(self, tx: Transaction):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO transactions (
                id, timestamp, trade_date, symbol, action, quantity, price,
                gross_value, broker_commission, sebon_fee, dp_charge, slippage,
                total_cost, net_value, pre_trade_cash, post_trade_cash,
                pre_trade_nav, post_trade_nav, route, reason, rule_ids,
                confidence_pct, decision_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                tx.id, tx.timestamp, tx.trade_date, tx.symbol, tx.action.value, tx.quantity, tx.price,
                tx.gross_value, tx.broker_commission, tx.sebon_fee, tx.dp_charge, tx.slippage,
                tx.total_cost, tx.net_value, tx.pre_trade_cash, tx.post_trade_cash,
                tx.pre_trade_nav, tx.post_trade_nav, tx.route.value, tx.reason,
                json.dumps(tx.rule_ids), tx.confidence_pct, tx.decision_id
            ))
            conn.commit()

    def get_all_transactions(self) -> List[Transaction]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM transactions ORDER BY timestamp ASC;").fetchall()
            return [
                Transaction(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    trade_date=r["trade_date"],
                    symbol=r["symbol"],
                    action=ActionType(r["action"]),
                    quantity=r["quantity"],
                    price=r["price"],
                    gross_value=r["gross_value"],
                    broker_commission=r["broker_commission"],
                    sebon_fee=r["sebon_fee"],
                    dp_charge=r["dp_charge"],
                    slippage=r["slippage"],
                    total_cost=r["total_cost"],
                    net_value=r["net_value"],
                    pre_trade_cash=r["pre_trade_cash"],
                    post_trade_cash=r["post_trade_cash"],
                    pre_trade_nav=r["pre_trade_nav"],
                    post_trade_nav=r["post_trade_nav"],
                    route=StrategicRoute(r["route"]),
                    reason=r["reason"],
                    rule_ids=json.loads(r["rule_ids"]),
                    confidence_pct=r["confidence_pct"],
                    decision_id=r["decision_id"],
                )
                for r in rows
            ]

    # --- IMMUTABLE Decisions ---
    def record_decision(self, dec: Decision):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO decisions (
                id, timestamp, trade_date, symbol, action, confidence_pct,
                target_quantity, estimated_price, capital_allocation_npr, route,
                structural_score, capital_velocity_score, physical_risk_score,
                regulatory_risk_score, bottleneck_score, literature_score,
                elite_alignment_score, sentiment_score, optionality_score,
                golden_zone_score, cognitive_delta_score, narrative_bias_score,
                anchoring_bias_score, recency_bias_score, intrinsic_value_est,
                delta_pct, final_score, reason_summary, applied_rules,
                invalidation_condition, executed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                dec.id, dec.timestamp, dec.trade_date, dec.symbol, dec.action.value, dec.confidence_pct,
                dec.target_quantity, dec.estimated_price, dec.capital_allocation_npr, dec.route.value,
                dec.structural_score, dec.capital_velocity_score, dec.physical_risk_score,
                dec.regulatory_risk_score, dec.bottleneck_score, dec.literature_score,
                dec.elite_alignment_score, dec.sentiment_score, dec.optionality_score,
                dec.golden_zone_score, dec.cognitive_delta_score, dec.narrative_bias_score,
                dec.anchoring_bias_score, dec.recency_bias_score, dec.intrinsic_value_est,
                dec.delta_pct, dec.final_score, dec.reason_summary, json.dumps(dec.applied_rules),
                dec.invalidation_condition, int(dec.executed)
            ))
            conn.commit()

    def get_recent_decisions(self, limit: int = 50) -> List[Decision]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM decisions ORDER BY timestamp DESC LIMIT ?;", (limit,)).fetchall()
            return [
                Decision(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    trade_date=r["trade_date"],
                    symbol=r["symbol"],
                    action=ActionType(r["action"]),
                    confidence_pct=r["confidence_pct"],
                    target_quantity=r["target_quantity"],
                    estimated_price=r["estimated_price"],
                    capital_allocation_npr=r["capital_allocation_npr"],
                    route=StrategicRoute(r["route"]),
                    structural_score=r["structural_score"],
                    capital_velocity_score=r["capital_velocity_score"],
                    physical_risk_score=r["physical_risk_score"],
                    regulatory_risk_score=r["regulatory_risk_score"],
                    bottleneck_score=r["bottleneck_score"],
                    literature_score=r["literature_score"],
                    elite_alignment_score=r["elite_alignment_score"],
                    sentiment_score=r["sentiment_score"],
                    optionality_score=r["optionality_score"],
                    golden_zone_score=r["golden_zone_score"],
                    cognitive_delta_score=r["cognitive_delta_score"],
                    narrative_bias_score=r["narrative_bias_score"],
                    anchoring_bias_score=r["anchoring_bias_score"],
                    recency_bias_score=r["recency_bias_score"],
                    intrinsic_value_est=r["intrinsic_value_est"],
                    delta_pct=r["delta_pct"],
                    final_score=r["final_score"],
                    reason_summary=r["reason_summary"],
                    applied_rules=json.loads(r["applied_rules"]),
                    invalidation_condition=r["invalidation_condition"],
                    executed=bool(r["executed"]),
                )
                for r in rows
            ]

    # --- Portfolio Snapshots ---
    def save_snapshot(self, snap: PortfolioSnapshot):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO portfolio_snapshots (
                trade_date, timestamp, total_assets, cash, invested_value,
                cash_weight_pct, shares_outstanding, nav_per_share, total_nav,
                daily_return_pct, cumulative_return_pct, high_water_mark,
                drawdown_pct, annualized_volatility_pct, sharpe_ratio,
                compliance_score_pct, status, market_regime, holdings_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(trade_date) DO UPDATE SET
                timestamp=excluded.timestamp,
                total_assets=excluded.total_assets,
                cash=excluded.cash,
                invested_value=excluded.invested_value,
                cash_weight_pct=excluded.cash_weight_pct,
                shares_outstanding=excluded.shares_outstanding,
                nav_per_share=excluded.nav_per_share,
                total_nav=excluded.total_nav,
                daily_return_pct=excluded.daily_return_pct,
                cumulative_return_pct=excluded.cumulative_return_pct,
                high_water_mark=excluded.high_water_mark,
                drawdown_pct=excluded.drawdown_pct,
                annualized_volatility_pct=excluded.annualized_volatility_pct,
                sharpe_ratio=excluded.sharpe_ratio,
                compliance_score_pct=excluded.compliance_score_pct,
                status=excluded.status,
                market_regime=excluded.market_regime,
                holdings_count=excluded.holdings_count;
            """, (
                snap.trade_date, snap.timestamp, snap.total_assets, snap.cash, snap.invested_value,
                snap.cash_weight_pct, snap.shares_outstanding, snap.nav_per_share, snap.total_nav,
                snap.daily_return_pct, snap.cumulative_return_pct, snap.high_water_mark,
                snap.drawdown_pct, snap.annualized_volatility_pct, snap.sharpe_ratio,
                snap.compliance_score_pct, snap.status.value, snap.market_regime.value, snap.holdings_count
            ))
            conn.commit()

    def get_all_snapshots(self) -> List[PortfolioSnapshot]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM portfolio_snapshots ORDER BY trade_date ASC;").fetchall()
            return [
                PortfolioSnapshot(
                    trade_date=r["trade_date"],
                    timestamp=r["timestamp"],
                    total_assets=r["total_assets"],
                    cash=r["cash"],
                    invested_value=r["invested_value"],
                    cash_weight_pct=r["cash_weight_pct"],
                    shares_outstanding=r["shares_outstanding"],
                    nav_per_share=r["nav_per_share"],
                    total_nav=r["total_nav"],
                    daily_return_pct=r["daily_return_pct"],
                    cumulative_return_pct=r["cumulative_return_pct"],
                    high_water_mark=r["high_water_mark"],
                    drawdown_pct=r["drawdown_pct"],
                    annualized_volatility_pct=r["annualized_volatility_pct"],
                    sharpe_ratio=r["sharpe_ratio"],
                    compliance_score_pct=r["compliance_score_pct"],
                    status=CompanyStatus(r["status"]),
                    market_regime=MarketRegime(r["market_regime"]),
                    holdings_count=r["holdings_count"],
                )
                for r in rows
            ]

    # --- Compliance Checks ---
    def record_compliance_checks(self, checks: List[ComplianceRecord]):
        with self._get_connection() as conn:
            for c in checks:
                conn.execute("""
                INSERT INTO compliance_checks (id, timestamp, trade_date, rule_id, rule_name, threshold_desc, current_value, limit_value, passed, severity, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (c.id, c.timestamp, c.trade_date, c.rule_id, c.rule_name, c.threshold_desc, c.current_value, c.limit_value, int(c.passed), c.severity, c.message))
            conn.commit()

    def get_latest_compliance(self, trade_date: Optional[str] = None) -> List[ComplianceRecord]:
        with self._get_connection() as conn:
            if trade_date:
                rows = conn.execute("SELECT * FROM compliance_checks WHERE trade_date = ?;", (trade_date,)).fetchall()
            else:
                rows = conn.execute("""
                SELECT c.* FROM compliance_checks c
                INNER JOIN (
                    SELECT MAX(trade_date) as max_date FROM compliance_checks
                ) latest ON c.trade_date = latest.max_date;
                """).fetchall()
            return [
                ComplianceRecord(
                    id=r["id"],
                    timestamp=r["timestamp"],
                    trade_date=r["trade_date"],
                    rule_id=r["rule_id"],
                    rule_name=r["rule_name"],
                    threshold_desc=r["threshold_desc"],
                    current_value=r["current_value"],
                    limit_value=r["limit_value"],
                    passed=bool(r["passed"]),
                    severity=r["severity"],
                    message=r["message"],
                )
                for r in rows
            ]

    # --- Benchmark History ---
    def save_benchmarks(self, records: List[BenchmarkRecord]):
        with self._get_connection() as conn:
            for b in records:
                conn.execute("""
                INSERT INTO benchmarks (trade_date, ai_company_nav, ai_company_return_pct, human_strategy_nav, human_strategy_return_pct, nepse_index, nepse_return_pct, equal_weight_nav, equal_weight_return_pct)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(trade_date) DO UPDATE SET
                    ai_company_nav=excluded.ai_company_nav,
                    ai_company_return_pct=excluded.ai_company_return_pct,
                    human_strategy_nav=excluded.human_strategy_nav,
                    human_strategy_return_pct=excluded.human_strategy_return_pct,
                    nepse_index=excluded.nepse_index,
                    nepse_return_pct=excluded.nepse_return_pct,
                    equal_weight_nav=excluded.equal_weight_nav,
                    equal_weight_return_pct=excluded.equal_weight_return_pct;
                """, (b.trade_date, b.ai_company_nav, b.ai_company_return_pct, b.human_strategy_nav, b.human_strategy_return_pct, b.nepse_index, b.nepse_return_pct, b.equal_weight_nav, b.equal_weight_return_pct))
            conn.commit()

    def get_all_benchmarks(self) -> List[BenchmarkRecord]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM benchmarks ORDER BY trade_date ASC;").fetchall()
            return [
                BenchmarkRecord(
                    trade_date=r["trade_date"],
                    ai_company_nav=r["ai_company_nav"],
                    ai_company_return_pct=r["ai_company_return_pct"],
                    human_strategy_nav=r["human_strategy_nav"],
                    human_strategy_return_pct=r["human_strategy_return_pct"],
                    nepse_index=r["nepse_index"],
                    nepse_return_pct=r["nepse_return_pct"],
                    equal_weight_nav=r["equal_weight_nav"],
                    equal_weight_return_pct=r["equal_weight_return_pct"],
                )
                for r in rows
            ]

    # --- Timeline Events ---
    def record_timeline_event(self, event_date: str, category: str, title: str, description: str, nav_at_event: Optional[float] = None, meta: Optional[Dict] = None):
        with self._get_connection() as conn:
            conn.execute("""
            INSERT INTO timeline_events (timestamp, event_date, category, title, description, nav_at_event, meta_json)
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (datetime.now().isoformat(), event_date, category, title, description, nav_at_event, json.dumps(meta or {})))
            conn.commit()

    def get_all_timeline_events(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM timeline_events ORDER BY event_date ASC, id ASC;").fetchall()
            return [
                {
                    "id": r["id"],
                    "timestamp": r["timestamp"],
                    "event_date": r["event_date"],
                    "category": r["category"],
                    "title": r["title"],
                    "description": r["description"],
                    "nav_at_event": r["nav_at_event"],
                    "meta": json.loads(r["meta_json"]) if r["meta_json"] else {},
                }
                for r in rows
            ]
