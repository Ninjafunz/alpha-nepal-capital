import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.data.models import PriceBar, Stock, AssetClass

class GlobalMarketsAPI:
    """Fetches international market prices and applies FX conversions."""
    
    def __init__(self):
        self.fx_rate_usd_npr = 135.0  # Fallback
        
    def fetch_usd_npr_rate(self) -> float:
        """Fetch live USD/NPR forex rate."""
        try:
            ticker = yf.Ticker("NPR=X")
            hist = ticker.history(period="1d")
            if not hist.empty:
                self.fx_rate_usd_npr = float(hist['Close'].iloc[-1])
        except Exception:
            pass # Use fallback
        return self.fx_rate_usd_npr

    def fetch_global_prices(self, universe: List[Stock]) -> List[PriceBar]:
        """Fetch prices for non-domestic assets and convert to NPR."""
        fx_rate = self.fetch_usd_npr_rate()
        
        global_assets = [s for s in universe if s.asset_class != AssetClass.EQUITY_DOMESTIC]
        if not global_assets:
            return []
            
        symbols = [s.symbol for s in global_assets]
        
        bars = []
        trade_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Download all symbols in one batch
            data = yf.download(symbols, period="2d", group_by="ticker", auto_adjust=True, progress=False)
            
            for asset in global_assets:
                sym = asset.symbol
                
                # yf.download structure depends on if 1 symbol or many
                if len(symbols) == 1:
                    df = data
                else:
                    df = data[sym]
                    
                if df.empty or len(df) < 1:
                    continue
                    
                # Convert USD to NPR
                current_close_usd = float(df['Close'].iloc[-1])
                prev_close_usd = float(df['Close'].iloc[-2]) if len(df) > 1 else current_close_usd
                
                current_close_npr = current_close_usd * fx_rate
                prev_close_npr = prev_close_usd * fx_rate
                
                pct_change = ((current_close_npr - prev_close_npr) / prev_close_npr * 100.0) if prev_close_npr > 0 else 0.0
                
                bars.append(PriceBar(
                    symbol=sym,
                    trade_date=trade_date,
                    open=float(df['Open'].iloc[-1]) * fx_rate,
                    high=float(df['High'].iloc[-1]) * fx_rate,
                    low=float(df['Low'].iloc[-1]) * fx_rate,
                    close=current_close_npr,
                    volume=int(df.get('Volume', 0).iloc[-1]),
                    turnover=0.0,
                    prev_close=prev_close_npr,
                    point_change=current_close_npr - prev_close_npr,
                    pct_change=pct_change
                ))
        except Exception as e:
            print(f"[ERROR] GlobalMarketsAPI fetch failed: {e}")
            
        return bars
