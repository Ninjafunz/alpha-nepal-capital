"""Transaction Friction & Cost Calculation Engine."""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.data.models import Transaction, ActionType, StrategicRoute
from src.strategy.policy import InvestmentPolicy


class TransactionEngine:
    """Calculates realistic transaction costs on NEPSE and generates immutable transaction records."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.costs = policy.transaction_costs

    def calculate_trade_costs(self, action: ActionType, quantity: int, price: float) -> Dict[str, float]:
        """Calculates broker commission, SEBON fee, DP fee, and slippage."""
        gross_value = round(quantity * price, 2)
        
        # 1. Broker Commission (0.36%)
        broker_comm = round(gross_value * (self.costs.broker_commission_pct / 100.0), 2)
        
        # 2. SEBON Regulatory Fee (0.015%)
        sebon_fee = round(gross_value * (self.costs.sebon_fee_pct / 100.0), 2)
        
        # 3. DP Charge (NPR 25 per sell transaction)
        dp_charge = self.costs.dp_charge_npr if action == ActionType.SELL else 0.0
        
        # 4. Slippage (0.10%)
        slippage = round(gross_value * (self.costs.slippage_pct / 100.0), 2)
        
        total_cost = round(broker_comm + sebon_fee + dp_charge + slippage, 2)

        if action == ActionType.BUY:
            net_value = round(gross_value + total_cost, 2)
        else:
            net_value = round(gross_value - total_cost, 2)

        return {
            "gross_value": gross_value,
            "broker_commission": broker_comm,
            "sebon_fee": sebon_fee,
            "dp_charge": dp_charge,
            "slippage": slippage,
            "total_cost": total_cost,
            "net_value": net_value,
        }

    def build_transaction(
        self,
        trade_date: str,
        symbol: str,
        action: ActionType,
        quantity: int,
        price: float,
        pre_cash: float,
        pre_nav: float,
        route: StrategicRoute,
        reason: str,
        rule_ids: List[str],
        confidence_pct: float,
        decision_id: str,
    ) -> Transaction:
        """Constructs an immutable Transaction object with updated pre/post state."""
        costs = self.calculate_trade_costs(action, quantity, price)
        
        if action == ActionType.BUY:
            post_cash = round(pre_cash - costs["net_value"], 2)
        else:
            post_cash = round(pre_cash + costs["net_value"], 2)

        # NAV post trade reflects transaction friction incurred
        post_nav = round(pre_nav - (costs["total_cost"] / self.policy.company.company.total_shares_issued), 4)

        tx_id = f"TX-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        return Transaction(
            id=tx_id,
            timestamp=datetime.now().isoformat(),
            trade_date=trade_date,
            symbol=symbol,
            action=action,
            quantity=quantity,
            price=price,
            gross_value=costs["gross_value"],
            broker_commission=costs["broker_commission"],
            sebon_fee=costs["sebon_fee"],
            dp_charge=costs["dp_charge"],
            slippage=costs["slippage"],
            total_cost=costs["total_cost"],
            net_value=costs["net_value"],
            pre_trade_cash=pre_cash,
            post_trade_cash=post_cash,
            pre_trade_nav=pre_nav,
            post_trade_nav=post_nav,
            route=route,
            reason=reason,
            rule_ids=rule_ids,
            confidence_pct=confidence_pct,
            decision_id=decision_id,
        )
