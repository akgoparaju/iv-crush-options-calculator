# Executive Summary
Your updated script now includes a calendar‑spread analysis path and produces a trading **recommendation** from three signals (term‑structure slope, IV30/RV30 ratio, and liquidity). The UI has been expanded into three panes (chain, calendar analysis, summary). Data access is provider‑agnostic (Yahoo → Alpha Vantage → Finnhub for price; Yahoo → Finnhub → Tradier for options) and supports a Demo mode.

**What’s solid today**
- Calendar spread **metrics** and recommendation: ✅
- **Term‑structure** interpolation (front → ~45D) and slope signal: ✅
- **IV30/RV30 ratio** using Yang–Zhang realized volatility (RV): ✅
- **Liquidity filter** via 30‑day average volume: ✅
- **Expected move** from ATM straddle/spot: ✅
- Robust logging, rate‑limit handling, provider fallbacks, and a clean UI: ✅

**What’s still missing to fully mirror the video’s strategy**
- **Earnings timing** logic (enter ~15m before the pre‑earnings close; exit ~15m after the post‑earnings open). ⏳
- **Trade construction & P&L**: compute **calendar debit/credit**, and simulate **post‑earnings P&L** under IV crush assumptions (front‑month drop > back‑month drop) and price moves. ⏳
- **Sizing** (fractional Kelly) and portfolio caps. ⏳
- **Backtest / Monte Carlo** on your own filtered events. ⏳

---

# Strategy Essence (from the video)
- **Edge:** Sell elevated earnings IV. Profit comes from **IV crush** and the stock’s move usually being **smaller than implied** going in.
- **Structures:**
  1) **Short ATM Straddle** (high mean, fat left tail; rare but large losses).  
  2) **ATM Calendar** (sell the front month that contains earnings; buy ~30D later at same strike). Lower variance, smoother P&L.
- **Timing (“jump” variant):** Enter ~**15 min before close** the day before earnings; exit ~**15 min after open** the day after.
- **Filters:** Favor trades when  
  (a) **Front vs ~45D term structure** is **negatively sloped** (near IV rich)  
  (b) **IV30/RV30** is **elevated** (IV overpriced vs realized)  
  (c) **Liquidity is high** (e.g., 30‑day average volume)
- **Sizing:** Use **fractional Kelly**; full‑Kelly is too aggressive.

---

# Cross‑Check Matrix — Updated Script vs Strategy
| Capability | Video Strategy | Your Script (current) |
|---|---|---|
| **Calendar spread** (ATM same strike, near vs ~30D back) | Required | **Partially implemented**: you compute calendar **signals** and recommendation; **no explicit debit/P&L** modeled yet. |
| **Term‑structure slope** (front → ~45D) | Required | **Implemented** via `build_term_structure()` + slope test (threshold ≈ **−0.00406/day**). |
| **IV30/RV30** | Required | **Implemented**: IV30 from ATM term; RV30 via **Yang–Zhang** estimator; ratio threshold **≥ 1.25**. |
| **Liquidity filter** (30‑day avg volume) | Recommended | **Implemented** with threshold **≥ 1.5M** shares/day. |
| **Expected move** (ATM straddle/spot) | Useful | **Implemented**; displayed in summary. |
| **Earnings timing (enter/exit windows)** | Required | **Missing** (no pre‑/post‑earnings scheduling). |
| **Trade P&L modeling** (calendar debit; post‑earnings exit with IV crush) | Recommended | **Missing**; no debit/Greek‑aware P&L yet. |
| **Sizing (fractional Kelly)** | Recommended | **Missing** (no account size/Kelly UI; no caps). |
| **Backtest & Monte Carlo** | Recommended | **Missing**. |
| **Provider resilience** | Helpful | **Implemented** (Yahoo/AV/Finnhub/Tradier + Demo). |

---

