import yfinance as yf
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from src.data.models import PriceBar, Stock, AssetClass

class GlobalMarketsAPI:
    """Fetches international market prices and applies FX conversions."""
    
    def __init__(self):
        self.fx_rate_usd_npr = 135.20  # Fallback
        
    def fetch_usd_npr_rate(self) -> float:
        """Fetch live USD/NPR forex rate."""
        try:
            ticker = yf.Ticker("NPR=X")
            hist = ticker.history(period="2d")
            if not hist.empty:
                val = float(hist['Close'].dropna().iloc[-1])
                if val > 0:
                    self.fx_rate_usd_npr = val
        except Exception:
            pass
        return self.fx_rate_usd_npr

    def fetch_global_prices(self, universe: List[Stock]) -> List[PriceBar]:
        """Fetch prices for non-domestic assets and convert to NPR."""
        fx_rate = self.fetch_usd_npr_rate()
        
        global_assets = [s for s in universe if s.asset_class != "EQUITY_DOMESTIC" and s.asset_class != AssetClass.EQUITY_DOMESTIC]
        if not global_assets:
            return []
            
        symbols = [s.symbol for s in global_assets]
        bars = []
        trade_date = datetime.now().strftime("%Y-%m-%d")
        
        try:
            data = yf.download(symbols, period="5d", group_by="ticker", auto_adjust=True, progress=False)
            
            for asset in global_assets:
                sym = asset.symbol
                if sym in data and not data[sym].empty:
                    df = data[sym].dropna(subset=['Close'])
                elif len(symbols) == 1 and not data.empty:
                    df = data.dropna(subset=['Close'])
                else:
                    continue
                    
                if df.empty or len(df) < 1:
                    continue
                    
                current_close_usd = float(df['Close'].iloc[-1])
                prev_close_usd = float(df['Close'].iloc[-2]) if len(df) > 1 else current_close_usd
                
                current_close_npr = current_close_usd * fx_rate
                prev_close_npr = prev_close_usd * fx_rate
                
                pct_change = ((current_close_npr - prev_close_npr) / prev_close_npr * 100.0) if prev_close_npr > 0 else 0.0
                
                vol_val = 1000
                if 'Volume' in df and not df['Volume'].empty:
                    raw_vol = df['Volume'].iloc[-1]
                    if not math.isnan(raw_vol):
                        vol_val = int(raw_vol)
                
                open_val = float(df['Open'].iloc[-1]) if 'Open' in df and not math.isnan(df['Open'].iloc[-1]) else current_close_usd
                high_val = float(df['High'].iloc[-1]) if 'High' in df and not math.isnan(df['High'].iloc[-1]) else current_close_usd
                low_val = float(df['Low'].iloc[-1]) if 'Low' in df and not math.isnan(df['Low'].iloc[-1]) else current_close_usd

                bars.append(PriceBar(
                    symbol=sym,
                    trade_date=trade_date,
                    open=open_val * fx_rate,
                    high=high_val * fx_rate,
                    low=low_val * fx_rate,
                    close=current_close_npr,
                    volume=vol_val,
                    turnover=0.0,
                    prev_close=prev_close_npr,
                    point_change=current_close_npr - prev_close_npr,
                    pct_change=pct_change
                ))
        except Exception as e:
            print(f"[WARNING] GlobalMarketsAPI batch fetch error: {e}")
            
        return bars
