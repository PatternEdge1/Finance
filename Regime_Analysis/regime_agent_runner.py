"""
Regime_Analysis/regime_agent_runner.py
=======================================
Agent-ready, fully non-interactive regime analysis runner.

Designed to be called by Claude agents (or any automation) without requiring
any keyboard input, GUI windows, or manual approval.

Usage
-----
# Default: SPY, 5 years, saves output to current directory
python Regime_Analysis/regime_agent_runner.py

# Custom ticker / lookback / output directory
python Regime_Analysis/regime_agent_runner.py --ticker QQQ --years 3 --output-dir /tmp/regime_out

# Suppress chart generation (metrics only)
python Regime_Analysis/regime_agent_runner.py --no-charts

Exit codes
----------
0  — analysis completed successfully
1  — error (ticker not found, insufficient data, …)
"""

import argparse
import datetime
import os
import sys
import warnings

import matplotlib
matplotlib.use('Agg')          # non-interactive backend — required for agents
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import yfinance as yf
from sklearn.mixture import GaussianMixture

warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# CLI arguments
# ─────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(
        description='GMM Regime Analysis — agent-friendly runner',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('--ticker', default='SPY',
                        help='Ticker symbol to analyse')
    parser.add_argument('--years', type=float, default=5.0,
                        help='Number of years of historical data to use')
    parser.add_argument('--rolling-window', type=int, default=22,
                        help='Rolling window (trading days) for vol / stats')
    parser.add_argument('--bb-window', type=int, default=20,
                        help='Bollinger Band window')
    parser.add_argument('--bb-std', type=float, default=2.0,
                        help='Bollinger Band std-dev multiplier')
    parser.add_argument('--momentum-window', type=int, default=50,
                        help='SMA window for momentum signal')
    parser.add_argument('--n-components', type=int, default=2,
                        help='Number of GMM components (regimes)')
    parser.add_argument('--output-dir', default='.',
                        help='Directory for output PNG charts and CSV files')
    parser.add_argument('--no-charts', action='store_true',
                        help='Skip chart generation (print metrics only)')
    return parser.parse_args()


# ─────────────────────────────────────────────
# Core analysis
# ─────────────────────────────────────────────