# What Your Script Does Well (Observed)
- **Provider abstraction & resilience**: `DataService` tries Yahoo, then Alpha Vantage and Finnhub for **price**, and Yahoo/Finnhub/Tradier for **options**, with throttling/retries and a 5‑minute **price cache**.
- **Term structure**: `build_term_structure(days, ivs)` uses `interp1d` to interpolate ATM IVs across expirations; slope is checked between the **front expiry** and a **45‑DTE** target (or second expiry if front >45D).
- **Volatility**: `yang_zhang_volatility(df)` for **RV30**; IV30 is taken from the term at ~30D; **IV30/RV30 ≥ 1.25** is a positive signal.
- **Liquidity**: 30‑day average **Volume ≥ 1.5M** triggers a positive signal.
- **Recommendation**: Count of signals (`ts_slope_signal`, `iv_over_rv_signal`, `volume_signal`) →  
  • **≥2** ⇒ “**BULLISH – Calendar spread opportunity**”  
  • **1** ⇒ “NEUTRAL”  
  • **0** ⇒ “BEARISH”.
- **UI**: Two analysis panels (chain & calendar) + a **summary** panel for recommendation, expected move, and signal count; Debug panel + log file.

> **Dependency note:** `scipy` is required for `interp1d`. Ensure it’s in your `requirements.txt`.

---

# Gaps and How to Close Them
## 1) Earnings‑Timing Logic (Entry/Exit)
**Goal:** Match the “jump” variant: **enter** ~15m before the close immediately **before** the earnings report; **exit** ~15m after the next **open**.

**Design:**
- Add `get_earnings_schedule(symbol)` with fallbacks (yfinance calendar/Finnhub earnings/Tradier corporate events). Normalize to: `{date, time: 'bmo|amc', confirmed: bool}`.
- Add `select_front_expiration(exps, earnings_dt)` ⇒ the **front** expiry must **contain** the event; `select_back_expiration(exps, target_dte≈30)` for calendar.
- Add `compute_trade_windows(earnings_dt, bmo_or_amc)` ⇒ precise timestamps for entry (T‑1 15:45 local) and exit (T+0 09:45 local) — make this configurable.
- Expose in UI: **“Timing: Jump (default) | Custom”**, and display computed windows with timezone.

## 2) Calendar Construction & P&L
**Goal:** Move from “signals” to a **concrete trade** with **debit** and **next‑day exit P&L** under IV crush.

**Design:**
- Add `build_calendar_trade(symbol, strike, front_exp, back_exp)` ⇒ fetch **ATM** call **or** put (consistent strike) both months; compute **mid prices** and **net debit**.
- Add `estimate_iv_crush(front_drop, back_drop)` ⇒ defaults e.g., **front −30% IV**, **back −10% IV**, configurable per ticker/liquidity.
- Add `simulate_post_earnings_pnl(calendar, underlying_move_pct, crush_params)` ⇒ reprice the calendar at **next‑day open** using updated spot and IVs (theta passes one calendar day). A quick first pass can use a **sticky‑strike IV** assumption with Black‑Scholes to revalue legs.
- Present a **P&L grid** (rows = price changes, cols = IV‑crush assumptions), and show:
  - **Breakeven band** at exit,
  - **Best‑/base‑/worst‑case** P&L,
  - **Expected move overlay**.

## 3) Sizing & Risk Controls
**Goal:** Enforce disciplined **fractional Kelly** with simple caps.

**Design:**
- UI fields: **Account Size ($)**, **Kelly Fraction (%)**, **Max %/Trade**, **Max $/Trade**, **Max Symbols / Day**.
- Compute **edge** proxy from signals (e.g., 2–3 signals ⇒ higher edge tier) or from historical backtest stats per tier; map to **recommended %** (e.g., 3/3 signals ⇒ 0.6×Kelly for calendar, capped; 2/3 ⇒ 0.3×Kelly; 1/3 ⇒ 0×/skip).
- Display **position size** and warn when **margin / concentration** constraints are exceeded.

## 4) Backtest & Monte Carlo (Phase 2)
**Goal:** Validate your filter tiers on **your tickers**.

