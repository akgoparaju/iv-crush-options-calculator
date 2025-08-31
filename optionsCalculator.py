#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Options / Earnings Calculator — provider‑agnostic, rate‑limit tolerant, with logging
----------------------------------------------------------------------------------
- GUI: FreeSimpleGUI (Tkinter)
- Primary data: Yahoo Finance via yfinance (free, but throttled)
- Optional fallbacks:
    • Alpha Vantage (FREE key) for PRICE only — env var: ALPHA_VANTAGE_API_KEY
    • Finnhub (FREE tier) for OPTIONS (limited) + PRICE — env var: FINNHUB_API_KEY
    • Tradier (FREE sandbox) for OPTIONS — env var: TRADIER_TOKEN (set to sandbox token)
- Demo mode: generates synthetic options to test UI without any API calls
- Logging: writes to ./trade_calculator.log; Debug panel in UI shows raw dicts

Why Yahoo?
----------
Your script needs two things:
  1) A recent UNDERLYING PRICE (to find ATM strikes)
  2) OPTIONS DATA (expirations + quotes) to compute ATM IV & straddle mids

Yahoo (via yfinance) provides both, for free — but rate‑limits hard. This version:
- Minimizes requests, caches prices for 5 minutes, and backs off on rate limits
- Falls back to other providers if you supply API keys (or to Demo Mode)

Setup
-----
• Optional: create a .env in the same folder, e.g.:
    ALPHA_VANTAGE_API_KEY=YOUR_KEY
    FINNHUB_API_KEY=YOUR_KEY
    TRADIER_TOKEN=YOUR_BEARER_TOKEN   # for sandbox or live
• pip install: FreeSimpleGUI yfinance requests pandas numpy
• Run: python optionsCalculator.py

