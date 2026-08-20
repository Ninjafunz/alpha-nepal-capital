class MacroRatesMonitor:
    """Tracks Central Bank and Interbank interest rates to determine Cost of Capital."""
    
    def __init__(self, policy):
        self.policy = policy
        self.base_lending_rate = 8.5
        
    def get_cost_of_capital(self, asset_class: str) -> float:
        """Return the cost of borrowing for a specific asset class."""
        risk_premium = self.policy.leverage.borrowing_rate_spread_pct
        
        if asset_class == "CRYPTO":
            return self.base_lending_rate + risk_premium + 5.0
        return self.base_lending_rate + risk_premium
