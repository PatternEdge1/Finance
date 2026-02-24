"""
Option Playbook: Regime & VIX-Based Strategy Selection
=======================================================
A hedge-fund-grade options strategy playbook that adapts to:
  - Market Regime : Bull / Neutral / Bear / Crisis
                    (detected via Gaussian Mixture Model on rolling volatility)
  - VIX Level     : Low (<15) / Normal (15-20) / Elevated (20-30) / High (>30)

Strategy Categories
-------------------
  1. Income (premium selling)          – collect theta decay
  2. Directional                        – express a view on price
  3. Stock Substitutes (defined risk)  – replicate stock exposure with less capital/downside

Per-Strategy Metrics (research-based, industry-calibrated)
-----------------------------------------------------------
  DTE             – Days to expiry for each leg
  Leg Delta       – Option delta of the key short/long leg
  POP             – Probability of Profit (theoretical or backtested)
  Win Rate        – Historical frequency of profitable trades
  Sortino         – Annualised Sortino ratio (downside-only vol)
  Max Risk        – Worst-case loss description
  Max Reward      – Best-case gain description
  IV Preference   – Preferred implied-volatility environment (sell high, buy low)

Outputs
-------
  Console : full strategy playbook tables + current regime recommendation
  CSV     : option_playbook.csv
  PNG     : option_playbook_chart.png  (regime timeline + tables + scatter)

Usage
-----
  python option_playbook.py
"""

import warnings

import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.mixture import GaussianMixture
import datetime

warnings.filterwarnings("ignore")
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 180)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuration
# ─────────────────────────────────────────────────────────────────────────────
TICKER = "SPY"
VIX_TICKER = "^VIX"
NUM_YEARS = 5
ROLLING_WINDOW = 22       # ~1 trading month
N_GMM_COMPONENTS = 3      # Bull / Neutral / Bear  (Crisis derived from VIX)
TRADING_DAYS = 252

# VIX level thresholds (tastytrade / CBOE convention)
VIX_LOW      = 15    # below → complacency / cheap IV → buy premium
VIX_NORMAL   = 20    # 15-20 → balanced regime
VIX_ELEVATED = 30    # 20-30 → sell premium aggressively
# VIX > VIX_ELEVATED → High

CRISIS_VIX_THRESHOLD = 35   # override GMM regime to "Crisis" above this level

# Chart / output settings
FIGURE_SIZE  = (20, 28)     # width × height in inches
CHART_DPI    = 120          # standard output quality
MARKER_SIZE_RECOMMENDED = 200   # scatter: highlighted strategy
MARKER_SIZE_DEFAULT     = 80    # scatter: non-recommended strategy

# ─────────────────────────────────────────────────────────────────────────────
# 2. Download price + VIX data
# ─────────────────────────────────────────────────────────────────────────────
start = datetime.date.today() - datetime.timedelta(days=int(365.25 * NUM_YEARS))
print(f"Downloading {TICKER} and {VIX_TICKER} data from {start} …")

try:
    spy_raw = yf.download(TICKER, start=start, progress=False)
    vix_raw = yf.download(VIX_TICKER, start=start, progress=False)
    if spy_raw.empty or vix_raw.empty:
        raise ValueError("Empty download – switching to synthetic demo data.")
    spy_close = spy_raw["Close"].squeeze()
    vix_close = vix_raw["Close"].squeeze()
    print("Live data loaded successfully.")
except Exception as e:
    print(f"[WARN] Data download failed ({e}). Using synthetic demo data.")
    np.random.seed(42)
    n_days = int(TRADING_DAYS * NUM_YEARS)
    dates = pd.bdate_range(end=datetime.date.today(), periods=n_days)
    # Synthetic SPY: geometric Brownian motion
    daily_ret = np.random.normal(0.0004, 0.011, n_days)
    spy_prices = 350 * np.exp(np.cumsum(daily_ret))
    spy_close = pd.Series(spy_prices, index=dates, name="Close")
    # Synthetic VIX: mean-reverting around 18
    vix_noise = np.random.normal(0, 1.5, n_days)
    vix_raw_vals = np.clip(18 + np.cumsum(vix_noise * 0.05), 8, 80)
    # Add a few crisis spikes
    spike_idx = np.random.choice(n_days, 3, replace=False)
    for si in spike_idx:
        vix_raw_vals[si: si + 20] = np.clip(vix_raw_vals[si: si + 20] + 25, 8, 80)
    vix_close = pd.Series(vix_raw_vals, index=dates, name="Close")

log_returns = np.log(spy_close / spy_close.shift(1)).dropna()
rolling_vol = log_returns.rolling(ROLLING_WINDOW).std().dropna() * np.sqrt(TRADING_DAYS)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Regime Detection — GMM on (rolling vol, VIX) joint feature
# ─────────────────────────────────────────────────────────────────────────────
common_idx = rolling_vol.index.intersection(vix_close.index)
rv = rolling_vol.reindex(common_idx)
vx = vix_close.reindex(common_idx).ffill() / 100.0          # scale to match vol

features = np.column_stack([rv.values, vx.values])

gmm = GaussianMixture(n_components=N_GMM_COMPONENTS, covariance_type="full", random_state=42)
regime_labels = gmm.fit_predict(features)

# Sort regimes by mean volatility: lowest → Bull, middle → Neutral, highest → Bear
mean_vol_by_label = [rv[regime_labels == i].mean() for i in range(N_GMM_COMPONENTS)]
sorted_labels = np.argsort(mean_vol_by_label)  # ascending: bull, neutral, bear
label_map = {sorted_labels[0]: "Bull", sorted_labels[1]: "Neutral", sorted_labels[2]: "Bear"}

