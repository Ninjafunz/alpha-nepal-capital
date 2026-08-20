from src.data.models import Stock, PriceBar, AssetClass

class MacroDeltaEngine:
    """Valuation engine for non-yielding assets (Crypto, Commodities, Forex)."""
    
    def __init__(self, policy):
        self.policy = policy

    def calculate_gap(self, asset: Stock, bar: PriceBar) -> float:
        """
        Returns the Cognitive/Macro Delta % (mispricing gap).
        Positive delta means asset is undervalued.
        """
        if asset.asset_class == AssetClass.COMMODITY:
            # Commodities: Proxied by historical baseline vs current momentum
            # In a real model, this uses TIPS yields. We use a momentum proxy.
            intrinsic = bar.close * 1.15 if bar.pct_change > 0 else bar.close * 0.90
            return ((intrinsic - bar.close) / bar.close) * 100.0
            
        elif asset.asset_class == AssetClass.CRYPTO:
            # Crypto: Highly volatile, large gaps based on volatility parity
            # We assume a fixed long-term monetary premium target
            intrinsic = bar.close * 1.25 # Aggressive monetary premium target
            return ((intrinsic - bar.close) / bar.close) * 100.0
            
        elif asset.asset_class == AssetClass.EQUITY_GLOBAL:
            # Global Equities: Use standard EPS compounding. Mocked here.
            intrinsic = bar.close * 1.20 
            return ((intrinsic - bar.close) / bar.close) * 100.0
            
        return 0.0
