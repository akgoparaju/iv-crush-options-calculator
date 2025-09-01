# Earnings IV Crush Strategy — Complete Playbook

> **Purpose.** A concise, practitioner-ready reference for trading earnings by *selling pre‑event volatility* and exiting on the immediate post‑event “jump.” This summarizes the idea, the edge, structures, filters, timing, sizing, risks, and an execution checklist.

---

## 1) What this strategy is
**Thesis.** Leading into earnings, options markets typically **overprice** the potential move. Immediately after the announcement, implied volatility (**IV**) collapses (**IV crush**). We aim to monetize this by taking the short side of near-term IV while keeping tail risk acceptable.

**Two trade structures.**
- **Short ATM Straddle (front month).** Sell 1× call + 1× put at (or as close as practical to) the **ATM strike** in the expiry that **contains the earnings event**. High average return potential but a **fat left tail** (gap risk).
- **ATM Calendar Spread (front vs ~30D back).** Sell the front-month option that contains earnings; buy the same‑strike option ~**30 calendar days** later. Debit trade with smoother P&L; profits when **front IV drops more than back IV** and the stock’s move is modest.

**Timing (“jump” variant).** Open ~**15 minutes before the close** on the session **before** earnings; close ~**15 minutes after the open** the session **after** earnings. This harvests the immediate IV crush while minimizing exposure to intraday post‑earnings drift.

---

## 2) Why it works (the edge)
- **Systematic demand** for short‑dated options before earnings (hedgers + speculators) pushes **near‑term IV above fair**, creating **backwardation** (front > back) in the IV term structure.
- **Observed tendency**: realized move the next day is often **smaller than the move implied** by the ATM straddle priced before earnings.
- **Mechanics of profit**:
  - **IV crush**: Front‑month IV drops sharply right after the print; back‑month IV drops **less**, which benefits calendars.
  - **Under‑move vs implied**: If the stock moves **less than the implied move**, short‑gamma costs are limited and the structure profits.

---

## 3) Structures in practice
### A) Short ATM Straddle (front month)
- **Exposure**: Short vega, **very short gamma**, short theta into the event, long theta after (if held).
- **Profit drivers**: Large front‑month IV collapse; realized move < implied move.
- **Risks**: **Tail/gap risk** on big beats/misses; *the* left‑tail blow‑up structure. Slippage/assignment risk around the open.

### B) ATM Calendar Spread (front vs ~30D back)
- **Construction**: Same strike; sell front that contains earnings; buy the back ~**+30D**. Net debit.
- **Exposure**: Net **short gamma** (front gamma dominates), net vega structure where **front‑IV drop > back‑IV drop** is beneficial.
- **Profit drivers**: Modest price change + larger IV drop in front than back; time passes one day.
- **Risks**: If **back IV also collapses**, the calendar’s edge thins; large spot moves hurt due to short gamma.

**Which is “better”?** Straddles may show **higher peak returns** when correct, but **calendars** generally exhibit a **smoother equity curve** and **smaller catastrophic outliers**. Practitioner preference tends to favor calendars for portfolio stability.

---

## 4) When to trade (and when not to)
**Enter** only when *at least* the following **selection signals** align:
1) **Term‑structure slope**: Front‑month IV vs ~**45 DTE** IV is **negative** (backwardated). The **more negative**, the better.
2) **IV30 / RV30 ratio** ≥ threshold (e.g., **1.25**): IV rich vs recent realized volatility (RV) over the past ~30 sessions.
3) **Liquidity**: 30‑day average volume **high** (e.g., ≥ **1.5M** shares/day) — improves execution, reduces idiosyncratic prints.

**Avoid** when: No backwardation; thin liquidity; overlapping **binary catalysts** (FDA, litigation, macro surprises) the same day; or if the **implied move** is extremely large for the ticker (idiosyncratic risk).

