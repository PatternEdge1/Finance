# Finance Repository – Tutorial

Welcome! This guide walks you through everything you need to know to get started with the tools in this repository.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Module Guide](#module-guide)
   - [Find_Stocks](#find_stocks)
   - [Stock_Data](#stock_data)
   - [Stock_Analysis](#stock_analysis)
   - [Technical_Indicators](#technical_indicators)
   - [Portfolio_Strategies](#portfolio_strategies)
   - [Machine_Learning](#machine_learning)
5. [Quick-Start Examples](#quick-start-examples)
6. [Tips & Common Issues](#tips--common-issues)
7. [Disclaimer](#disclaimer)

---

## Overview

This repository is a collection of Python scripts for **stock market research and analysis**. Each folder is self-contained around a specific theme:

| Folder | Theme |
|---|---|
| `Find_Stocks` | Screeners that surface candidate buy signals |
| `Stock_Data` | Data collection – prices, fundamentals, dividends, etc. |
| `Stock_Analysis` | Statistical analysis of returns, risk, CAPM, etc. |
| `Technical_Indicators` | ~140 charted technical indicators (RSI, MACD, Bollinger Bands …) |
| `Portfolio_Strategies` | Portfolio optimisation, backtesting, trading strategies |
| `Machine_Learning` | ML/DL price prediction and classification models |

Scripts are standalone – just open the one you want, adjust the ticker/parameter variables near the top, and run it.

---

## Prerequisites

- **Python 3.8 or higher** (`python --version`)
- **pip** package manager

Optional but useful:
- A free [Yahoo Finance](https://finance.yahoo.com/) account (most data comes via `yfinance` / `pandas_datareader`)
- API keys for optional data sources (Alpaca, Alpha Vantage, Tiingo, Quandl, Twilio, Twitter) – only required by the specific scripts that use them

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/PatternEdge1/Finance.git
cd Finance

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

> **Note:** Some packages (e.g. `TA-Lib`, `tensorflow`, `fbprophet`) have additional system-level requirements. Check the respective library's installation guide if you hit errors.

---

## Module Guide

### Find_Stocks

Scripts that **screen the market** and surface potential buy opportunities.

| Script | What it does |
|---|---|
| `rsi_values.py` | Scans S&P 500 tickers and flags those that are oversold (RSI ≤ 30) or overbought (RSI ≥ 70) |
| `finviz_growth.py` | Scrapes Finviz for growth-oriented stocks |
| `fundamental_ratios_screener.py` | Filters stocks by fundamental ratios (P/E, P/B, etc.) |
| `yahoo_recommendations.py` | Parses analyst buy/sell/hold recommendations from Yahoo Finance |
| `stock_sentiment.py` | Calculates sentiment score from news headlines |
| `send_top_movers.py` | Sends an e-mail/SMS with the day's top movers |
| `email_stock_alert.py` | E-mails an alert when a stock hits a price threshold |
| `scrape_reddit.py` | Scrapes Reddit (e.g. r/WallStreetBets) for trending tickers |

**Quick start:**

```bash
cd Find_Stocks
python rsi_values.py
```

---

### Stock_Data

Scripts that **collect raw market data** and save or display it.

| Script | What it does |
|---|---|
| `basic_stock_data.py` | Fetches 5-year OHLCV history and computes alpha, beta, R², volatility, momentum |
| `dividend_history.py` | Downloads the full dividend history for a ticker |
| `historical_sp500_data.py` | Downloads historical OHLCV for all S&P 500 companies and saves them to individual CSV files |
| `value_at_risk.py` | Computes Value-at-Risk (VaR) for a position |
| `finviz_parser.py` | Scrapes the Finviz stock page for a given ticker |
| `yf_intraday_data.py` | Downloads intraday (minute-level) data from Yahoo Finance |
| `stock_earnings.py` | Fetches upcoming earnings dates and EPS estimates |

**Quick start:**

Open `Stock_Data/basic_stock_data.py`, change the `stock` variable near the top to your ticker, then:

```bash
cd Stock_Data
python basic_stock_data.py
```

Expected output:

```
beta = 1.23
alpha = 0.05
r_squared = 0.72
volatility = 0.28
momentum = 0.34
```

---

### Stock_Analysis

Scripts that perform **statistical and quantitative analysis** on individual stocks or groups.

| Script | What it does |
|---|---|
| `capm_analysis.py` | CAPM (Capital Asset Pricing Model) analysis |
| `risk_vs_returns.py` | Plots a risk/return scatter for a list of stocks |
| `ols_regression.py` | OLS regression of a stock vs. a benchmark |
| `fibonacci_retracement.py` | Plots Fibonacci retracement levels |
| `kelly_criterion.py` | Calculates the Kelly Criterion optimal position size |
| `seasonal_stock_analysis.py` | Checks for seasonality patterns in stock returns |
| `stock_statistical_dist.py` | Fits statistical distributions to return data |
| `value_stocks.py` | Screens for undervalued stocks using fundamental metrics |

**Quick start:**

```bash
cd Stock_Analysis
python risk_vs_returns.py
```

---

### Technical_Indicators

Nearly **140 charted technical indicators**, each in its own self-contained script. Indicators include:

- Trend-following: SMA, EMA, TEMA, DEMA, KAMA, Ichimoku, Bollinger Bands …
- Momentum: RSI, MACD, Stochastic, ROC, CCI, Williams %R …
- Volume: MFI, OBV (Accumulation/Distribution), VWAP, Chaikin Oscillator …
- Volatility: ATR, Keltner Channels, Donchian Channel …

All scripts follow the same pattern:

1. Define a ticker and date range at the top of the file.
2. Data is fetched automatically from Yahoo Finance.
3. A Matplotlib chart is produced and displayed.

**Quick start:**

```bash
cd Technical_Indicators
python RSI.py          # Relative Strength Index
python bollinger_bands.py
python MACD.py
```

---

### Portfolio_Strategies

Scripts for **portfolio construction, optimisation, backtesting, and live strategy simulation**.

| Script | What it does |
|---|---|
| `optimal_portfolio.py` | Finds the portfolio weights that maximise the Sharpe ratio via scipy optimisation |
| `portfolio_optimization.py` | Mean-variance (Markowitz) efficient frontier |
| `monte_carlo.py` | Monte Carlo simulation of future portfolio values |
| `backtest_strategies.py` | Backtests moving average / RSI strategies |
| `moving_avg_strategy.py` | Simple & exponential moving average crossover strategy |
| `pairs_trading.py` | Statistical arbitrage / pairs trading with co-integration test |
| `risk_management.py` | Portfolio VaR, CVaR, and drawdown analysis |
| `portfolio_sharpe_ratio.py` | Computes Sharpe, Sortino, and Calmar ratios |
| `alpaca_algo_bot.py` | Live paper-trading bot via the Alpaca API (requires API key) |
| `geometric_brownian_motion.py` | GBM price simulation |

**Quick start – Optimal Portfolio:**

Open `Portfolio_Strategies/optimal_portfolio.py`, edit the `symbols` list near the top:

```python
symbols = ['AAPL', 'MSFT', 'TSLA']
```

Then run:

```bash
cd Portfolio_Strategies
python optimal_portfolio.py
```

Expected output:

```
Efficient Portfolio (Mean-Variance)
Symbols:  ['AAPL', 'MSFT', 'TSLA']
Sharpe ratio for an equal-weighted portfolio: 0.8412
Optimal weights: [0.52  0.31  0.17]
Sharpe ratio: 1.0234
```

---

### Machine_Learning

Scripts that apply **machine learning and deep learning** to stock price prediction and classification.

| Script | What it does |
|---|---|
| `lstm_prediction.py` | LSTM neural network trained on 10 years of close prices; predicts next-day price and movement accuracy |
| `lstm_arima_prediction.py` | Hybrid LSTM + ARIMA model |
| `prophet_ml_model.py` | Facebook Prophet time-series forecast |
| `ml_models_prediction.py` | Compares multiple sklearn regressors (RF, GBM, SVR …) |
| `ml_models_accuracy.py` | Evaluates model accuracy across multiple stocks |
| `kmeans_clustering.py` | K-Means clustering of stocks by return/risk profile |
| `PCA_analytics.py` | PCA dimensionality reduction on a stock universe |
| `deep_learning_bot.py` | Deep learning trading bot |
| `sklearn_trading_bot.py` | Sklearn-based trading signal classifier |
| `time_series_analysis.py` | ARIMA / SARIMA analysis |

**Quick start – LSTM Price Prediction:**

```bash
cd Machine_Learning
python lstm_prediction.py
# Prompts: Enter a stock ticker: AAPL
```

The script will:
1. Download 10 years of closing prices
2. Train an LSTM model (takes a few minutes)
3. Display a chart of actual vs. predicted prices
4. Print next-day price prediction and directional accuracy

---

## Quick-Start Examples

### Example 1 – Find oversold stocks

```bash
cd Find_Stocks
python rsi_values.py
# Iterates all S&P 500 tickers and prints those with RSI ≤ 30
```

### Example 2 – Plot RSI for a single stock

```bash
cd Technical_Indicators
# Open RSI.py and set: stock = 'NVDA'
python RSI.py
```

### Example 3 – Optimise a three-stock portfolio

```bash
cd Portfolio_Strategies
# Open optimal_portfolio.py and set: symbols = ['AAPL', 'GOOGL', 'AMZN']
python optimal_portfolio.py
```

### Example 4 – Predict next-day price with LSTM

```bash
cd Machine_Learning
python lstm_prediction.py
# Enter ticker when prompted, e.g. TSLA
```

---

## Tips & Common Issues

| Problem | Solution |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt`; for TA-Lib see [its install guide](https://github.com/mrjbq7/ta-lib) |
| Yahoo Finance data errors | Update yfinance: `pip install --upgrade yfinance` |
| Slow data downloads | Most scripts include a `time.sleep()` between API calls; this is intentional to avoid rate-limiting |
| API key scripts fail | Check that you have set the required environment variables or filled in the key directly in the script |
| `spxTickers.pickle` missing | Run `Stock_Data/historical_sp500_data.py` first to generate the pickle file used by some screeners |

---

## Disclaimer

*The material in this repository is purely for educational purposes and should not be taken as professional investment advice. Invest at your own discretion.*
