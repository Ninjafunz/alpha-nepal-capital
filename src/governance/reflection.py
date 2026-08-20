from typing import List, Dict
from src.data.models import PortfolioHolding, Transaction, ActionType
from datetime import datetime

class ReflectionEngine:
    """Self-reflection engine for AI post-trade journaling and win-rate analysis."""
    
    def __init__(self, policy):
        self.policy = policy
        
    def evaluate_holdings(self, holdings: Dict[str, PortfolioHolding]) -> List[dict]:
        """Generates post-mortems for deeply losing trades and reinforcements for winning trades."""
        reflections = []
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        for symbol, h in holdings.items():
            if h.unrealized_pnl_pct <= -5.0:
                reflections.append({
                    "date": date_str,
                    "symbol": symbol,
                    "profile_id": h.profile_id,
                    "type": "LOSS_POST_MORTEM",
                    "pnl_pct": h.unrealized_pnl_pct,
                    "message": f"Position in {symbol} is down {h.unrealized_pnl_pct:.1f}%. Hypothesis: Short-term momentum overpowered our structural valuation gap. Will continue to monitor for margin call or invalidation threshold."
                })
            elif h.unrealized_pnl_pct >= 5.0:
                reflections.append({
                    "date": date_str,
                    "symbol": symbol,
                    "profile_id": h.profile_id,
                    "type": "WIN_REINFORCEMENT",
                    "pnl_pct": h.unrealized_pnl_pct,
                    "message": f"Position in {symbol} is up {h.unrealized_pnl_pct:.1f}%. Our cognitive delta thesis was correct and the market is re-pricing to intrinsic value."
                })
        return reflections

    def calculate_win_rate(self, tx_ledger: List[Transaction]) -> dict:
        """Calculates win rate based on realized PnL of past sell transactions."""
        # Simple proxy: how many sells were profitable vs unprofitable
        sells = [tx for tx in tx_ledger if tx.action == ActionType.SELL]
        if not sells:
            return {"hit_rate_pct": 0.0, "total": 0, "wins": 0, "losses": 0}
            
        wins = sum(1 for tx in sells if tx.realized_pnl and tx.realized_pnl > 0)
        losses = len(sells) - wins
        hit_rate = (wins / len(sells)) * 100.0 if sells else 0.0
        
        return {
            "hit_rate_pct": hit_rate,
            "total": len(sells),
            "wins": wins,
            "losses": losses
        }