def run_regime_analysis(
    ticker: str,
    years: float,
    rolling_window: int,
    bb_window: int,
    bb_std: float,
    momentum_window: int,
    n_components: int,
    output_dir: str,
    save_charts: bool,
) -> dict:
    """
    Run end-to-end GMM regime analysis and return a results dictionary.

    Parameters
    ----------
    ticker         : Ticker symbol (uppercase recommended)
    years          : Lookback period in years
    rolling_window : Rolling window for volatility / statistics
    bb_window      : Bollinger Band window
    bb_std         : Bollinger Band standard deviation multiplier
    momentum_window: SMA window for momentum signal
    n_components   : Number of GMM regime components
    output_dir     : Directory to save output files
    save_charts    : Whether to save PNG charts

    Returns
    -------
    dict with keys:
        ticker, current_regime, regime_counts,
        metrics (dict keyed by strategy name),
        chart_path (str or None)
    """
    ticker = ticker.upper()
    start = datetime.date.today() - datetime.timedelta(days=int(365.25 * years))
    trading_days = 252

    print(f'\n{"="*60}')
    print(f'Regime Analysis: {ticker}  |  lookback: {years}y  |  start: {start}')
    print(f'{"="*60}')

    # ── 1. Download data ───────────────────────────────────────────
    print(f'Downloading {ticker} data …')
    raw = yf.download(ticker, start=start, progress=False, auto_adjust=True)
    if raw.empty:
        raise ValueError(f'No data returned for ticker "{ticker}". '
                         f'Check the symbol and your internet connection.')

    close = raw['Close'].squeeze()
    high  = raw['High'].squeeze()
    low   = raw['Low'].squeeze()

    if len(close) < rolling_window * 2:
        raise ValueError(
            f'Insufficient data: {len(close)} bars downloaded for {ticker}. '
            f'Need at least {rolling_window * 2} bars.'
        )

    log_returns = np.log(close / close.shift(1)).dropna()

    # ── 2. GMM regime detection ────────────────────────────────────
    rolling_vol = log_returns.rolling(rolling_window).std().dropna()

    gmm = GaussianMixture(n_components=n_components, random_state=42)
    regime_labels = gmm.fit_predict(rolling_vol.values.reshape(-1, 1))

    mean_vol  = [rolling_vol[regime_labels == i].mean() for i in range(n_components)]
    sorted_labels = np.argsort(mean_vol)          # ascending vol order
    bull_label    = int(sorted_labels[0])          # lowest vol  → bull
    neutral_label = int(sorted_labels[-1])         # highest vol → neutral (bear/choppy)

    # Assign named regimes: lowest vol = bull, highest vol = neutral,
    # any intermediate components map to 'neutral' as well.
    label_to_regime = {lbl: 'neutral' for lbl in range(n_components)}
    label_to_regime[bull_label] = 'bull'

    regime_series = pd.Series(
        [label_to_regime[lbl] for lbl in regime_labels],
        index=rolling_vol.index,
        name='regime',
    )

    current_regime = regime_series.iloc[-1]
    regime_counts  = regime_series.value_counts().to_dict()

    print(f'\nCurrent regime  : {current_regime.upper()}')
    print(f'Regime counts   : {regime_counts}')

    # ── 3. Align price / return series ────────────────────────────
    price   = close.reindex(regime_series.index)
    returns = log_returns.reindex(regime_series.index)

    # ── 4. Bull momentum signal ────────────────────────────────────
    sma = price.rolling(momentum_window).mean()
    bull_signal = pd.Series(0.0, index=price.index)
    bull_mask   = (price > sma) & (regime_series == 'bull')
    bull_signal[bull_mask] = 1.0

    bull_rets     = bull_signal.shift(1) * returns
    bull_cum_rets = bull_rets.cumsum().apply(np.exp) - 1

    # ── 5. Neutral Bollinger Band mean-reversion ───────────────────
    bb_mid   = price.rolling(bb_window).mean()
    bb_std_s = price.rolling(bb_window).std()
    bb_lower = bb_mid - bb_std * bb_std_s

    neutral_pos     = 0
    neutral_sig_arr = np.zeros(len(price))
    price_arr       = price.values
    bb_lower_arr    = bb_lower.values
    bb_mid_arr      = bb_mid.values
    regime_arr      = regime_series.values

    for i in range(len(price_arr)):
        if np.isnan(bb_lower_arr[i]):
            continue
        if regime_arr[i] == 'neutral':
            if neutral_pos == 0 and price_arr[i] < bb_lower_arr[i]:
                neutral_pos = 1
            elif neutral_pos == 1 and price_arr[i] >= bb_mid_arr[i]:
                neutral_pos = 0
        else:
            neutral_pos = 0
        neutral_sig_arr[i] = float(neutral_pos)

    neutral_signal   = pd.Series(neutral_sig_arr, index=price.index)
    neutral_rets     = neutral_signal.shift(1) * returns
    neutral_cum_rets = neutral_rets.cumsum().apply(np.exp) - 1

    # ── 6. Combined regime-adaptive ────────────────────────────────
    combined_signal = pd.Series(0.0, index=price.index)
    combined_signal[regime_series == 'bull']    = bull_signal[regime_series == 'bull']
    combined_signal[regime_series == 'neutral'] = neutral_signal[regime_series == 'neutral']

    combined_rets     = combined_signal.shift(1) * returns
    combined_cum_rets = combined_rets.cumsum().apply(np.exp) - 1
    bah_cum_rets      = returns.cumsum().apply(np.exp) - 1

    # ── 7. Performance metrics ─────────────────────────────────────
    def _metrics(strat_rets, name):
        ann_ret = strat_rets.mean() * trading_days
        ann_vol = strat_rets.std() * np.sqrt(trading_days)
        sharpe  = ann_ret / ann_vol if ann_vol != 0 else np.nan
        total   = (strat_rets.cumsum().apply(np.exp) - 1).iloc[-1]
        wins    = (strat_rets > 0).sum()
        losses  = (strat_rets < 0).sum()
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else np.nan
        cum      = strat_rets.cumsum().apply(np.exp)
        max_dd   = ((cum - cum.cummax()) / cum.cummax()).min()

        print(f'\n  Strategy: {name}')
        print(f'    Total Return   : {total*100:.2f}%')
        print(f'    Ann. Return    : {ann_ret*100:.2f}%')
        print(f'    Ann. Volatility: {ann_vol*100:.2f}%')
        print(f'    Sharpe Ratio   : {sharpe:.2f}')
        print(f'    Win Rate       : {win_rate*100:.2f}%')
        print(f'    Max Drawdown   : {max_dd*100:.2f}%')

        return {
            'total_return_pct': round(total * 100, 2),
            'ann_return_pct':   round(ann_ret * 100, 2),
            'ann_vol_pct':      round(ann_vol * 100, 2),
            'sharpe':           round(sharpe, 3) if not np.isnan(sharpe) else None,
            'win_rate_pct':     round(win_rate * 100, 2) if not np.isnan(win_rate) else None,
            'max_drawdown_pct': round(max_dd * 100, 2),
        }

    print('\n─── Performance Metrics ───')
    all_metrics = {
        'buy_and_hold':          _metrics(returns,       'Buy & Hold'),
        'bull_momentum':         _metrics(bull_rets,     'Bull Momentum'),
        'neutral_mean_reversion':_metrics(neutral_rets,  'Neutral Mean-Reversion'),
        'combined_regime_adaptive': _metrics(combined_rets, 'Combined Regime-Adaptive'),
    }

    # ── 8. Optional charts ─────────────────────────────────────────
    chart_path = None
    if save_charts:
        os.makedirs(output_dir, exist_ok=True)
        chart_path = os.path.join(output_dir, f'{ticker}_regime_analysis.png')

        fig, axes = plt.subplots(
            3, 1, figsize=(15, 14),
            gridspec_kw={'height_ratios': [1, 1, 1.5]},
        )
        date_fmt = mdates.DateFormatter('%Y-%m')

        # Panel 1: Price + Bollinger Bands + regime shading
        ax1 = axes[0]
        ax1.plot(price.index, price, color='black', linewidth=1, label=ticker)
        ax1.plot(bb_mid,   color='blue',  linewidth=0.7, linestyle='--', label='BB Mid')
        ax1.plot(bb_mid + bb_std * bb_std_s, color='red',   linewidth=0.5, linestyle=':', label='BB Upper')
        ax1.plot(bb_lower, color='green', linewidth=0.5, linestyle=':', label='BB Lower')
        for i in range(len(regime_series) - 1):
            color = 'green' if regime_series.iloc[i] == 'bull' else 'orange'
            ax1.axvspan(regime_series.index[i], regime_series.index[i + 1],
                        alpha=0.08, color=color)
        ax1.set_title(f'{ticker} Price with Market Regimes (green=Bull, orange=Neutral)', fontsize=11)
        ax1.set_ylabel('Price ($)')
        ax1.legend(loc='upper left', fontsize=8)
        ax1.xaxis.set_major_formatter(date_fmt)
        ax1.grid(True, alpha=0.3)

        # Panel 2: Rolling annualised volatility
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

        # Panel 3: Cumulative returns comparison
        ax3 = axes[2]
        ax3.plot(bah_cum_rets.index,      bah_cum_rets * 100,      color='black',  linewidth=1.5, label='Buy & Hold')
        ax3.plot(bull_cum_rets.index,     bull_cum_rets * 100,     color='green',  linewidth=1.2, label='Bull Momentum')
        ax3.plot(neutral_cum_rets.index,  neutral_cum_rets * 100,  color='orange', linewidth=1.2, label='Neutral Mean-Reversion')
        ax3.plot(combined_cum_rets.index, combined_cum_rets * 100, color='blue',   linewidth=1.8, linestyle='--', label='Combined Regime-Adaptive')
        ax3.axhline(0, color='gray', linestyle=':', linewidth=0.8)
        ax3.set_title('Cumulative Returns: Income Strategies vs Buy & Hold', fontsize=11)
        ax3.set_ylabel('Cumulative Return (%)')
        ax3.set_xlabel('Date')
        ax3.legend(loc='upper left', fontsize=9)
        ax3.xaxis.set_major_formatter(date_fmt)
        ax3.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(chart_path, dpi=120, bbox_inches='tight')
        plt.close(fig)
        print(f'\nChart saved → {chart_path}')

    # ── 9. Save metrics CSV ────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, f'{ticker}_regime_metrics.csv')
    rows = []
    for strat, m in all_metrics.items():
        rows.append({'ticker': ticker, 'strategy': strat,
                     'current_regime': current_regime, **m})
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    print(f'Metrics CSV saved → {csv_path}')

    return {
        'ticker':         ticker,
        'current_regime': current_regime,
        'regime_counts':  regime_counts,
        'metrics':        all_metrics,
        'chart_path':     chart_path,
        'csv_path':       csv_path,
    }


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

if __name__ == '__main__':
    args = parse_args()
    try:
        result = run_regime_analysis(
            ticker=args.ticker,
            years=args.years,
            rolling_window=args.rolling_window,
            bb_window=args.bb_window,
            bb_std=args.bb_std,
            momentum_window=args.momentum_window,
            n_components=args.n_components,
            output_dir=args.output_dir,
            save_charts=not args.no_charts,
        )
        print(f'\n✓ Done. Current regime for {result["ticker"]}: {result["current_regime"].upper()}')
        sys.exit(0)
    except Exception as exc:
        print(f'\nERROR: {exc}', file=sys.stderr)
        sys.exit(1)
