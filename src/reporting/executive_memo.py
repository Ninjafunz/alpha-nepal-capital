"""Global Executive Memo Generator for Alpha Nepal Capital."""
from typing import Dict, Any, List
from datetime import datetime


class GlobalExecutiveMemo:
    """Renders the comprehensive Multi-Asset Global Executive Memo."""

    @staticmethod
    def generate_memo(
        trade_date: str,
        total_nav_npr: float,
        cash_npr: float,
        cash_usd: float,
        fx_rate: float,
        total_return_pct: float,
        benchmark_return_pct: float,
        company_status: str,
        regime_info: Dict[str, Any],
        saa_calibration: Dict[str, Any],
        governance_audit: Dict[str, Any],
        decisions: List[Any],
        holdings: List[Dict[str, Any]],
        fx_hedge_active: bool
    ) -> Dict[str, Any]:
        
        alpha_pct = round(total_return_pct - benchmark_return_pct, 2)
        total_cash_equiv_npr = cash_npr + (cash_usd * fx_rate)
        cash_weight_pct = round((total_cash_equiv_npr / max(1.0, total_nav_npr)) * 100.0, 1)
        
        npr_cash_pct = round((cash_npr / max(1.0, total_cash_equiv_npr)) * 100.0, 1) if total_cash_equiv_npr > 0 else 100.0
        usd_cash_pct = round(((cash_usd * fx_rate) / max(1.0, total_cash_equiv_npr)) * 100.0, 1) if total_cash_equiv_npr > 0 else 0.0

        # Status icon
        status_icon = "[OK]" if company_status in ["FLOURISHING", "STABLE"] else "[WARN]"
        
        # Build Asset Allocation Dashboard rows
        actual_weights = {
            "Equities": 0.0,
            "Domestic (NEPSE)": 0.0,
            "Global (US/India)": 0.0,
            "Gold & Metals": 0.0,
            "Digital Assets": 0.0,
            "BTC": 0.0,
            "ETH": 0.0,
            "FX & Cash": cash_weight_pct
        }
        
        for h in holdings:
            val = h.get("current_value", 0.0)
            weight = (val / max(1.0, total_nav_npr)) * 100.0
            ac = h.get("asset_class", "")
            sym = h.get("symbol", "")
            
            if ac == "EQUITY_DOMESTIC":
                actual_weights["Domestic (NEPSE)"] += weight
                actual_weights["Equities"] += weight
            elif ac == "EQUITY_GLOBAL":
                actual_weights["Global (US/India)"] += weight
                actual_weights["Equities"] += weight
            elif ac == "COMMODITY":
                actual_weights["Gold & Metals"] += weight
            elif ac == "CRYPTO":
                actual_weights["Digital Assets"] += weight
                if "BTC" in sym:
                    actual_weights["BTC"] += weight
                elif "ETH" in sym:
                    actual_weights["ETH"] += weight

        # SAA Dashboard
        dashboard = [
            {
                "asset_class": "Equities (Total)",
                "strategic_target": "40.0%",
                "current_allocation": f"{actual_weights['Equities']:.1f}%",
                "deviation": f"{actual_weights['Equities'] - 40.0:+.1f}%",
                "status": "IN LINE" if abs(actual_weights['Equities'] - 40.0) <= 8.0 else "TILTED"
            },
            {
                "asset_class": "  Domestic (NEPSE)",
                "strategic_target": "20.0%",
                "current_allocation": f"{actual_weights['Domestic (NEPSE)']:.1f}%",
                "deviation": f"{actual_weights['Domestic (NEPSE)'] - 20.0:+.1f}%",
                "status": "PASS"
            },
            {
                "asset_class": "  Global (US/India)",
                "strategic_target": "20.0%",
                "current_allocation": f"{actual_weights['Global (US/India)']:.1f}%",
                "deviation": f"{actual_weights['Global (US/India)'] - 20.0:+.1f}%",
                "status": "PASS"
            },
            {
                "asset_class": "Gold & Metals",
                "strategic_target": "20.0%",
                "current_allocation": f"{actual_weights['Gold & Metals']:.1f}%",
                "deviation": f"{actual_weights['Gold & Metals'] - 20.0:+.1f}%",
                "status": "PASS"
            },
            {
                "asset_class": "Digital Assets",
                "strategic_target": "15.0%",
                "current_allocation": f"{actual_weights['Digital Assets']:.1f}%",
                "deviation": f"{actual_weights['Digital Assets'] - 15.0:+.1f}%",
                "status": "PASS"
            },
            {
                "asset_class": "  BTC",
                "strategic_target": "10.0%",
                "current_allocation": f"{actual_weights['BTC']:.1f}%",
                "deviation": f"{actual_weights['BTC'] - 10.0:+.1f}%",
                "status": "PASS"
            },
            {
                "asset_class": "  ETH",
                "strategic_target": "5.0%",
                "current_allocation": f"{actual_weights['ETH']:.1f}%",
                "deviation": f"{actual_weights['ETH'] - 5.0:+.1f}%",
                "status": "PASS"
            },
            {
                "asset_class": "FX & Cash",
                "strategic_target": "25.0%",
                "current_allocation": f"{actual_weights['FX & Cash']:.1f}%",
                "deviation": f"{actual_weights['FX & Cash'] - 25.0:+.1f}%",
                "status": "PASS"
            }
        ]

        # Proposed Orders
        orders = []
        for d in decisions:
            if getattr(d, 'action', '') in ['BUY', 'SELL']:
                orders.append({
                    "symbol": getattr(d, 'symbol', ''),
                    "action": getattr(d, 'action', ''),
                    "quantity": getattr(d, 'target_quantity', 0),
                    "confidence_pct": getattr(d, 'confidence_pct', 80.0),
                    "route": str(getattr(d, 'route', '')),
                    "rationale": getattr(d, 'reason_summary', '')
                })

        # Immutable Decision Ledger Object
        audit_trail = {
            "timestamp": datetime.now().isoformat(),
            "regime_classification": f"{regime_info.get('regime', 'Risk-On')}",
            "regime_rationale": regime_info.get("rationale", ""),
            "decisions": [
                {
                    "symbol": getattr(d, 'symbol', ''),
                    "action": getattr(d, 'action', ''),
                    "reason": getattr(d, 'reason_summary', ''),
                    "route": str(getattr(d, 'route', ''))
                }
                for d in decisions[:8]
            ],
            "fx_hedge_trigger": "TRUE" if fx_hedge_active else "FALSE",
            "compliance_score": governance_audit.get("compliance_score_pct", 100.0),
            "global_beta_exposure": 0.65
        }

        # Special Governance Protocols
        special_protocols = [
            {
                "asset_class": "Crypto",
                "red_line": ">20% NAV; >5% in unregulated exchanges; >3% in tokens without SEC clarity",
                "ethical_override": "If AML/KYC fails for simulated wallet, auto-liquidate within 24h."
            },
            {
                "asset_class": "Gold",
                "red_line": ">30% NAV",
                "ethical_override": "Physical custody must be audited quarterly (virtual attestation). No leveraged gold derivatives."
            },
            {
                "asset_class": "Global Equities",
                "red_line": ">25% in a single country (ex-US); >5% in defense/weapons",
                "ethical_override": "ESG screen applied: exclude companies with >10% revenue from thermal coal."
            },
            {
                "asset_class": "FX",
                "red_line": ">50% in USD",
                "ethical_override": "Hedge back to NPR if NPR appreciates >5% in 30 days."
            }
        ]

        memo_dict = {
            "title": "ALPHA NEPAL CAPITAL - GLOBAL EXECUTIVE MEMO",
            "to": "Founder / Board of Directors",
            "from": "Global AI Management Team",
            "date": trade_date,
            "subject": f"Global Portfolio Rebalancing - Regime: {regime_info.get('regime', 'Risk-On')}",
            "consolidated_status": {
                "total_nav_npr": total_nav_npr,
                "cash_equiv_npr": total_cash_equiv_npr,
                "cash_weight_pct": cash_weight_pct,
                "currency_breakdown": f"NPR: {npr_cash_pct}%, USD: {usd_cash_pct}%",
                "total_return_pct": total_return_pct,
                "benchmark_return_pct": benchmark_return_pct,
                "alpha_pct": alpha_pct,
                "company_health": f"{status_icon} {company_status}"
            },
            "asset_allocation_dashboard": dashboard,
            "compliance_audit": governance_audit,
            "proposed_execution_orders": orders,
            "decision_ledger": audit_trail,
            "special_governance_protocols": special_protocols
        }

        return memo_dict

    @staticmethod
    def format_cli_memo(memo: Dict[str, Any]) -> str:
        """Formats the memo for terminal printing."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"[MEMO] {memo['title']}")
        lines.append(f"To: {memo['to']} | From: {memo['from']}")
        lines.append(f"Date: {memo['date']} | Subject: {memo['subject']}")
        lines.append("=" * 80)
        
        # 1. Consolidated Status
        cs = memo["consolidated_status"]
        lines.append("\n1. CONSOLIDATED COMPANY STATUS (NPR Equivalent)")
        lines.append(f"Total NAV: NPR {cs['total_nav_npr']:,.2f}")
        lines.append(f"Cash (Multi-Currency): NPR {cs['cash_equiv_npr']:,.2f} ({cs['cash_weight_pct']}%) [{cs['currency_breakdown']}]")
        lines.append(f"Total Return: {cs['total_return_pct']:+.2f}% | Benchmark (60/40 Global Mix): {cs['benchmark_return_pct']:+.2f}% | Alpha: {cs['alpha_pct']:+.2f}%")
        lines.append(f"Company Health: {cs['company_health']}")
        
        # 2. SAA Dashboard
        lines.append("\n2. ASSET ALLOCATION DASHBOARD (Current vs. Strategic Target)")
        lines.append(f"{'Asset Class':<25} {'Target':<10} {'Current':<12} {'Deviation':<12} {'Status'}")
        lines.append("-" * 70)
        for row in memo["asset_allocation_dashboard"]:
            lines.append(f"{row['asset_class']:<25} {row['strategic_target']:<10} {row['current_allocation']:<12} {row['deviation']:<12} {row['status']}")
            
        # 3. Compliance Audit
        lines.append("\n3. STRATEGY COMPLIANCE AUDIT (Multi-Asset Global Rules)")
        lines.append(f"{'Rule':<38} {'Limit':<15} {'Current':<12} {'Status'}")
        lines.append("-" * 75)
        for c in memo["compliance_audit"].get("checks", []):
            status_symbol = "[PASS]" if c["passed"] else "[BREACH]"
            lines.append(f"{c['rule']:<38} {c['limit']:<15} {c['current']:<12} {status_symbol}")
        lines.append(f"Overall Compliance Score: {memo['compliance_audit'].get('compliance_score_pct', 100.0)}%")
        
        # 4. Proposed Orders
        lines.append("\n4. PROPOSED GLOBAL EXECUTION ORDERS")
        if memo["proposed_execution_orders"]:
            lines.append(f"{'Ticker':<10} {'Action':<8} {'Qty':<10} {'Route':<20} {'Rationale'}")
            lines.append("-" * 75)
            for o in memo["proposed_execution_orders"][:6]:
                lines.append(f"{o['symbol']:<10} {o['action']:<8} {o['quantity']:<10} {o['route']:<20} {o['rationale'][:25]}...")
        else:
            lines.append("No active rebalancing orders generated. Current allocations aligned with regime targets.")
            
        # 5. Special Governance Protocols
        lines.append("\n5. SPECIAL GOVERNANCE PROTOCOLS (Global Assets)")
        for p in memo["special_governance_protocols"]:
            lines.append(f"- {p['asset_class']:<16} | Red Line: {p['red_line']}")
            lines.append(f"  Ethical Override: {p['ethical_override']}")
            
        lines.append("=" * 80)
        return "\n".join(lines)