**Design:**
- Add a **backtest module** that iterates past earnings dates, applies **your exact filters**, builds the calendar, and “exits” at next open using historical **spot** and a **parametrized IV crush** curve (front/back IV drop functions). Store event‑level P&L.
- Add a **Monte Carlo** sampler over per‑event returns to simulate equity paths and **drawdown distributions** for different Kelly fractions and portfolio caps.
- Report: CAGR, vol, skew/kurtosis, **max DD** and **time‑to‑recover**, win rate, and return by **signal tier**.

## 5) UX Enhancements
- **Provider selector** (Auto/Force Yahoo/Finnhub/Tradier) for debugging.
- **CSV Export** of per‑event inputs/outputs (filters, expected move, trade size, P&L).  
- **Status bar** showing which provider delivered **price/expiries/chain**.

---

# Concrete Implementation Checklist (Code Pointers)
- **Term Structure & Signals** (already in place)
  - `build_term_structure(days, ivs)` → interpolation.  
  - **Thresholds** currently: slope ≤ **−0.00406**, IV30/RV30 ≥ **1.25**, AvgVol30D ≥ **1.5M**.  
  - `calculate_calendar_spread_metrics(...)` → aggregates signals and sets `recommendation` & `signal_count`.

- **New Modules to Add**
  - `get_earnings_schedule(symbol)` → yfinance/Finnhub/Tradier fallback.
  - `select_front_expiration(exps, earnings_dt)`; `select_back_expiration(exps, target_dte=30)`.
  - `build_calendar_trade(symbol, strike, front_exp, back_exp)` → returns legs, **net debit**, Greeks snapshot.
  - `estimate_iv_crush(front_drop=0.30, back_drop=0.10)` → defaults by liquidity tier.
  - `simulate_post_earnings_pnl(calendar_trade, move_pct_grid, crush_grid)` → grid for summary pane.
  - `position_sizing(account_usd, kelly_frac, edge_tier, caps)` → shares/contracts to buy.

- **UI Wiring**
  - Add inputs for **Account Size**, **Kelly %**, **Max %/Trade**; add **Earnings Timing** selector.  
  - Add a **third pane** section showing **calendar debit**, **size**, and **P&L grid** (with expected‑move overlay line).

- **Data & Requirements**  
  Ensure `requirements.txt` includes:  
  `FreeSimpleGUI, yfinance, requests, pandas, numpy, scipy`

---

# Acceptance Tests (Smoke Tests)
1) **Demo mode**: Any symbol; verify that all three panes render; summary shows recommendation and expected move; no network calls.  
2) **Liquid names**: `AAPL`, `MSFT`, **Expirations=2+**; verify term‑structure slope, IV30/RV30 ratio, AvgVol30D, and a non‑empty recommendation.  
3) **Illiquid/No options**: Smallcap with thin options; expect a graceful per‑expiry error and a summary that explains missing data.  
4) **Rate‑limit**: Temporarily force Yahoo failure; confirm fallback to AV/Finnhub and readable summary.  
5) **(After adding trade & timing)**: Pick a past earnings date; verify entry window, constructed calendar debit, and next‑day exit P&L calculation across IV‑crush scenarios.

---

# Forward‑Looking Recommendations
- **Parameterize** thresholds per ticker universe; persist per‑ticker stats (win rate and return by tier) and adapt thresholds with more data.
- Add **outlier guards** (skip if expected move > Xσ, or if simultaneous major catalyst exists).
- Save per‑event **snapshots** (inputs, quotes, decision) for auditability.
- Integrate **email/Slack** notifications for upcoming eligible trades (once earnings scheduling is in place).

---

# Quick How‑To (for you and future contributors)
1) Use **Expirations ≥ 2** for calendar analysis.  
2) Start with **Demo mode** to validate UI; then switch to live with small requests (Expirations=1–2).  
3) Treat the current recommendation as **pre‑trade screening**. Only move to live sizing after the **Earnings Timing** and **P&L simulation** pieces are added.

— End of report —

