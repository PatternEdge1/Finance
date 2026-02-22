"""
Regime-Based Income Trading Strategies
=======================================
Generates income across market regimes: Bull and Neutral.

Regime Detection:
  - Gaussian Mixture Model (GMM) on rolling volatility
  - Bull regime:    trending upward, lower rolling volatility
  - Neutral regime: ranging/sideways, higher rolling volatility

Strategies:
  - Bull:    Momentum / trend-following with dividend ETF focus
  - Neutral: Bollinger Band mean-reversion (buy dips, sell at mean)
  - Combined: Regime-adaptive strategy switching between the two

Usage:
  python regime_income_strategies.py
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import yfinance as yf
import datetime
import warnings
from sklearn.mixture import GaussianMixture

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# Parameters
# ─────────────────────────────────────────────
TICKER = 'SPY'          # Primary asset
NUM_YEARS = 5           # Lookback window
ROLLING_WINDOW = 22     # ~1 trading month for rolling statistics
BB_WINDOW = 20          # Bollinger Band window
BB_STD = 2.0            # Bollinger Band standard deviation multiplier
MOMENTUM_WINDOW = 50    # Momentum trend window (SMA)
N_COMPONENTS = 2        # Number of GMM components (bull / neutral)

# ─────────────────────────────────────────────
# 1. Download Data
# ─────────────────────────────────────────────
start = datetime.date.today() - datetime.timedelta(days=int(365.25 * NUM_YEARS))
print(f'Downloading {TICKER} data from {start} …')
raw = yf.download(TICKER, start=start, progress=False)

close = raw['Adj Close'].squeeze()
high = raw['High'].squeeze()
low = raw['Low'].squeeze()

log_returns = np.log(close / close.shift(1)).dropna()

# ─────────────────────────────────────────────
# 2. Regime Detection via GMM on Rolling Volatility
# ─────────────────────────────────────────────
rolling_vol = log_returns.rolling(ROLLING_WINDOW).std().dropna()

gmm = GaussianMixture(n_components=N_COMPONENTS, random_state=42)
regime_labels = gmm.fit_predict(rolling_vol.values.reshape(-1, 1))

# Identify which label corresponds to the bull (lower-vol) regime.
# Lower average volatility → trending/bull; higher vol → choppy/neutral.
mean_vol = [rolling_vol[regime_labels == i].mean() for i in range(N_COMPONENTS)]
bull_label = int(np.argmin(mean_vol))
neutral_label = 1 - bull_label

regime_series = pd.Series(
    np.where(regime_labels == bull_label, 'bull', 'neutral'),
    index=rolling_vol.index,
    name='regime',
)

print(f'\nRegime distribution:\n{regime_series.value_counts()}')

# Align price data with regime index
price = close.reindex(regime_series.index)
returns = log_returns.reindex(regime_series.index)

# ─────────────────────────────────────────────
# 3. Bull Strategy: Momentum / Trend-Following
#    ‣ Long when price > SMA(MOMENTUM_WINDOW)
#    ‣ Cash (0) otherwise — avoids drawdowns
#    ‣ Suitable for bull regime; dividend-payers trend upward
# ─────────────────────────────────────────────
sma = price.rolling(MOMENTUM_WINDOW).mean()
# Signal: 1 (long) when price above SMA and in bull regime; else 0
bull_signal = pd.Series(0.0, index=price.index)
bull_mask = (price > sma) & (regime_series == 'bull')
bull_signal[bull_mask] = 1.0

bull_strategy_returns = bull_signal.shift(1) * returns
bull_cum_returns = bull_strategy_returns.cumsum().apply(np.exp) - 1

# ─────────────────────────────────────────────
# 4. Neutral Strategy: Bollinger Band Mean-Reversion
#    ‣ Buy when close < Lower Band (oversold)
#    ‣ Sell when close > Middle Band (mean)
#    ‣ Generates income from repeated mean-reversion oscillations
# ─────────────────────────────────────────────
bb_mid = price.rolling(BB_WINDOW).mean()
bb_std = price.rolling(BB_WINDOW).std()
bb_upper = bb_mid + BB_STD * bb_std
bb_lower = bb_mid - BB_STD * bb_std

neutral_position = 0
neutral_signal_arr = np.zeros(len(price))
price_arr = price.values
bb_lower_arr = bb_lower.values
bb_mid_arr = bb_mid.values
regime_arr = regime_series.values

for i in range(len(price_arr)):
    if np.isnan(bb_lower_arr[i]):
        continue
    if regime_arr[i] == 'neutral':
        if neutral_position == 0 and price_arr[i] < bb_lower_arr[i]:
            neutral_position = 1       # enter long
        elif neutral_position == 1 and price_arr[i] >= bb_mid_arr[i]:
            neutral_position = 0       # exit at mean
    else:
        neutral_position = 0           # flat outside neutral regime
    neutral_signal_arr[i] = float(neutral_position)

neutral_signal = pd.Series(neutral_signal_arr, index=price.index)

neutral_strategy_returns = neutral_signal.shift(1) * returns
neutral_cum_returns = neutral_strategy_returns.cumsum().apply(np.exp) - 1

# ─────────────────────────────────────────────
# 5. Combined Regime-Adaptive Strategy
#    ‣ Bull regime  → use momentum signal
#    ‣ Neutral regime → use mean-reversion signal
# ─────────────────────────────────────────────
combined_signal = pd.Series(0.0, index=price.index)
combined_signal[regime_series == 'bull'] = bull_signal[regime_series == 'bull']
combined_signal[regime_series == 'neutral'] = neutral_signal[regime_series == 'neutral']

combined_strategy_returns = combined_signal.shift(1) * returns
combined_cum_returns = combined_strategy_returns.cumsum().apply(np.exp) - 1

# Buy-and-Hold benchmark
bah_cum_returns = returns.cumsum().apply(np.exp) - 1

# ─────────────────────────────────────────────
# 6. Performance Metrics
# ─────────────────────────────────────────────
trading_days = 252

def performance_metrics(strategy_returns, name):
    ann_return = strategy_returns.mean() * trading_days
    ann_vol = strategy_returns.std() * np.sqrt(trading_days)
    sharpe = ann_return / ann_vol if ann_vol != 0 else np.nan
    total_return = (strategy_returns.cumsum().apply(np.exp) - 1).iloc[-1]
    wins = (strategy_returns > 0).sum()
    losses = (strategy_returns < 0).sum()
    win_rate = wins / (wins + losses) if (wins + losses) > 0 else np.nan

    # Max drawdown
    cum = strategy_returns.cumsum().apply(np.exp)
    rolling_max = cum.cummax()
    drawdown = (cum - rolling_max) / rolling_max
    max_dd = drawdown.min()

    print(f'\n{"─"*50}')
    print(f'Strategy: {name}')
    print(f'  Total Return      : {total_return*100:.2f}%')
    print(f'  Ann. Return       : {ann_return*100:.2f}%')
    print(f'  Ann. Volatility   : {ann_vol*100:.2f}%')
    print(f'  Sharpe Ratio      : {sharpe:.2f}')
    print(f'  Win Rate          : {win_rate*100:.2f}%')
    print(f'  Max Drawdown      : {max_dd*100:.2f}%')
    return total_return, sharpe

print('\n===== PERFORMANCE METRICS =====')
performance_metrics(returns, 'Buy and Hold')
performance_metrics(bull_strategy_returns, 'Bull Momentum')
performance_metrics(neutral_strategy_returns, 'Neutral Mean-Reversion')
performance_metrics(combined_strategy_returns, 'Combined Regime-Adaptive')

# ─────────────────────────────────────────────
# 7. Visualizations
# ─────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(15, 14), gridspec_kw={'height_ratios': [1, 1, 1.5]})
date_fmt = mdates.DateFormatter('%Y-%m')

# --- Panel 1: Price with Regime Background ---
ax1 = axes[0]
ax1.plot(price.index, price, color='black', linewidth=1, label=TICKER)
ax1.plot(bb_mid, color='blue', linewidth=0.7, linestyle='--', label='BB Mid')
ax1.plot(bb_upper, color='red', linewidth=0.5, linestyle=':', label='BB Upper')
ax1.plot(bb_lower, color='green', linewidth=0.5, linestyle=':', label='BB Lower')

# Shade regimes
for i in range(len(regime_series) - 1):
    if regime_series.iloc[i] == 'bull':
        ax1.axvspan(regime_series.index[i], regime_series.index[i + 1],
                    alpha=0.08, color='green')
    else:
        ax1.axvspan(regime_series.index[i], regime_series.index[i + 1],
                    alpha=0.08, color='orange')

ax1.set_title(f'{TICKER} Price with Market Regimes (green=Bull, orange=Neutral)', fontsize=11)
ax1.set_ylabel('Price ($)')
ax1.legend(loc='upper left', fontsize=8)
ax1.xaxis.set_major_formatter(date_fmt)
ax1.grid(True, alpha=0.3)

# --- Panel 2: Rolling Volatility with Regime Labels ---
ax2 = axes[1]
ax2.plot(rolling_vol.index, rolling_vol * np.sqrt(trading_days) * 100,
         color='purple', linewidth=1, label='Ann. Volatility (%)')

for i in range(len(regime_series) - 1):
    color = 'green' if regime_series.iloc[i] == 'bull' else 'orange'
    ax2.axvspan(regime_series.index[i], regime_series.index[i + 1],
                alpha=0.08, color=color)

ax2.set_title('Rolling Annualised Volatility by Regime', fontsize=11)
ax2.set_ylabel('Volatility (%)')
ax2.legend(loc='upper right', fontsize=8)
ax2.xaxis.set_major_formatter(date_fmt)
ax2.grid(True, alpha=0.3)

# --- Panel 3: Cumulative Returns Comparison ---
ax3 = axes[2]
ax3.plot(bah_cum_returns.index, bah_cum_returns * 100,
         color='black', linewidth=1.5, label='Buy & Hold')
ax3.plot(bull_cum_returns.index, bull_cum_returns * 100,
         color='green', linewidth=1.2, label='Bull Momentum')
ax3.plot(neutral_cum_returns.index, neutral_cum_returns * 100,
         color='orange', linewidth=1.2, label='Neutral Mean-Reversion')
ax3.plot(combined_cum_returns.index, combined_cum_returns * 100,
         color='blue', linewidth=1.8, linestyle='--', label='Combined Regime-Adaptive')

ax3.axhline(0, color='gray', linestyle=':', linewidth=0.8)
ax3.set_title('Cumulative Returns: Income Strategies vs Buy & Hold', fontsize=11)
ax3.set_ylabel('Cumulative Return (%)')
ax3.set_xlabel('Date')
ax3.legend(loc='upper left', fontsize=9)
ax3.xaxis.set_major_formatter(date_fmt)
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('regime_income_strategies.png', dpi=120, bbox_inches='tight')
plt.show()
print('\nChart saved to regime_income_strategies.png')