**Timing discipline (Jump).**
- **Entry window**: ~T‑1 **15:45–16:00 local** (or last 15 minutes of normal session) to ensure you’re capturing the final pre‑earnings IV level.
- **Exit window**: ~T+0 **09:45–10:00 local** (or ~15 minutes after the opening print). Do not hold through the full day unless explicitly trading a drift view.

---

## 5) Sizing and portfolio construction
**Principle**: Treat this as a **short‑volatility strategy** with episodic tail risk. Use **fractional Kelly** or fixed‑fraction sizing.

- **Indicative Kelly fractions** (from empirical modeling):
  - Straddle **~6.5%**; Calendar **~60%** (full‑Kelly estimates are *too aggressive* to use directly).
- **Practical sizing** (fractional Kelly):
  - Straddle ≈ **2% of equity per trade** (~30% of full‑Kelly).
  - Calendar ≈ **6% of equity per trade** (~10% of full‑Kelly).
- **Portfolio caps**: Limit tickers per day and total % of equity exposed to a single earnings session.

**Expected path metrics** (illustrative, model‑based): Calendars sized at **~10% Kelly** can deliver strong growth with drawdowns that are more tolerable than straddles; straddles require very small sizing to survive left tails. Treat all figures as model‑based *expectations*, not guarantees.

---

## 6) Risk management — what can go wrong
- **Gap/tail risk**: Outlier earnings surprises or guidance shocks; single‑name headlines (M&A, probes).
- **IV dynamics**: If **back‑month IV collapses** as much as front, calendar edge diminishes.
- **Execution**: Wide spreads / opening‑auction noise; slippage; temporary halts.
- **Process drift**: Ignoring the timing rule, or relaxing filters during “FOMO” periods.
- **Correlation clusters**: Multiple names in the same sector reporting together → concentrated exposure.

**Controls.** Stick to **jump timing**, enforce **filters**, apply **sizing caps**, and maintain a **stop‑trading rule** after a severe drawdown until the equity curve recovers.

---

## 7) Step‑by‑step execution checklist
1) **Calendar review**: List upcoming earnings (by watchlist).
2) **Pre‑trade screen (day before)**: Pull ATM IV term; compute **front vs 45D slope**, **IV30/RV30**, and **AvgVol30D**.
3) **If signals align**: Decide **structure** (default: Calendar). Stage orders for the front/back legs (same strike; +~30D back).
4) **Enter** in the **final 15 minutes** before the pre‑earnings close. Record entry fills/debit and implied move.
5) **Exit** **~15 minutes after the open** post‑earnings. Use limits; don’t dither. Record P&L and realized move vs implied.
6) **Post‑trade log**: Update your journal (signals, fills, realized move, P&L, notes). Review weekly.

---

## 8) Parameter guide (starting points)
- **ATM anchor**: use the nearest strike to spot (or delta ~0.50).
- **Back‑month tenor** (calendar): **+30D** (±1 week is usually fine if inventory is sparse).
- **Signal thresholds**: Slope **< 0** and preferably “steep”; **IV30/RV30 ≥ 1.25**; **AvgVol30D ≥ 1.5M** shares/day. Tighten or relax with your own data.
- **Exit discipline**: Do not “hope” through the morning. Treat **10:00 local** as a hard latest exit unless explicitly trading for drift.

---

## 9) Glossary
- **IV crush**: Fast drop in implied volatility after a known catalyst (earnings).
- **Backwardation** (IV): Near‑term IV > longer‑dated IV — often indicates pre‑event overpricing.
- **Jump variant**: Entry before the print; exit shortly after the next open.
- **IV30 / RV30**: 30‑day implied vs realized volatility ratio.
- **Kelly fraction**: Optimal bet size in theory; use **fractional Kelly** in practice.

---

## 10) Disclaimers
This document is **for education only** and not investment advice. Single‑name earnings trades can incur **rapid, substantial losses**. Backtests/simulations are not guarantees of future results. Size small, diversify sensibly, and operate with clear, written rules.

— End of playbook —

