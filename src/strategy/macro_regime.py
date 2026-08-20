"""Macro Regime Detection & Strategic Asset Allocation (SAA) Tactical Tilt Engine."""
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
import yfinance as yf

from src.strategy.policy import InvestmentPolicy

logger = logging.getLogger(__name__)


class MacroRegimeEngine:
    """Ingests global macro signals, classifies global regime, and calculates tactical tilts."""

    def __init__(self, policy: InvestmentPolicy):
        self.policy = policy
        self.regime_cache: Dict[str, Any] = {}

    def fetch_macro_indicators(self) -> Dict[str, float]:
        """Fetch live macro indicators: US 10Y Yield, DXY Proxy, VIX, Gold, BTC, USD/NPR."""
        macro_data = {
            "us_10y_yield": 4.25,
            "dxy_proxy": 28.50,
            "vix": 16.50,
            "gold_spot_usd": 2650.0,
            "btc_price_usd": 92000.0,
            "usd_npr_rate": 135.20,
            "nepse_sentiment_score": 58.0
        }
        
        symbols_to_fetch = ["^TNX", "UUP", "^VIX", "GLD", "BTC-USD", "NPR=X"]
        try:
            data = yf.download(symbols_to_fetch, period="5d", group_by="ticker", auto_adjust=True, progress=False)
            if not data.empty:
                if "^TNX" in data and not data["^TNX"].empty:
                    macro_data["us_10y_yield"] = float(data["^TNX"]["Close"].dropna().iloc[-1])
                if "UUP" in data and not data["UUP"].empty:
                    macro_data["dxy_proxy"] = float(data["UUP"]["Close"].dropna().iloc[-1])
                if "^VIX" in data and not data["^VIX"].empty:
                    macro_data["vix"] = float(data["^VIX"]["Close"].dropna().iloc[-1])
                if "GLD" in data and not data["GLD"].empty:
                    macro_data["gold_spot_usd"] = float(data["GLD"]["Close"].dropna().iloc[-1]) * 10.0 # GLD is ~1/10 oz
                if "BTC-USD" in data and not data["BTC-USD"].empty:
                    macro_data["btc_price_usd"] = float(data["BTC-USD"]["Close"].dropna().iloc[-1])
                if "NPR=X" in data and not data["NPR=X"].empty:
                    macro_data["usd_npr_rate"] = float(data["NPR=X"]["Close"].dropna().iloc[-1])
        except Exception as e:
            logger.warning(f"Macro indicator fetch exception ({e}); fallback baselines engaged.")
            
        return macro_data

    def detect_regime(self, macro_data: Dict[str, float]) -> Dict[str, Any]:
        """Classify macro environment into one of 4 regimes."""
        vix = macro_data.get("vix", 16.5)
        us10y = macro_data.get("us_10y_yield", 4.25)
        dxy = macro_data.get("dxy_proxy", 28.5)
        
        if vix > 24.0:
            regime = "Risk-Off"
            rationale = "Elevated VIX volatility and flight to safety; defensive liquidity prioritised."
        elif us10y > 4.6 and vix > 18.0:
            regime = "Stagflation / Inflation Hedge"
            rationale = "Rising sovereign yields and sticky inflation expectations; physical gold prioritized."
        elif dxy > 30.5:
            regime = "Liquidity Crunch"
            rationale = "Dollar liquidity strain and FX pressure on emerging economies; maximum cash reserve."
        else:
            regime = "Risk-On"
            rationale = "Accommodative cross-asset conditions, stable volatility, positive growth momentum."

        return {
            "regime": regime,
            "rationale": rationale,
            "macro_signals": macro_data,
            "timestamp": datetime.now().isoformat()
        }

    def calculate_saa_and_tilts(self, regime_info: Dict[str, Any], current_allocations: Dict[str, float]) -> Dict[str, Any]:
        """Calculates Strategic Asset Allocation baseline, tactical tilt deviation, and target allocations."""
        regime = regime_info["regime"]
        
        # Baseline SAA
        saa = {
            "Equities": {
                "strategic_target_pct": 40.0,
                "sub_classes": {
                    "Domestic (NEPSE)": 20.0,
                    "Global (US/India)": 20.0
                }
            },
            "Gold & Metals": {
                "strategic_target_pct": 20.0,
                "sub_classes": {
                    "Physical / GLD Proxy": 15.0,
                    "Paper / Futures": 5.0
                }
            },
            "Digital Assets": {
                "strategic_target_pct": 15.0,
                "sub_classes": {
                    "BTC": 10.0,
                    "ETH": 5.0
                }
            },
            "FX & Cash": {
                "strategic_target_pct": 25.0,
                "sub_classes": {
                    "NPR Cash": 15.0,
                    "USD Cash": 10.0
                }
            }
        }
        
        # Tactical Tilts by regime
        tilt_map = {
            "Risk-On": {"Equities": 5.0, "Gold & Metals": -4.0, "Digital Assets": 3.0, "FX & Cash": -4.0},
            "Risk-Off": {"Equities": -5.0, "Gold & Metals": 6.0, "Digital Assets": -5.0, "FX & Cash": 4.0},
            "Stagflation / Inflation Hedge": {"Equities": -6.0, "Gold & Metals": 8.0, "Digital Assets": -4.0, "FX & Cash": 2.0},
            "Liquidity Crunch": {"Equities": -8.0, "Gold & Metals": -2.0, "Digital Assets": -8.0, "FX & Cash": 18.0}
        }
        
        tilts = tilt_map.get(regime, {"Equities": 0.0, "Gold & Metals": 0.0, "Digital Assets": 0.0, "FX & Cash": 0.0})
        
        # Apply tilts
        calibrated_targets = {}
        for asset_class, data in saa.items():
            base = data["strategic_target_pct"]
            tilt = tilts.get(asset_class, 0.0)
            calibrated_targets[asset_class] = round(base + tilt, 1)

        # Ethical Governance Override: If crypto target > 20% NAV, veto tilt and enforce 20% cap
        if calibrated_targets.get("Digital Assets", 0.0) > 20.0:
            excess = calibrated_targets["Digital Assets"] - 20.0
            calibrated_targets["Digital Assets"] = 20.0
            calibrated_targets["FX & Cash"] += excess
            logger.info("Ethical Governance Override Triggered: Digital Assets capped at 20.0% NAV.")

        return {
            "baseline_saa": saa,
            "regime": regime,
            "tactical_tilts": tilts,
            "tactical_target_allocation": calibrated_targets,
            "current_allocation": current_allocations
        }