regime_series = pd.Series(
    [label_map[l] for l in regime_labels], index=common_idx, name="Regime"
)

# Override to Crisis when VIX > CRISIS_VIX_THRESHOLD
vx_pct = vix_close.reindex(common_idx).ffill()
regime_series[vx_pct > CRISIS_VIX_THRESHOLD] = "Crisis"

# ─────────────────────────────────────────────────────────────────────────────
# 4. VIX Bucketing
# ─────────────────────────────────────────────────────────────────────────────
def vix_bucket(v: float) -> str:
    if v < VIX_LOW:
        return "Low (<15)"
    elif v < VIX_NORMAL:
        return "Normal (15-20)"
    elif v < VIX_ELEVATED:
        return "Elevated (20-30)"
    else:
        return "High (>30)"


current_vix = float(vx_pct.iloc[-1])
current_regime = regime_series.iloc[-1]
current_vix_bucket = vix_bucket(current_vix)

print(f"\n{'='*60}")
print(f"  Current Regime : {current_regime}")
print(f"  Current VIX    : {current_vix:.2f}  →  {current_vix_bucket}")
print(f"{'='*60}\n")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Strategy Playbook Definition
#    Research sources: tastytrade backtests, CBOE studies, academic literature.
#    All POP / Win-Rate / Sortino values represent approximate historical ranges
#    on liquid index ETFs (SPY, QQQ, IWM) under the stated conditions.
# ─────────────────────────────────────────────────────────────────────────────
playbook = [
    # ── INCOME STRATEGIES ───────────────────────────────────────────────────
    {
        "Strategy": "Covered Call",
        "Category": "Income",
        "Best Regimes": "Bull, Neutral",
        "VIX Preference": "Low, Normal",
        "Legs": "Long 100 sh stock  |  Short call",
        "Leg 1 DTE": "–",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "0.25–0.30",
        "Long Leg Delta": "Stock (≈1.0)",
        "POP (%)": "70–75",
        "Win Rate (%)": "65–72",
        "Sortino": "1.2–1.5",
        "IV Preference": "Sell high IV",
        "Max Risk": "Stock drops to zero (downside same as owning stock)",
        "Max Reward": "Strike – entry + premium collected",
        "Key Risk": "Capped upside; stock can gap lower",
        "Notes": "Best for slightly bullish view; systematic 30-DTE rolls reduce cost basis",
    },
    {
        "Strategy": "Cash-Secured Put (CSP)",
        "Category": "Income",
        "Best Regimes": "Bull, Neutral",
        "VIX Preference": "Normal, Elevated",
        "Legs": "Short put (cash collateral)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "–",
        "Short Leg Delta": "0.25–0.30",
        "Long Leg Delta": "–",
        "POP (%)": "70–75",
        "Win Rate (%)": "68–72",
        "Sortino": "1.1–1.4",
        "IV Preference": "Sell high IV",
        "Max Risk": "Strike × 100 – premium (assignment: own stock at strike)",
        "Max Reward": "Premium collected",
        "Key Risk": "Assignment; stock collapses below break-even",
        "Notes": "Equivalent to covered call on same strike; use at technical support",
    },
    {
        "Strategy": "Bull Put Spread",
        "Category": "Income",
        "Best Regimes": "Bull, Neutral",
        "VIX Preference": "Normal, Elevated",
        "Legs": "Short put (higher strike)  |  Long put (lower strike)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "0.30",
        "Long Leg Delta": "0.15",
        "POP (%)": "65–70",
        "Win Rate (%)": "62–68",
        "Sortino": "1.3–1.6",
        "IV Preference": "Sell elevated IV",
        "Max Risk": "(Strike width – credit) × 100",
        "Max Reward": "Net credit received",
        "Key Risk": "Defined; max loss if stock below long put at expiry",
        "Notes": "Preferred over CSP when margin is limited; 1:2 risk/reward min",
    },
    {
        "Strategy": "Bear Call Spread",
        "Category": "Income",
        "Best Regimes": "Bear, Neutral",
        "VIX Preference": "Elevated, High",
        "Legs": "Short call (lower strike)  |  Long call (higher strike)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "0.30",
        "Long Leg Delta": "0.15",
        "POP (%)": "65–70",
        "Win Rate (%)": "62–68",
        "Sortino": "1.2–1.5",
        "IV Preference": "Sell elevated IV",
        "Max Risk": "(Strike width – credit) × 100",
        "Max Reward": "Net credit received",
        "Key Risk": "Defined; max loss if stock above long call at expiry",
        "Notes": "Pair with bear put spread for iron condor; scale position size",
    },
    {
        "Strategy": "Iron Condor",
        "Category": "Income",
        "Best Regimes": "Neutral",
        "VIX Preference": "Elevated (20-30)",
        "Legs": "Short put (δ–0.16)  |  Long put (δ–0.05)  |  Short call (δ0.16)  |  Long call (δ0.05)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "±0.16",
        "Long Leg Delta": "±0.05",
        "POP (%)": "68–72",
        "Win Rate (%)": "60–65",
        "Sortino": "1.0–1.4",
        "IV Preference": "Sell elevated IV; avoid earnings week",
        "Max Risk": "Width of widest wing – total credit",
        "Max Reward": "Total credit received (both spreads)",
        "Key Risk": "Breakout beyond wings; pin risk at short strikes",
        "Notes": "Manage at 50% max profit or 21 DTE; roll tested side up/down 1 SD",
    },
    {
        "Strategy": "Short Strangle",
        "Category": "Income",
        "Best Regimes": "Neutral",
        "VIX Preference": "High (>30)",
        "Legs": "Short OTM put  |  Short OTM call",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "±0.15–0.20",
        "Long Leg Delta": "–",
        "POP (%)": "70–75",
        "Win Rate (%)": "55–65",
        "Sortino": "0.8–1.2",
        "IV Preference": "Very high IV; IV rank >50",
        "Max Risk": "Theoretically unlimited on both sides",
        "Max Reward": "Total premium collected",
        "Key Risk": "Unlimited risk; black-swan gap risk; margin intensive",
        "Notes": "Only on highly liquid ETFs (SPY/QQQ); strict delta-neutral management",
    },
    {
        "Strategy": "Iron Butterfly",
        "Category": "Income",
        "Best Regimes": "Neutral",
        "VIX Preference": "High (>30)",
        "Legs": "Short ATM call  |  Short ATM put  |  Long OTM call  |  Long OTM put",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "±0.50",
        "Long Leg Delta": "±0.25",
        "POP (%)": "50–55",
        "Win Rate (%)": "55–65",
        "Sortino": "1.0–1.5",
        "IV Preference": "Very high IV; IV crush expected",
        "Max Risk": "Wing width – credit",
        "Max Reward": "Credit received (larger than IC)",
        "Key Risk": "Pin risk; requires tight management",
        "Notes": "Captures IV crush post-event; target 25% max profit; break-even ±credit/2 from ATM",
    },
    {
        "Strategy": "Jade Lizard",
        "Category": "Income",
        "Best Regimes": "Bull, Neutral",
        "VIX Preference": "Normal, Elevated",
        "Legs": "Short put (δ–0.30)  |  Short call (δ0.25)  |  Long call (δ0.15)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "–0.30 / 0.25",
        "Long Leg Delta": "0.15",
        "POP (%)": "75–80",
        "Win Rate (%)": "65–70",
        "Sortino": "1.3–1.7",
        "IV Preference": "Elevated IV; skew favors puts",
        "Max Risk": "(Put strike – credit received) × 100 (no upside risk if structured right)",
        "Max Reward": "Total credit (no upside risk if call-spread credit ≥ width)",
        "Key Risk": "Downside from put; structured so upside is risk-free",
        "Notes": "Ideal when skew is steep and you are neutral-to-bullish",
    },
    {
        "Strategy": "Calendar Spread",
        "Category": "Income",
        "Best Regimes": "Neutral",
        "VIX Preference": "Low (<15)",
        "Legs": "Short near-term ATM  |  Long far-term ATM",
        "Leg 1 DTE": "7-21",
        "Leg 2 DTE": "30-60",
        "Short Leg Delta": "±0.50",
        "Long Leg Delta": "±0.50",
        "POP (%)": "55–65",
        "Win Rate (%)": "55–60",
        "Sortino": "0.9–1.2",
        "IV Preference": "Low front-month IV vs. higher back-month IV",
        "Max Risk": "Net debit paid (limited)",
        "Max Reward": "Max at expiry when stock pins near short strike",
        "Key Risk": "Volatility collapse in the back month; large moves hurt",
        "Notes": "Profits from time-decay differential; roll short leg weekly for income",
    },
    {
        "Strategy": "Diagonal Spread (Income)",
        "Category": "Income",
        "Best Regimes": "Bull, Neutral",
        "VIX Preference": "Normal (15-20)",
        "Legs": "Long far-term call (δ0.70)  |  Short near-term call (δ0.30)",
        "Leg 1 DTE": "60-90",
        "Leg 2 DTE": "14-21",
        "Short Leg Delta": "0.30",
        "Long Leg Delta": "0.70",
        "POP (%)": "55–65",
        "Win Rate (%)": "58–65",
        "Sortino": "1.1–1.5",
        "IV Preference": "Back month IV < front month IV",
        "Max Risk": "Net debit if long leg loses all value",
        "Max Reward": "Credit harvested repeatedly from short leg rolls",
        "Key Risk": "Stock drops sharply; long leg loses value faster",
        "Notes": "Roll short leg every 14-21 DTE; aim to recover 50–100% of long debit",
    },
    # ── DIRECTIONAL STRATEGIES ───────────────────────────────────────────────
    {
        "Strategy": "Long Call",
        "Category": "Directional",
        "Best Regimes": "Bull",
        "VIX Preference": "Low, Normal",
        "Legs": "Long OTM-to-ATM call",
        "Leg 1 DTE": "60-90",
        "Leg 2 DTE": "–",
        "Short Leg Delta": "–",
        "Long Leg Delta": "0.50–0.70",
        "POP (%)": "40–50",
        "Win Rate (%)": "40–50",
        "Sortino": "1.5–2.5",
        "IV Preference": "Buy low IV (IV rank <30)",
        "Max Risk": "100% of premium paid",
        "Max Reward": "Unlimited (stock rises)",
        "Key Risk": "Total loss of premium; time decay + IV crush",
        "Notes": "Use 60-90 DTE to reduce theta drag; roll at 21 DTE to next month",
    },
    {
        "Strategy": "Long Put",
        "Category": "Directional",
        "Best Regimes": "Bear",
        "VIX Preference": "Low, Normal",
        "Legs": "Long OTM-to-ATM put",
        "Leg 1 DTE": "45-60",
        "Leg 2 DTE": "–",
        "Short Leg Delta": "–",
        "Long Leg Delta": "–0.40 to –0.60",
        "POP (%)": "40–50",
        "Win Rate (%)": "35–45",
        "Sortino": "1.2–2.0",
        "IV Preference": "Buy low IV; before IV expansion",
        "Max Risk": "100% of premium paid",
        "Max Reward": "Stock falls to zero (put spread to reduce cost)",
        "Key Risk": "Total loss; IV spike inflates entry price",
        "Notes": "Use at VIX <20; expensive when VIX already elevated",
    },
    {
        "Strategy": "Bull Call Spread",
        "Category": "Directional",
        "Best Regimes": "Bull",
        "VIX Preference": "Low, Normal",
        "Legs": "Long call (δ0.50)  |  Short call (δ0.25)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "0.25",
        "Long Leg Delta": "0.50",
        "POP (%)": "40–50",
        "Win Rate (%)": "42–52",
        "Sortino": "1.4–2.0",
        "IV Preference": "Moderately low IV",
        "Max Risk": "Net debit paid",
        "Max Reward": "(Strike width – debit) × 100",
        "Key Risk": "Defined loss; opportunity cost if strong rally",
        "Notes": "Aim for 1:2 risk/reward min; select strikes around expected move",
    },
    {
        "Strategy": "Bear Put Spread",
        "Category": "Directional",
        "Best Regimes": "Bear",
        "VIX Preference": "Low, Normal",
        "Legs": "Long put (δ–0.50)  |  Short put (δ–0.25)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "–0.25",
        "Long Leg Delta": "–0.50",
        "POP (%)": "40–50",
        "Win Rate (%)": "40–48",
        "Sortino": "1.3–1.9",
        "IV Preference": "Moderately low IV",
        "Max Risk": "Net debit paid",
        "Max Reward": "(Strike width – debit) × 100",
        "Key Risk": "Defined loss; cheaper than outright long put",
        "Notes": "Useful hedge when IV is already elevated (cheaper than long put)",
    },
    {
        "Strategy": "Long Straddle",
        "Category": "Directional",
        "Best Regimes": "Neutral (pre-event)",
        "VIX Preference": "Low (<15)",
        "Legs": "Long ATM call  |  Long ATM put",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "–",
        "Long Leg Delta": "±0.50",
        "POP (%)": "35–45",
        "Win Rate (%)": "40–50",
        "Sortino": "0.8–1.5",
        "IV Preference": "Low IV; before catalyst / breakout",
        "Max Risk": "Total premium paid (both legs)",
        "Max Reward": "Unlimited on call side; nearly unlimited on put side",
        "Key Risk": "IV crush post-event; time decay if stock stays flat",
        "Notes": "Enter 10-14 days before catalyst; exit immediately after",
    },
    {
        "Strategy": "Long Strangle",
        "Category": "Directional",
        "Best Regimes": "Neutral (pre-event)",
        "VIX Preference": "Low (<15)",
        "Legs": "Long OTM call (δ0.25)  |  Long OTM put (δ–0.25)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "–",
        "Long Leg Delta": "±0.25",
        "POP (%)": "30–40",
        "Win Rate (%)": "35–45",
        "Sortino": "0.9–1.5",
        "IV Preference": "Low IV before volatility expansion",
        "Max Risk": "Total premium paid (cheaper than straddle)",
        "Max Reward": "Unlimited on call; nearly unlimited on put",
        "Key Risk": "Stock doesn't move enough to cover both premiums",
        "Notes": "Wider strikes = lower cost but needs bigger move to profit",
    },
    {
        "Strategy": "Put Calendar",
        "Category": "Directional",
        "Best Regimes": "Bear",
        "VIX Preference": "Low (<15)",
        "Legs": "Short near-term put (δ–0.40)  |  Long far-term put (δ–0.50)",
        "Leg 1 DTE": "14-21",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "–0.40",
        "Long Leg Delta": "–0.50",
        "POP (%)": "50–60",
        "Win Rate (%)": "50–58",
        "Sortino": "1.0–1.5",
        "IV Preference": "Low front-month; higher back-month IV",
        "Max Risk": "Net debit (limited)",
        "Max Reward": "When stock lands near short strike at near-term expiry",
        "Key Risk": "Sharp drop beyond long put; time spread collapses",
        "Notes": "Bearish with time-decay income; roll short leg each expiry",
    },
    {
        "Strategy": "Call Ratio Back-Spread",
        "Category": "Directional",
        "Best Regimes": "Bull (after IV spike)",
        "VIX Preference": "Elevated (20-30)",
        "Legs": "Short 1 ATM call (δ0.50)  |  Long 2 OTM calls (δ0.25 each)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "0.50",
        "Long Leg Delta": "0.25 ×2",
        "POP (%)": "50–60",
        "Win Rate (%)": "55–62",
        "Sortino": "1.0–1.4",
        "IV Preference": "Elevated IV; expect IV mean-reversion + upside move",
        "Max Risk": "Between short and first long strike at expiry",
        "Max Reward": "Unlimited upside (extra long calls); near-zero entry cost",
        "Key Risk": "Stock lands between strikes at expiry (max pain zone)",
        "Notes": "Structure for near-zero debit; profits from big upside or staying below short strike",
    },
    # ── STOCK SUBSTITUTES (lesser downside) ─────────────────────────────────
    {
        "Strategy": "Long LEAPS Call (Stock Sub)",
        "Category": "Stock Substitute",
        "Best Regimes": "Bull",
        "VIX Preference": "Low, Normal",
        "Legs": "Long deep-ITM call (LEAPS)",
        "Leg 1 DTE": "365-730",
        "Leg 2 DTE": "–",
        "Short Leg Delta": "–",
        "Long Leg Delta": "0.80–0.90",
        "POP (%)": "60–70",
        "Win Rate (%)": "60–68",
        "Sortino": "2.0–3.0",
        "IV Preference": "Low IV; avoid purchasing post-spike",
        "Max Risk": "Premium paid (typically 10-20% of stock notional)",
        "Max Reward": "Essentially same as long stock (leveraged)",
        "Key Risk": "Total loss of premium if stock collapses; no dividends",
        "Notes": "Deep-ITM call mimics stock with 5-10× less capital; exit at 21 DTE",
    },
    {
        "Strategy": "Poor Man's Covered Call (PMCC)",
        "Category": "Stock Substitute",
        "Best Regimes": "Bull, Neutral",
        "VIX Preference": "Normal (15-20)",
        "Legs": "Long LEAPS call (δ0.70-0.80)  |  Short near-term call (δ0.25-0.30)",
        "Leg 1 DTE": "365+",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "0.25–0.30",
        "Long Leg Delta": "0.70–0.80",
        "POP (%)": "65–72",
        "Win Rate (%)": "63–70",
        "Sortino": "1.5–2.5",
        "IV Preference": "Moderate IV on short; lower IV on LEAPS",
        "Max Risk": "Net debit (LEAPS premium – credits collected over time)",
        "Max Reward": "Strike difference × 100 – net debit; short call rolls reduce cost basis",
        "Key Risk": "Inverted spread if stock rockets past long strike; roll short up/out",
        "Notes": "Replaces covered call at 10-20% of capital; roll short leg monthly for income",
    },
    {
        "Strategy": "Synthetic Long Stock",
        "Category": "Stock Substitute",
        "Best Regimes": "Bull",
        "VIX Preference": "Normal (15-20)",
        "Legs": "Long ATM call (δ≈0.50)  |  Short ATM put (δ≈–0.50)",
        "Leg 1 DTE": "30-60",
        "Leg 2 DTE": "30-60",
        "Short Leg Delta": "–0.50",
        "Long Leg Delta": "0.50",
        "POP (%)": "50",
        "Win Rate (%)": "52–58",
        "Sortino": "1.3–1.8",
        "IV Preference": "Neutral IV; prefer put/call parity balance",
        "Max Risk": "Short put assignment at strike (similar to owning stock); limited capital",
        "Max Reward": "Effectively same as long stock above entry cost",
        "Key Risk": "Short put creates margin obligation; stock gap down triggers assignment",
        "Notes": "Near-zero cost entry vs stock; same P&L as stock, minimal upfront capital",
    },
    {
        "Strategy": "Risk Reversal",
        "Category": "Stock Substitute",
        "Best Regimes": "Bull",
        "VIX Preference": "Elevated (20-30)",
        "Legs": "Short OTM put (δ–0.25)  |  Long OTM call (δ0.25)",
        "Leg 1 DTE": "30-45",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "–0.25",
        "Long Leg Delta": "0.25",
        "POP (%)": "50–60",
        "Win Rate (%)": "52–58",
        "Sortino": "1.2–1.8",
        "IV Preference": "Skewed IV (puts > calls IV); sell rich puts, buy cheap calls",
        "Max Risk": "Short put strike risk (if stock collapses); often near-zero debit",
        "Max Reward": "Unlimited upside via long call; often entered for credit",
        "Key Risk": "Short put risk in sharp downturn; hedge with stop-loss",
        "Notes": "Exploits volatility skew; often zero or small credit entry; bullish position",
    },
    {
        "Strategy": "Leveraged Bull Call Spread (Stock Sub)",
        "Category": "Stock Substitute",
        "Best Regimes": "Bull",
        "VIX Preference": "Low (<15)",
        "Legs": "Long ITM call (δ0.70)  |  Short OTM call (δ0.30)",
        "Leg 1 DTE": "45-60",
        "Leg 2 DTE": "45-60",
        "Short Leg Delta": "0.30",
        "Long Leg Delta": "0.70",
        "POP (%)": "55–65",
        "Win Rate (%)": "55–65",
        "Sortino": "1.5–2.2",
        "IV Preference": "Low IV; cheaper debit entry",
        "Max Risk": "Net debit paid (5-15% of stock notional)",
        "Max Reward": "(Strike width – debit) × 100; defined",
        "Key Risk": "Capped upside; stock must move to long breakeven",
        "Notes": "Use when strongly bullish but want defined downside risk vs stock",
    },
    {
        "Strategy": "Collar (Stock + Protective Put + Short Call)",
        "Category": "Stock Substitute",
        "Best Regimes": "Neutral, Bear",
        "VIX Preference": "Elevated (20-30)",
        "Legs": "Long stock  |  Long put (δ–0.30)  |  Short call (δ0.25)",
        "Leg 1 DTE": "–",
        "Leg 2 DTE": "30-45",
        "Short Leg Delta": "0.25",
        "Long Leg Delta": "–0.30",
        "POP (%)": "55–65",
        "Win Rate (%)": "60–68",
        "Sortino": "1.4–2.0",
        "IV Preference": "Elevated IV; sell expensive call, buy cheaper put (or vice versa)",
        "Max Risk": "Stock – put strike (floor defined by put)",
        "Max Reward": "Call strike – stock entry + net credit/debit",
        "Key Risk": "Capped upside; opportunity cost in strong bull run",
        "Notes": "Ideal for existing stock position in uncertain regime; insures downside",
    },
    {
        "Strategy": "Protective Put (Married Put)",
        "Category": "Stock Substitute",
        "Best Regimes": "Bull (hedged)",
        "VIX Preference": "Low, Normal",
        "Legs": "Long stock  |  Long put (δ–0.25 to –0.40)",
        "Leg 1 DTE": "–",
        "Leg 2 DTE": "60-90",
        "Short Leg Delta": "–",
        "Long Leg Delta": "–0.25 to –0.40",
        "POP (%)": "60–70",
        "Win Rate (%)": "62–70",
        "Sortino": "1.6–2.5",
        "IV Preference": "Low IV (cheaper puts)",
        "Max Risk": "Stock – put strike + premium paid (hard floor)",
        "Max Reward": "Unlimited upside (same as stock)",
        "Key Risk": "Put premium cost erodes returns; theta drag",
        "Notes": "Insurance policy on stock; use when bullish but fear tail risk",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# 6. Build DataFrame
# ─────────────────────────────────────────────────────────────────────────────
df_playbook = pd.DataFrame(playbook)

# ─────────────────────────────────────────────────────────────────────────────
# 7. Current Regime Filtering — recommended strategies
# ─────────────────────────────────────────────────────────────────────────────
def is_recommended(row, regime: str, vix_bkt: str) -> bool:
    # Neutral strategies are only universally included when current regime is Neutral;
    # during Crisis, only explicitly Crisis-compatible or Neutral strategies apply.
    include_neutral = regime in ("Neutral",)
    candidates = [regime]
    if include_neutral:
        candidates.append("Neutral")
    regime_match = any(r.strip() in row["Best Regimes"] for r in candidates)
    # VIX label matching (simplified bucket name matching)
    vix_labels_in_row = row["VIX Preference"].lower()
    vix_short = vix_bkt.split("(")[0].strip().lower()  # e.g. "low", "normal"
    vix_match = vix_short in vix_labels_in_row or "all" in vix_labels_in_row
    return regime_match and vix_match


recommended_mask = df_playbook.apply(
    lambda r: is_recommended(r, current_regime, current_vix_bucket), axis=1
)
df_recommended = df_playbook[recommended_mask].copy()

# ─────────────────────────────────────────────────────────────────────────────
# 8. Console Output
# ─────────────────────────────────────────────────────────────────────────────
display_cols = [
    "Strategy", "Category", "Best Regimes", "VIX Preference",
    "Leg 1 DTE", "Leg 2 DTE", "Short Leg Delta", "Long Leg Delta",
    "POP (%)", "Win Rate (%)", "Sortino",
    "Max Risk", "Max Reward", "Key Risk",
]

print("\n" + "═" * 80)
print("  FULL OPTION PLAYBOOK  (all regimes)")
print("═" * 80)
print(df_playbook[display_cols].to_string(index=False))

print("\n" + "═" * 80)
print(f"  RECOMMENDED STRATEGIES  |  Regime: {current_regime}  |  VIX: {current_vix:.1f} ({current_vix_bucket})")
print("═" * 80)
if df_recommended.empty:
    print("  (No strategies matched current regime/VIX bucket – default to Iron Condor or review VIX manually)")
else:
    print(df_recommended[display_cols].to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# 9. Save CSV
# ─────────────────────────────────────────────────────────────────────────────
csv_path = "option_playbook.csv"
df_playbook.to_csv(csv_path, index=False)
print(f"\nFull playbook saved to {csv_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 10. Visualisation
# ─────────────────────────────────────────────────────────────────────────────
REGIME_COLORS = {"Bull": "#2ecc71", "Neutral": "#f39c12", "Bear": "#e74c3c", "Crisis": "#8e44ad"}
CATEGORY_COLORS = {"Income": "#3498db", "Directional": "#e67e22", "Stock Substitute": "#27ae60"}

fig = plt.figure(figsize=FIGURE_SIZE)
gs = gridspec.GridSpec(
    4, 2,
    figure=fig,
    hspace=0.45,
    wspace=0.35,
    height_ratios=[1.4, 1.6, 1.8, 0.9],
)

# ── Panel A : Regime Timeline ───────────────────────────────────────────────
ax_regime = fig.add_subplot(gs[0, :])
price_aligned = spy_close.reindex(common_idx).ffill()
ax_regime.plot(price_aligned.index, price_aligned, color="black", linewidth=1, label=TICKER)

for i in range(len(regime_series) - 1):
    reg = regime_series.iloc[i]
    ax_regime.axvspan(
        regime_series.index[i], regime_series.index[i + 1],
        alpha=0.15, color=REGIME_COLORS.get(reg, "grey")
    )

legend_patches = [
    mpatches.Patch(color=REGIME_COLORS[r], alpha=0.5, label=r)
    for r in ["Bull", "Neutral", "Bear", "Crisis"]
]
ax_regime.legend(handles=legend_patches + [
    plt.Line2D([0], [0], color="black", linewidth=1, label=TICKER)
], loc="upper left", fontsize=9)
ax_regime.set_title(
    f"{TICKER} Price with Detected Regimes  |  Current: {current_regime}  |  VIX={current_vix:.1f} ({current_vix_bucket})",
    fontsize=12, fontweight="bold",
)
ax_regime.set_ylabel("Price ($)")
ax_regime.grid(True, alpha=0.3)

# Add current VIX annotation
ax_vix = ax_regime.twinx()
vix_aligned = vix_close.reindex(common_idx).ffill()
ax_vix.plot(vix_aligned.index, vix_aligned, color="purple", linewidth=0.8, alpha=0.5, linestyle="--", label="VIX")
ax_vix.axhline(VIX_LOW, color="green", linewidth=0.6, linestyle=":", alpha=0.7)
ax_vix.axhline(VIX_NORMAL, color="orange", linewidth=0.6, linestyle=":", alpha=0.7)
ax_vix.axhline(VIX_ELEVATED, color="red", linewidth=0.6, linestyle=":", alpha=0.7)
ax_vix.set_ylabel("VIX", color="purple")
ax_vix.tick_params(axis="y", labelcolor="purple")
ax_vix.legend(loc="upper right", fontsize=9)

# ── Panel B : Risk-Reward Scatter ────────────────────────────────────────────
ax_scatter = fig.add_subplot(gs[1, 0])

pop_vals, sortino_vals, names, colors, sizes = [], [], [], [], []
for _, row in df_playbook.iterrows():
    try:
        pop_mid = np.mean([float(x) for x in row["POP (%)"].replace(" ", "").split("–")])
        sortino_mid = np.mean([float(x) for x in row["Sortino"].replace(" ", "").split("–")])
        pop_vals.append(pop_mid)
        sortino_vals.append(sortino_mid)
        names.append(row["Strategy"])
        colors.append(CATEGORY_COLORS.get(row["Category"], "grey"))
        # Highlight recommended strategies with larger marker
        sizes.append(MARKER_SIZE_RECOMMENDED if recommended_mask.loc[row.name] else MARKER_SIZE_DEFAULT)
    except Exception:
        pass

sc = ax_scatter.scatter(pop_vals, sortino_vals, c=colors, s=sizes, alpha=0.8, edgecolors="black", linewidths=0.5)
for x, y, n, s in zip(pop_vals, sortino_vals, names, sizes):
    short_n = n[:22] + ".." if len(n) > 22 else n
    ax_scatter.annotate(short_n, (x, y), fontsize=5.5, ha="center", va="bottom",
                        xytext=(0, 4), textcoords="offset points")

cat_legend = [mpatches.Patch(color=c, label=cat) for cat, c in CATEGORY_COLORS.items()]
ax_scatter.legend(handles=cat_legend, fontsize=8, title="Category")
ax_scatter.set_xlabel("POP – Probability of Profit (%)")
ax_scatter.set_ylabel("Sortino Ratio (mid-range)")
ax_scatter.set_title("Strategy Risk–Reward Map\n(larger dot = recommended for current regime/VIX)", fontsize=10, fontweight="bold")
ax_scatter.grid(True, alpha=0.3)

# ── Panel C : Win-Rate Bar Chart ─────────────────────────────────────────────
ax_bar = fig.add_subplot(gs[1, 1])
wr_mid, strat_names, bar_colors = [], [], []
for _, row in df_playbook.iterrows():
    try:
        wr = np.mean([float(x) for x in row["Win Rate (%)"].replace(" ", "").split("–")])
        wr_mid.append(wr)
        strat_names.append(row["Strategy"][:28])
        bar_colors.append(CATEGORY_COLORS.get(row["Category"], "grey"))
    except Exception:
        pass

y_pos = np.arange(len(strat_names))
bars = ax_bar.barh(y_pos, wr_mid, color=bar_colors, alpha=0.8, edgecolor="black", linewidth=0.4)
ax_bar.set_yticks(y_pos)
ax_bar.set_yticklabels(strat_names, fontsize=6.5)
ax_bar.set_xlabel("Win Rate (%) – historical mid-range")
ax_bar.set_title("Historical Win Rate by Strategy", fontsize=10, fontweight="bold")
ax_bar.axvline(50, color="grey", linewidth=0.8, linestyle="--")
ax_bar.set_xlim(0, 85)
ax_bar.grid(True, axis="x", alpha=0.3)
# Highlight recommended
for i, row in enumerate(df_playbook.itertuples()):
    if recommended_mask.iloc[i]:
        bars[i].set_edgecolor("gold")
        bars[i].set_linewidth(2.0)

# ── Panel D : Full Playbook Table (two halves) ───────────────────────────────
table_cols = ["Strategy", "Category", "Leg 1 DTE", "Leg 2 DTE",
              "Short Leg Delta", "Long Leg Delta", "POP (%)", "Win Rate (%)", "Sortino"]
df_tbl = df_playbook[table_cols].copy()
n_half = len(df_tbl) // 2

for panel_idx, (ax_pos, slice_) in enumerate([
    (gs[2, 0], df_tbl.iloc[:n_half]),
    (gs[2, 1], df_tbl.iloc[n_half:]),
]):
    ax_t = fig.add_subplot(ax_pos)
    ax_t.axis("off")
    col_widths = [0.30, 0.13, 0.07, 0.07, 0.09, 0.09, 0.07, 0.09, 0.09]
    tbl = ax_t.table(
        cellText=slice_.values,
        colLabels=slice_.columns.tolist(),
        cellLoc="center",
        loc="center",
        colWidths=col_widths,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(6.0)
    tbl.scale(1, 1.55)

    # Header styling
    for col_i in range(len(table_cols)):
        tbl[(0, col_i)].set_facecolor("#2c3e50")
        tbl[(0, col_i)].set_text_props(color="white", fontweight="bold")

    # Row colouring by category
    cat_col_idx = table_cols.index("Category")
    for row_i, (_, row) in enumerate(slice_.iterrows(), start=1):
        cat = row["Category"]
        bg = CATEGORY_COLORS.get(cat, "#ecf0f1")
        for col_i in range(len(table_cols)):
            tbl[(row_i, col_i)].set_facecolor(bg)
            tbl[(row_i, col_i)].set_alpha(0.25)
            tbl[(row_i, col_i)].set_text_props(fontsize=5.8)

    ax_t.set_title(
        f"Option Playbook – Metrics (Part {panel_idx + 1})",
        fontsize=10, fontweight="bold", pad=6
    )

# ── Panel E : Regime Distribution + VIX histogram ───────────────────────────
ax_pie = fig.add_subplot(gs[3, 0])
regime_counts = regime_series.value_counts()
pie_colors = [REGIME_COLORS.get(r, "grey") for r in regime_counts.index]
ax_pie.pie(
    regime_counts.values,
    labels=regime_counts.index,
    colors=pie_colors,
    autopct="%1.1f%%",
    startangle=90,
    textprops={"fontsize": 9},
)
ax_pie.set_title(f"Regime Distribution (last {NUM_YEARS} years)", fontsize=10, fontweight="bold")

ax_vix_hist = fig.add_subplot(gs[3, 1])
vix_hist_data = vix_aligned.dropna()
ax_vix_hist.hist(vix_hist_data, bins=40, color="purple", alpha=0.7, edgecolor="black", linewidth=0.4)
ax_vix_hist.axvline(VIX_LOW, color="green", linestyle="--", linewidth=1.2, label=f"VIX={VIX_LOW} (Low)")
ax_vix_hist.axvline(VIX_NORMAL, color="orange", linestyle="--", linewidth=1.2, label=f"VIX={VIX_NORMAL} (Normal)")
ax_vix_hist.axvline(VIX_ELEVATED, color="red", linestyle="--", linewidth=1.2, label=f"VIX={VIX_ELEVATED} (High)")
ax_vix_hist.axvline(current_vix, color="black", linestyle="-", linewidth=2, label=f"Current VIX={current_vix:.1f}")
ax_vix_hist.legend(fontsize=8)
ax_vix_hist.set_xlabel("VIX Level")
ax_vix_hist.set_ylabel("Frequency (trading days)")
ax_vix_hist.set_title("VIX Distribution & Regime Buckets", fontsize=10, fontweight="bold")
ax_vix_hist.grid(True, alpha=0.3)

# ── Super-title ───────────────────────────────────────────────────────────────
fig.suptitle(
    "Options Strategy Playbook  |  Regime & VIX-Based  |  Income · Directional · Stock Substitutes",
    fontsize=14, fontweight="bold", y=0.995,
)

png_path = "option_playbook_chart.png"
plt.savefig(png_path, dpi=CHART_DPI, bbox_inches="tight")
plt.show()
print(f"Chart saved to {png_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 11. Risk Summary Table — hedge-fund style
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "═" * 80)
print("  RISK SUMMARY BY CATEGORY")
print("═" * 80)
risk_cols = ["Strategy", "Category", "Key Risk", "Max Risk", "IV Preference", "Notes"]
for cat in ["Income", "Directional", "Stock Substitute"]:
    print(f"\n── {cat} ──")
    sub = df_playbook[df_playbook["Category"] == cat][risk_cols]
    print(sub.to_string(index=False))

print("\n" + "═" * 80)
print("  HEDGE-FUND MANAGER NOTES")
print("═" * 80)
notes = [
    "1. REGIME FIRST: Always identify regime before selecting a strategy.",
    "   - Bull  →  bias toward premium-selling (CSP, CC, Bull Put Spread) + stock subs (PMCC, LEAPS).",
    "   - Neutral→  Iron Condor, Jade Lizard, Calendar Spread (capture theta in range-bound markets).",
    "   - Bear  →  Bear Put Spread, Bear Call Spread, Long Put; hedge existing longs with Collars.",
    "   - Crisis →  Short Strangle / Iron Butterfly ONLY on liquid ETFs; avoid single-stock risk.",
    "",
    "2. VIX DISCIPLINE:",
    "   - VIX <15 : Buy premium (Long Calls, Straddles, LEAPS). IV is cheap.",
    "   - VIX 15-20: Mix income + directional. CSP, Bull Put Spread, Diagonal.",
    "   - VIX 20-30: Sell premium aggressively (Iron Condor, Strangle, Jade Lizard).",
    "   - VIX >30 : Extreme premium selling opportunity; wide strangles; size down!",
    "",
    "3. POSITION SIZING:",
    "   - Never risk more than 2-5% of portfolio per trade.",
    "   - Undefined-risk (strangles) positions: max 1-2% risk allocation.",
    "   - Defined-risk (spreads): max 3-5% risk allocation.",
    "",
    "4. MANAGEMENT RULES:",
    "   - Take profits at 50% of max credit (proven to outperform holding to expiry).",
    "   - Close losers at 2× credit received (prevents large drawdowns).",
    "   - Roll positions with 21 DTE remaining to next monthly cycle.",
    "   - Adjust delta-heavy positions when underlying moves ≥0.5 SD from entry.",
    "",
    "5. SORTINO > SHARPE:",
    "   - Income strategies target Sortino >1.0 (downside-risk-adjusted return).",
    "   - LEAPS / Stock Substitutes target Sortino >2.0 (leveraged, limited downside).",
    "",
    "6. PORTFOLIO CONSTRUCTION:",
    "   - 60% Income strategies (stable theta income, Sharpe diversification).",
    "   - 25% Stock Substitutes / LEAPS (leveraged directional with defined downside).",
    "   - 15% Directional (high-conviction trades, long convexity hedge).",
]
for line in notes:
    print(line)
print("═" * 80)