"""

from __future__ import annotations

import os
import sys
import json
import time
import random
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Third‑party deps
import FreeSimpleGUI as sg
import yfinance as yf
import numpy as np
import pandas as pd
import requests
from scipy.interpolate import interp1d

try:
    from yfinance.exceptions import YFRateLimitError  # recent yfinance
except Exception:  # pragma: no cover
    class YFRateLimitError(Exception):
        pass

# --------------------------
# Config & Logging
# --------------------------
LOG_PATH = os.path.abspath(os.path.join(os.getcwd(), "trade_calculator.log"))
PRICE_CACHE_PATH = os.path.abspath(os.path.join(os.getcwd(), ".price_cache.json"))
PRICE_CACHE_TTL_SEC = 300  # 5 minutes
MIN_INTERVAL_BETWEEN_REQUESTS = 0.7
MAX_RETRIES = 3
BASE_DELAY = 0.9

logger = logging.getLogger("trade_calculator")
logger.setLevel(logging.DEBUG)
_fh = logging.FileHandler(LOG_PATH, mode="a", encoding="utf-8")
_fh.setLevel(logging.DEBUG)
_fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_ch = logging.StreamHandler()
_ch.setLevel(logging.ERROR)
_ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
for h in list(logger.handlers):
    logger.removeHandler(h)
logger.addHandler(_fh)
logger.addHandler(_ch)
logger.debug("===== Trade Calculator started (provider‑agnostic) =====")

# --------------------------
# .env loader (optional)
# --------------------------
ENV_PATH = Path(".env")
if ENV_PATH.exists():
    try:
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
    except Exception:
        logger.exception("Failed to parse .env")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
TRADIER_TOKEN = os.getenv("TRADIER_TOKEN")  # sandbox or live
TRADIER_BASE = os.getenv("TRADIER_BASE", "https://sandbox.tradier.com")

# --------------------------
# Utility: disk cache for prices
# --------------------------

def _load_cache() -> Dict[str, Any]:
    try:
        if not os.path.exists(PRICE_CACHE_PATH):
            return {}
        with open(PRICE_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        logger.exception("Failed to load price cache")
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    try:
        with open(PRICE_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f)
    except Exception:
        logger.exception("Failed to save price cache")


def get_cached_price(symbol: str, ttl_sec: int = PRICE_CACHE_TTL_SEC) -> Optional[float]:
    try:
        cache = _load_cache()
        ent = cache.get(symbol.upper())
        if not ent:
            return None
        ts = ent.get("ts"); px = ent.get("price")
        if isinstance(ts, (int, float)) and isinstance(px, (int, float)):
            age = time.time() - ts
            if age <= ttl_sec:
                logger.debug("Using cached price for %s (age=%.1fs)", symbol, age)
                return float(px)
    except Exception:
        logger.exception("get_cached_price failed")
    return None


def set_cached_price(symbol: str, price: float) -> None:
    try:
        cache = _load_cache()
        cache[symbol.upper()] = {"price": float(price), "ts": time.time()}
        _save_cache(cache)
    except Exception:
        logger.exception("set_cached_price failed")

# --------------------------
# Term Structure & Volatility Analysis
# --------------------------

def build_term_structure(days: List[float], ivs: List[float]):
    """Build interpolated term structure spline from implied volatilities."""
    if len(days) < 2 or len(ivs) < 2:
        return None
        
    days = np.array(days)
    ivs = np.array(ivs)
    
    # Sort by days to expiry
    sort_idx = days.argsort()
    days = days[sort_idx]
    ivs = ivs[sort_idx]
    
    # Create interpolation spline
    spline = interp1d(days, ivs, kind='linear', fill_value="extrapolate")
    
    def term_spline(dte: float) -> float:
        """Get implied volatility for given days to expiry."""
        if dte < days[0]:  
            return float(ivs[0])
        elif dte > days[-1]:
            return float(ivs[-1])
        else:  
            return float(spline(dte))
    
    return term_spline


def yang_zhang_volatility(price_history: pd.DataFrame) -> float:
    """
    Calculate Yang-Zhang realized volatility estimator.
    More accurate than close-to-close volatility.
    """
    try:
        if price_history.empty or len(price_history) < 2:
            return 0.0
            
        # Required columns: Open, High, Low, Close
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in price_history.columns for col in required_cols):
            logger.warning("Missing OHLC columns for Yang-Zhang calculation")
            return 0.0
            
        df = price_history[required_cols].dropna()
        if len(df) < 2:
            return 0.0
            
        # Yang-Zhang volatility calculation
        o = np.log(df['Open'])
        h = np.log(df['High'])
        l = np.log(df['Low'])
        c = np.log(df['Close'])
        
        # Overnight returns (close to next open)
        overnight = o[1:].values - c[:-1].values
        
        # Close-to-open returns
        co = o - c.shift(1)
        co = co.dropna()
        
        # High-low variance
        hl = h - l
        
        # Close-to-open variance
        cc = c - o
        
        # Yang-Zhang estimator components
        overnight_var = np.var(overnight, ddof=1) if len(overnight) > 1 else 0
        co_var = np.var(co, ddof=1) if len(co) > 1 else 0
        hl_var = np.mean(hl ** 2) if len(hl) > 0 else 0
        cc_var = np.var(cc, ddof=1) if len(cc) > 1 else 0
        
        # Yang-Zhang volatility (annualized)
        k = 0.34 / (1.34 + (len(df) + 1) / (len(df) - 1))
        yz_var = overnight_var + k * co_var + (1 - k) * (hl_var + cc_var)
        
        return np.sqrt(yz_var * 252)  # Annualized
        
    except Exception as e:
        logger.warning(f"Yang-Zhang volatility calculation failed: {e}")
        return 0.0


def calculate_calendar_spread_metrics(atm_ivs: Dict[str, float], underlying_price: float, 
                                    straddle_price: float = None, 
                                    price_history: pd.DataFrame = None) -> Dict[str, Any]:
    """
    Calculate calendar spread and term structure metrics.
    Returns trading recommendation based on volatility analysis.
    """
    try:
        if len(atm_ivs) < 2:
            return {"error": "Need at least 2 expirations for term structure analysis"}
            
        # Convert expiration dates to days to expiry
        today = datetime.now().date()
        dtes = []
        ivs = []
        
        for exp_date_str, iv in atm_ivs.items():
            try:
                exp_date = datetime.strptime(exp_date_str, "%Y-%m-%d").date()
                dte = (exp_date - today).days
                if dte > 0:  # Only future expirations
                    dtes.append(dte)
                    ivs.append(iv)
            except Exception:
                continue
                
        if len(dtes) < 2:
            return {"error": "Need at least 2 valid future expirations"}
            
        # Build term structure
        term_spline = build_term_structure(dtes, ivs)
        if term_spline is None:
            return {"error": "Failed to build term structure"}
            
        # Calculate metrics
        metrics = {}
        
        # 1. Term structure slope (first expiry to 45 days)
        first_dte = min(dtes)
        if first_dte < 45:
            slope_end = 45
        else:
            # Use second expiration if first is > 45 days
            sorted_dtes = sorted(dtes)
            slope_end = sorted_dtes[1] if len(sorted_dtes) > 1 else first_dte + 15
            
        ts_slope = (term_spline(slope_end) - term_spline(first_dte)) / (slope_end - first_dte)
        metrics['term_structure_slope'] = ts_slope
        metrics['ts_slope_signal'] = ts_slope <= -0.00406  # Bearish term structure
        
        # 2. IV30 vs RV30 ratio
        iv30 = term_spline(30)
        metrics['iv30'] = iv30
        
        if price_history is not None and not price_history.empty:
            rv30 = yang_zhang_volatility(price_history.tail(30))  # Last 30 days
            metrics['rv30'] = rv30
            if rv30 > 0:
                iv_rv_ratio = iv30 / rv30
                metrics['iv_rv_ratio'] = iv_rv_ratio
                metrics['iv_rv_signal'] = iv_rv_ratio >= 1.25  # IV > RV indicates opportunity
            else:
                metrics['iv_rv_ratio'] = None
                metrics['iv_rv_signal'] = False
        else:
            metrics['rv30'] = None
            metrics['iv_rv_ratio'] = None
            metrics['iv_rv_signal'] = False
            
        # 3. Expected move calculation
        if straddle_price and underlying_price > 0:
            expected_move_pct = (straddle_price / underlying_price) * 100
            metrics['expected_move_pct'] = expected_move_pct
        else:
            metrics['expected_move_pct'] = None
            
        # 4. Volume analysis (if price history available)
        if price_history is not None and 'Volume' in price_history.columns:
            recent_volume = price_history['Volume'].tail(30).mean()
            metrics['avg_volume_30d'] = recent_volume
            metrics['volume_signal'] = recent_volume >= 1_500_000  # High volume threshold
        else:
            metrics['avg_volume_30d'] = None
            metrics['volume_signal'] = False
            
        # 5. Overall recommendation
        signals = [
            metrics.get('ts_slope_signal', False),
            metrics.get('iv_rv_signal', False),
            metrics.get('volume_signal', False)
        ]
        
        signal_count = sum(signals)
        if signal_count >= 2:
            recommendation = "BULLISH - Calendar spread opportunity detected"
        elif signal_count == 1:
            recommendation = "NEUTRAL - Some positive signals"
        else:
            recommendation = "BEARISH - No clear calendar spread opportunity"
            
        metrics['recommendation'] = recommendation
        metrics['signal_count'] = signal_count
        
        return metrics
        
    except Exception as e:
        logger.exception("Calendar spread calculation failed")
        return {"error": f"Analysis failed: {str(e)}"}

# --------------------------
# Throttle + retry
# --------------------------
_last_request_ts = 0.0

def _throttle():
    global _last_request_ts
    now = time.time(); elapsed = now - _last_request_ts
    if elapsed < MIN_INTERVAL_BETWEEN_REQUESTS:
        time.sleep(MIN_INTERVAL_BETWEEN_REQUESTS - elapsed)
    _last_request_ts = time.time()


def fetch_with_retries(callable_, *args, **kwargs):
    attempt = 0
    while True:
        try:
            _throttle()
            return callable_(*args, **kwargs)
        except YFRateLimitError as e:
            if attempt >= MAX_RETRIES:
                logger.error("RATE_LIMIT: exhausted retries (%d)", attempt)
                raise
            sleep_s = (BASE_DELAY * (2 ** attempt)) + random.random() * 0.3
            logger.warning("RATE_LIMIT: retry %d after %.2fs", attempt + 1, sleep_s)
            time.sleep(sleep_s)
            attempt += 1

# --------------------------
# Provider interfaces
# --------------------------
class PriceProvider:
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        raise NotImplementedError

class OptionsProvider:
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        raise NotImplementedError
    def get_chain(self, symbol: str, expiration: str):
        """Return an object with .calls and .puts DataFrames (yfinance‑like), or raise."""
        raise NotImplementedError

# --------------------------
# Yahoo provider (price + options)
# --------------------------
class YahooProvider(PriceProvider, OptionsProvider):
    def __init__(self):
        self._tickers: Dict[str, yf.Ticker] = {}

    def _tkr(self, symbol: str) -> yf.Ticker:
        t = self._tickers.get(symbol)
        if t is None:
            t = yf.Ticker(symbol)
            self._tickers[symbol] = t
        return t

    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        tkr = self._tkr(symbol)
        # fast path
        try:
            def _fast():
                info = tkr.fast_info
                lp = getattr(info, "last_price", None)
                if lp is None and isinstance(info, dict):
                    lp = info.get("last_price")
                return lp
            price = fetch_with_retries(_fast)
            if price is not None:
                return float(price), "yahoo.fast_info"
        except Exception:
            logger.info("Yahoo fast_info failed; trying intraday history")
        # fallback intraday
        try:
            def _intraday():
                df = tkr.history(period="1d", interval="1m")
                if df is not None and not df.empty:
                    return float(df["Close"].iloc[-1])
                return None
            price = fetch_with_retries(_intraday)
            if price is not None:
                return float(price), "yahoo.history"
        except Exception:
            logger.exception("Yahoo intraday history failed")
        return None, "yahoo.none"

    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        tkr = self._tkr(symbol)
        try:
            def _opts():
                return list(tkr.options or [])
            exps = fetch_with_retries(_opts)
            if not exps:
                return []
            # Filter future and sort
            today = datetime.utcnow().date()
            fut = [e for e in exps if datetime.strptime(e, "%Y-%m-%d").date() > today]
            fut.sort(key=lambda d: datetime.strptime(d, "%Y-%m-%d").date())
            return fut[:max_count]
        except Exception:
            logger.exception("Yahoo get_expirations failed")
            return []

    def get_chain(self, symbol: str, expiration: str):
        tkr = self._tkr(symbol)
        return fetch_with_retries(tkr.option_chain, expiration)

# --------------------------
# Alpha Vantage (price only)
# --------------------------
class AlphaVantagePrice(PriceProvider):
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key

    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        if not self.api_key:
            return None, "av.none"
        try:
            # Use GLOBAL_QUOTE to keep it simple and free‑tier friendly
            url = "https://www.alphavantage.co/query"
            params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": self.api_key}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            js = r.json()
            q = js.get("Global Quote", {})
            p = q.get("05. price") or q.get("05. Price")
            if p is None:
                return None, "av.noquote"
            return float(p), "alpha_vantage.global_quote"
        except Exception:
            logger.exception("AlphaVantage price failed")
            return None, "av.error"

# --------------------------
# Finnhub (options + price) — limited free tier
# --------------------------
class FinnhubProvider(PriceProvider, OptionsProvider):
    BASE = "https://finnhub.io/api/v1"
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
    def _enabled(self) -> bool:
        return bool(self.api_key)
    def _get(self, path: str, **params):
        params = {**params, "token": self.api_key}
        r = requests.get(f"{self.BASE}{path}", params=params, timeout=10)
        r.raise_for_status(); return r.json()
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        if not self._enabled():
            return None, "finnhub.none"
        try:
            js = self._get("/quote", symbol=symbol)
            c = js.get("c")  # current price
            if c:
                return float(c), "finnhub.quote"
        except Exception:
            logger.exception("Finnhub quote failed")
        return None, "finnhub.error"
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        if not self._enabled():
            return []
        try:
            js = self._get("/stock/options", symbol=symbol)
            exps = js.get("data", {}).get("expirationDates") or js.get("expirationDates") or []
            exps = sorted([e for e in exps if isinstance(e, str)])[:max_count]
            return exps
        except Exception:
            logger.exception("Finnhub get_expirations failed")
            return []
    def get_chain(self, symbol: str, expiration: str):
        if not self._enabled():
            raise RuntimeError("Finnhub disabled")
        try:
            js = self._get("/stock/options", symbol=symbol, date=expiration)
            # Build yfinance‑like object with .calls and .puts DataFrames
            contracts = js.get("data") or []
            if not contracts:
                raise RuntimeError("Empty chain from Finnhub")
            calls = []
            puts = []
            for c in contracts:
                row = {
                    "strike": c.get("strike"),
                    "bid": c.get("bid"),
                    "ask": c.get("ask"),
                    "lastPrice": c.get("lastPrice"),
                    "impliedVolatility": c.get("impliedVolatility"),
                }
                if c.get("type") == "call":
                    calls.append(row)
                elif c.get("type") == "put":
                    puts.append(row)
            class Chain:
                pass
            obj = Chain()
            obj.calls = pd.DataFrame(calls)
            obj.puts = pd.DataFrame(puts)
            return obj
        except Exception:
            logger.exception("Finnhub get_chain failed")
            raise

# --------------------------
# Tradier (options only) — sandbox good for testing
# --------------------------
class TradierOptions(OptionsProvider):
    def __init__(self, token: Optional[str], base: str):
        self.token = token
        self.base = base.rstrip("/")
    def _enabled(self) -> bool:
        return bool(self.token)
    def _headers(self):
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/json"}
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        if not self._enabled():
            return []
        try:
            url = f"{self.base}/v1/markets/options/expirations"
            r = requests.get(url, headers=self._headers(), params={"symbol": symbol, "includeAllRoots": "true"}, timeout=10)
            r.raise_for_status()
            js = r.json()
            exps = js.get("expirations", {}).get("date", [])
            if isinstance(exps, dict):
                exps = [exps.get("date")]
            exps = [e for e in exps if isinstance(e, str)]
            exps = sorted(exps)[:max_count]
            return exps
        except Exception:
            logger.exception("Tradier get_expirations failed")
            return []
    def get_chain(self, symbol: str, expiration: str):
        if not self._enabled():
            raise RuntimeError("Tradier disabled")
        try:
            url = f"{self.base}/v1/markets/options/chains"
            r = requests.get(url, headers=self._headers(), params={"symbol": symbol, "expiration": expiration}, timeout=10)
            r.raise_for_status()
            js = r.json().get("options", {}).get("option", [])
            calls, puts = [], []
            for c in js:
                row = {
                    "strike": c.get("strike"),
                    "bid": c.get("bid"),
                    "ask": c.get("ask"),
                    "lastPrice": c.get("last"),
                    "impliedVolatility": c.get("greeks", {}).get("mid_iv"),
                }
                (calls if c.get("option_type") == "call" else puts).append(row)
            class Chain:
                pass
            obj = Chain()
            obj.calls = pd.DataFrame(calls)
            obj.puts = pd.DataFrame(puts)
            return obj
        except Exception:
            logger.exception("Tradier get_chain failed")
            raise

# --------------------------
# Demo provider (no network)
# --------------------------
class DemoProvider(PriceProvider, OptionsProvider):
    def get_price(self, symbol: str) -> Tuple[Optional[float], str]:
        random.seed(symbol)
        return round(100 + random.random() * 50, 2), "demo.price"
    def get_expirations(self, symbol: str, max_count: int = 3) -> List[str]:
        return ["2025-09-20", "2025-10-18", "2025-11-15"][:max_count]
    def get_chain(self, symbol: str, expiration: str):
        price, _ = self.get_price(symbol)
        strikes = [round(price + d, 2) for d in (-5, 0, 5)]
        def mk_side(is_call: bool):
            rows = []
            for k in strikes:
                bid = max(0.1, round(random.random() * 2.0, 2))
                ask = bid + round(random.random(), 2)
                rows.append({"strike": k, "bid": bid, "ask": ask, "lastPrice": (bid+ask)/2, "impliedVolatility": round(0.2 + random.random()*0.2, 4)})
            return pd.DataFrame(rows)
        class Chain: pass
        obj = Chain(); obj.calls = mk_side(True); obj.puts = mk_side(False)
        return obj

# --------------------------
# Core helpers (provider‑agnostic)
# --------------------------

def ensure_numeric_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    for c in ("strike", "impliedVolatility", "bid", "ask", "lastPrice"):
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def nearest_strike_row(df: pd.DataFrame, price: float) -> Optional[pd.Series]:
    try:
        if df is None or df.empty:
            return None
        df = ensure_numeric_cols(df)
        idx = (df["strike"] - price).abs().sort_values().index
        return df.loc[idx[0]]
    except Exception:
        logger.exception("nearest_strike_row failed")
        return None


def summarize_chain_for_atm(chain, price: float) -> Dict[str, Any]:
    try:
        calls = ensure_numeric_cols(chain.calls.copy())
        puts  = ensure_numeric_cols(chain.puts.copy())
        call_atm = nearest_strike_row(calls, price)
        put_atm  = nearest_strike_row(puts, price)
        if call_atm is None or put_atm is None:
            return {"error": "Unable to locate ATM rows (calls/puts)."}
        def _mid(row):
            bid = float(row.get("bid", np.nan)); ask = float(row.get("ask", np.nan))
            if np.isfinite(bid) and np.isfinite(ask) and ask >= bid:
                return (bid + ask) / 2.0
            lp = row.get("lastPrice", np.nan)
            return float(lp) if np.isfinite(lp) else np.nan
        call_mid = _mid(call_atm); put_mid  = _mid(put_atm)
        straddle_mid = call_mid + put_mid if np.isfinite(call_mid) and np.isfinite(put_mid) else np.nan
        ivs = [float(call_atm.get("impliedVolatility", np.nan)), float(put_atm.get("impliedVolatility", np.nan))]
        ivs = [v for v in ivs if np.isfinite(v)]; atm_iv = float(np.mean(ivs)) if ivs else np.nan
        return {
            "atm_strike_call": float(call_atm["strike"]),
            "atm_strike_put": float(put_atm["strike"]),
            "call_mid": float(call_mid) if np.isfinite(call_mid) else None,
            "put_mid": float(put_mid) if np.isfinite(put_mid) else None,
            "straddle_mid": float(straddle_mid) if np.isfinite(straddle_mid) else None,
            "atm_iv": float(atm_iv) if np.isfinite(atm_iv) else None,
        }
    except Exception:
        logger.exception("summarize_chain_for_atm failed")
        return {"error": "Exception while summarizing ATM chain."}

# --------------------------
# Orchestration
# --------------------------
class DataService:
    def __init__(self, use_demo: bool = False):
        self.yahoo = YahooProvider()
        self.av = AlphaVantagePrice(ALPHA_VANTAGE_API_KEY)
        self.finn = FinnhubProvider(FINNHUB_API_KEY)
        self.tradier = TradierOptions(TRADIER_TOKEN, TRADIER_BASE)
        self.demo = DemoProvider() if use_demo else None

    def get_price(self, symbol: str) -> Tuple[Optional[float], str, bool]:
        # 1) Demo
        if self.demo:
            p, src = self.demo.get_price(symbol); return p, src, False
        # 2) Yahoo
        p, src = self.yahoo.get_price(symbol)
        if p is not None:
            set_cached_price(symbol, p); return p, src, False
        # 3) Alpha Vantage
        p, src = self.av.get_price(symbol)
        if p is not None:
            set_cached_price(symbol, p); return p, src, False
        # 4) Finnhub price fallback
        p, src = self.finn.get_price(symbol)
        if p is not None:
            set_cached_price(symbol, p); return p, src, False
        # 5) Cache
        cp = get_cached_price(symbol)
        if cp is not None:
            return cp, "cache", True
        return None, "none", False

    def get_expirations(self, symbol: str, max_count: int = 1) -> Tuple[List[str], str]:
        if self.demo:
            return self.demo.get_expirations(symbol, max_count), "demo"
        # Try Yahoo → Finnhub → Tradier
        exps = self.yahoo.get_expirations(symbol, max_count)
        if exps:
            return exps, "yahoo"
        exps = self.finn.get_expirations(symbol, max_count)
        if exps:
            return exps, "finnhub"
        exps = self.tradier.get_expirations(symbol, max_count)
        if exps:
            return exps, "tradier"
        return [], "none"

    def get_chain(self, symbol: str, expiration: str):
        if self.demo:
            return self.demo.get_chain(symbol, expiration), "demo"
        # Yahoo → Finnhub → Tradier
        try:
            return self.yahoo.get_chain(symbol, expiration), "yahoo"
        except Exception as e:
            if isinstance(e, YFRateLimitError):
                logger.error("Yahoo option_chain rate‑limited for %s @ %s", symbol, expiration)
            else:
                logger.exception("Yahoo option_chain failed for %s @ %s", symbol, expiration)
        try:
            return self.finn.get_chain(symbol, expiration), "finnhub"
        except Exception:
            logger.exception("Finnhub chain failed for %s @ %s", symbol, expiration)
        try:
            return self.tradier.get_chain(symbol, expiration), "tradier"
        except Exception:
            logger.exception("Tradier chain failed for %s @ %s", symbol, expiration)
        raise RuntimeError("No options provider available")

# --------------------------
# Public API for GUI
# --------------------------

def analyze_symbol(symbol: str, expirations_to_check: int = 1, use_demo: bool = False) -> Dict[str, Any]:
    try:
        sym = symbol.strip().upper()
        if not sym:
            return {"error": "Please enter a symbol."}
        svc = DataService(use_demo=use_demo)
        price, psrc, cached = svc.get_price(sym)
        if price is None:
            return {"error": f"Unable to retrieve current price (sources failed)."}
        exps, esrc = svc.get_expirations(sym, max_count=max(1, int(expirations_to_check or 1)))
        if not exps:
            return {"error": "No upcoming expirations found from any provider."}
        out: Dict[str, Any] = {
            "symbol": sym,
            "price": float(price),
            "price_source": psrc,
            "price_cached": bool(cached),
            "expirations_source": esrc,
            "expirations": [],
        }
        # Collect ATM IVs for term structure analysis
        atm_ivs = {}
        first_straddle = None
        
        for e in exps:
            try:
                chain, csrc = svc.get_chain(sym, e)
                summ = summarize_chain_for_atm(chain, float(price))
                summ["expiration"] = e
                summ["chain_source"] = csrc
                out["expirations"].append(summ)
                
                # Collect ATM IV for calendar spread analysis
                if "atm_iv" in summ and summ["atm_iv"] is not None:
                    atm_ivs[e] = summ["atm_iv"]
                    
                # Get first straddle price for expected move calculation
                if first_straddle is None and "straddle_mid" in summ and summ["straddle_mid"] is not None:
                    first_straddle = summ["straddle_mid"]
                    
            except Exception as ex:
                out["expirations"].append({"expiration": e, "error": f"Failed to fetch option chain: {type(ex).__name__}"})
        
        # Add calendar spread analysis if we have multiple expirations
        if len(atm_ivs) >= 2:
            try:
                # Get price history for volatility analysis
                price_history = None
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(sym)
                    price_history = ticker.history(period='3mo')  # 3 months of data
                except Exception as e:
                    logger.warning(f"Failed to get price history for {sym}: {e}")
                
                # Calculate calendar spread metrics
                calendar_metrics = calculate_calendar_spread_metrics(
                    atm_ivs=atm_ivs,
                    underlying_price=float(price),
                    straddle_price=first_straddle,
                    price_history=price_history
                )
                
                out["calendar_spread_analysis"] = calendar_metrics
                
            except Exception as e:
                logger.warning(f"Calendar spread analysis failed: {e}")
                out["calendar_spread_analysis"] = {"error": f"Analysis failed: {str(e)}"}
        else:
            out["calendar_spread_analysis"] = {"error": "Need at least 2 expirations for calendar spread analysis"}
            
        return out
    except Exception:
        logger.exception("analyze_symbol failed")
        return {"error": "Unexpected error in analyze_symbol. See log."}

# --------------------------
# GUI
# --------------------------

def build_layout() -> List[List[Any]]:
    sg.theme("SystemDefault")
    
    # Header section
    header = [sg.Text("Advanced Options Calculator & Calendar Spread Analyzer", font=("Helvetica", 16, "bold"))]
    
    # Input controls
    row1 = [
        sg.Text("Symbol:"), sg.Input(key="-SYMBOL-", size=(14, 1)),
        sg.Text("Expirations:"), sg.Spin(values=[1,2,3,4,5], initial_value=2, key="-NEXP-", size=(3,1)),
        sg.Checkbox("Debug panel", key="-DEBUG-"), sg.Checkbox("Demo mode", key="-DEMO-"),
        sg.Button("Submit", bind_return_key=True), sg.Button("Exit")
    ]
    
    # Main results - divided into two columns
    left_col = [
        [sg.Text("OPTIONS CHAIN ANALYSIS", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(key="-CHAIN-RESULTS-", size=(50, 20), disabled=True, autoscroll=True, 
                     font=("Courier New", 9), background_color="#f8f9fa")]
    ]
    
    right_col = [
        [sg.Text("CALENDAR SPREAD ANALYSIS", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(key="-CALENDAR-RESULTS-", size=(50, 20), disabled=True, autoscroll=True, 
                     font=("Courier New", 9), background_color="#f0f8ff")]
    ]
    
    # Results section with two columns
    results_section = [
        [sg.Column(left_col, vertical_alignment='top'), 
         sg.VerticalSeparator(), 
         sg.Column(right_col, vertical_alignment='top')]
    ]
    
    # Summary section for key metrics
    summary_frame = [
        [sg.Text("TRADING RECOMMENDATION", font=("Helvetica", 12, "bold"))],
        [sg.Multiline(key="-SUMMARY-", size=(104, 4), disabled=True, autoscroll=True, 
                     font=("Courier New", 10), background_color="#fff9e6")]
    ]
    
    # Debug section
    debug_frame = [[sg.Multiline(key="-DEBUGOUT-", size=(104, 10), disabled=True, autoscroll=True, 
                                 visible=False, font=("Courier New", 9))]]
    
    # Footer
    footer = [
        sg.Text("TIP: Use 2+ expirations for calendar spread analysis  |  ", text_color="gray"),
        sg.Text(f"Logs: {LOG_PATH}", text_color="gray")
    ]
    
    # Complete layout
    layout = [
        header,
        row1,
        [sg.Frame("Analysis Results", results_section, font=("Helvetica", 11))],
        [sg.Frame("Trading Recommendation", summary_frame, font=("Helvetica", 11))],
        [sg.Frame("Debug Output", debug_frame, key="-DEBUGFRAME-", visible=False, font=("Helvetica", 10))],
        footer
    ]
    
    return layout


def format_chain_results(res: Dict[str, Any]) -> str:
    """Format options chain analysis for the left panel."""
    if "error" in res:
        return f"ERROR: {res['error']}"

    lines: List[str] = []
    
    # Header with basic info
    lines.append(f"SYMBOL: {res['symbol']}")
    lines.append(f"Price: ${res['price']:.2f}")
    lines.append(f"Source: {res.get('price_source', 'unknown')}")
    lines.append(f"Cached: {'Yes' if res.get('price_cached') else 'No'}")
    lines.append("=" * 45)
    
    # Options chain data
    for i, item in enumerate(res.get("expirations", []), 1):
        exp = item.get("expiration", "?")
        if "error" in item:
            lines.append(f"Exp #{i}: {exp}")
            lines.append(f"ERROR: {item['error']}")
            lines.append("")
            continue

        # Extract data
        atm_iv = item.get("atm_iv")
        straddle = item.get("straddle_mid")
        call_mid = item.get("call_mid")
        put_mid = item.get("put_mid")
        strike_c = item.get("atm_strike_call")
        strike_p = item.get("atm_strike_put")
        src = item.get("chain_source", "?")

        # Format values
        iv_txt = f"{atm_iv:.4f}" if isinstance(atm_iv, (int, float)) else "n/a"
        cm_txt = f"${call_mid:.2f}" if isinstance(call_mid, (int, float)) else "n/a"
        pm_txt = f"${put_mid:.2f}" if isinstance(put_mid, (int, float)) else "n/a"
        sm_txt = f"${straddle:.2f}" if isinstance(straddle, (int, float)) else "n/a"

        lines.append(f"Exp #{i}: {exp}")
        lines.append(f"Source: {src}")
        lines.append(f"ATM: C@{strike_c} P@{strike_p}")
        lines.append(f"IV: {iv_txt}")
        lines.append(f"Call: {cm_txt} | Put: {pm_txt}")
        lines.append(f"Straddle: {sm_txt}")
        lines.append("")
    
    return "\n".join(lines)


def format_calendar_results(res: Dict[str, Any]) -> str:
    """Format calendar spread analysis for the right panel."""
    if "error" in res:
        return "Calendar spread analysis requires\nmultiple expirations.\n\nTry increasing 'Expirations' to 2+."
    
    calendar_data = res.get("calendar_spread_analysis", {})
    if "error" in calendar_data:
        return f"Calendar Analysis Error:\n{calendar_data['error']}"
    
    lines: List[str] = []
    
    lines.append("TERM STRUCTURE METRICS")
    lines.append("=" * 45)
    
    # Term Structure Analysis
    ts_slope = calendar_data.get("term_structure_slope")
    if ts_slope is not None:
        lines.append(f"Term Structure Slope: {ts_slope:.6f}")
        signal = "✓ BEARISH TS" if calendar_data.get("ts_slope_signal", False) else "✗ Not Bearish"
        lines.append(f"TS Signal: {signal}")
    else:
        lines.append("Term Structure Slope: n/a")
    
    lines.append("")
    
    # Volatility Analysis
    lines.append("VOLATILITY ANALYSIS")
    lines.append("-" * 45)
    iv30 = calendar_data.get("iv30")
    rv30 = calendar_data.get("rv30")
    iv_rv_ratio = calendar_data.get("iv_rv_ratio")
    
    if iv30 is not None:
        lines.append(f"30-Day IV: {iv30:.4f}")
    if rv30 is not None:
        lines.append(f"30-Day RV: {rv30:.4f}")
    if iv_rv_ratio is not None:
        lines.append(f"IV/RV Ratio: {iv_rv_ratio:.2f}")
        signal = "✓ HIGH IV/RV" if calendar_data.get("iv_rv_signal", False) else "✗ Low IV/RV"
        lines.append(f"IV/RV Signal: {signal}")
    else:
        lines.append("IV/RV Analysis: Insufficient data")
    
    lines.append("")
    
    # Volume & Expected Move
    lines.append("MARKET METRICS")
    lines.append("-" * 45)
    
    expected_move = calendar_data.get("expected_move_pct")
    if expected_move is not None:
        lines.append(f"Expected Move: {expected_move:.1f}%")
    
    avg_vol = calendar_data.get("avg_volume_30d")
    if avg_vol is not None:
        lines.append(f"Avg Volume (30d): {avg_vol:,.0f}")
        vol_signal = "✓ HIGH VOL" if calendar_data.get("volume_signal", False) else "✗ Low Vol"
        lines.append(f"Volume Signal: {vol_signal}")
    
    lines.append("")
    
    # Signals Summary
    signal_count = calendar_data.get("signal_count", 0)
    lines.append(f"SIGNALS: {signal_count}/3")
    signals = []
    if calendar_data.get("ts_slope_signal"): signals.append("TS")
    if calendar_data.get("iv_rv_signal"): signals.append("IV/RV")  
    if calendar_data.get("volume_signal"): signals.append("VOL")
    
    if signals:
        lines.append(f"Active: {', '.join(signals)}")
    else:
        lines.append("Active: None")
    
    return "\n".join(lines)


def format_summary_results(res: Dict[str, Any]) -> str:
    """Format trading recommendation summary."""
    if "error" in res:
        return f"Analysis Error: {res['error']}"
    
    calendar_data = res.get("calendar_spread_analysis", {})
    if "error" in calendar_data:
        return "⚠️  Need 2+ expirations for calendar spread analysis. Increase 'Expirations' setting."
    
    lines: List[str] = []
    
    # Get recommendation
    recommendation = calendar_data.get("recommendation", "Analysis incomplete")
    signal_count = calendar_data.get("signal_count", 0)
    
    # Add emoji based on recommendation
    if "BULLISH" in recommendation:
        emoji = "🟢"
    elif "NEUTRAL" in recommendation:
        emoji = "🟡"
    else:
        emoji = "🔴"
    
    lines.append(f"{emoji} {recommendation}")
    lines.append("")
    
    # Add key metrics in summary format
    symbol = res.get("symbol", "")
    price = res.get("price", 0)
    expected_move = calendar_data.get("expected_move_pct")
    
    summary_parts = [f"Symbol: {symbol}", f"Price: ${price:.2f}"]
    
    if expected_move:
        summary_parts.append(f"Expected Move: {expected_move:.1f}%")
        
    if signal_count is not None:
        summary_parts.append(f"Calendar Signals: {signal_count}/3")
    
    lines.append(" | ".join(summary_parts))
    
    return "\n".join(lines)


def run_gui():
    window = sg.Window("Advanced Options Calculator & Calendar Spread Analyzer", build_layout(), finalize=True)
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Exit"):
            break
        if event == "Submit":
            try:
                sym = values.get("-SYMBOL-", "").strip()
                n_exp = int(values.get("-NEXP-", 1) or 1)
                show_debug = bool(values.get("-DEBUG-", False))
                demo = bool(values.get("-DEMO-", False))
                
                # Update debug panel visibility
                window["-DEBUGFRAME-"].update(visible=show_debug)
                window["-DEBUGOUT-"].update(visible=show_debug)
                
                # Clear all result panels
                window["-CHAIN-RESULTS-"].update("")
                window["-CALENDAR-RESULTS-"].update("")
                window["-SUMMARY-"].update("")
                
                if show_debug:
                    window["-DEBUGOUT-"].update("Starting analysis...")
                
                # Run analysis
                res = analyze_symbol(sym, expirations_to_check=n_exp, use_demo=demo)
                
                # Update each panel with formatted results
                chain_text = format_chain_results(res)
                calendar_text = format_calendar_results(res)
                summary_text = format_summary_results(res)
                
                window["-CHAIN-RESULTS-"].update(chain_text)
                window["-CALENDAR-RESULTS-"].update(calendar_text)
                window["-SUMMARY-"].update(summary_text)
                
                if show_debug:
                    window["-DEBUGOUT-"].print("Raw result dict:", res)
                    
            except Exception:
                logger.exception("GUI Submit handler failed")
                error_msg = "Error: Unexpected failure in GUI Submit handler. See log."
                window["-CHAIN-RESULTS-"].update(error_msg)
                window["-CALENDAR-RESULTS-"].update("Analysis failed")
                window["-SUMMARY-"].update("🔴 Error occurred")
                if values.get("-DEBUG-", False):
                    window["-DEBUGOUT-"].print(traceback.format_exc())
    window.close()


if __name__ == "__main__":
    try:
        run_gui()
    except Exception:
        logger.exception("__main__ crashed")
