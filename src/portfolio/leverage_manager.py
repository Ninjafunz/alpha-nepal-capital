from src.strategy.policy import InvestmentPolicy
from src.strategy.macro_rates import MacroRatesMonitor

class LeverageManager:
    """Handles autonomous borrowing and deleveraging."""
    
    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.rate_monitor = MacroRatesMonitor(policy)

    def evaluate_borrowing(self, expected_yield: float, asset_class: str, current_equity: float, current_liabilities: float) -> dict:
        """
        Determines if the AI should borrow money to invest.
        """
        if not self.policy.leverage.enabled:
            return {"action": "NONE", "amount": 0.0, "reason": "Leverage disabled"}

        cost_of_capital = self.rate_monitor.get_cost_of_capital(asset_class)
        
        # We need a risk premium of at least 3% over borrowing cost to justify leverage
        risk_premium_threshold = 3.0
        
        if expected_yield > (cost_of_capital + risk_premium_threshold):
            # Calculate max allowed borrowing
            max_borrowing = current_equity * (self.policy.leverage.max_leverage_ratio - 1.0)
            available_borrowing = max(0.0, max_borrowing - current_liabilities)
            
            if available_borrowing > 0:
                # Borrow a safe chunk, not everything at once (e.g. 10% of equity)
                target_borrowing = min(available_borrowing, current_equity * 0.10)
                return {
                    "action": "BORROW", 
                    "amount": target_borrowing, 
                    "reason": f"Expected yield {expected_yield:.1f}% > Cost of Capital {cost_of_capital:.1f}%"
                }

        # De-leveraging logic
        if expected_yield < cost_of_capital:
            if current_liabilities > 0:
                target_repayment = min(current_liabilities, current_equity * 0.10)
                return {
                    "action": "REPAY", 
                    "amount": target_repayment, 
                    "reason": f"Expected yield {expected_yield:.1f}% < Cost of Capital {cost_of_capital:.1f}%"
                }
                
        return {"action": "NONE", "amount": 0.0, "reason": "Optimal capital structure maintained"}
