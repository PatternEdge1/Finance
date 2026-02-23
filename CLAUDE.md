# CLAUDE.md — Agent Guide for PatternEdge1/Finance

This file is read automatically by Claude Code and Claude-based agents.
It tells the agent how this repository is structured, how to run things, and
how to approach regime-analysis tasks **without needing to ask for approval on
every action** (see `.claude/settings.json`).

---

## Repository Overview

| Folder | Purpose |
|---|---|
| `Portfolio_Strategies/` | Trading strategies, backtests, regime detection (primary focus) |
| `Machine_Learning/` | ML-based price prediction models (LSTM, Prophet, k-means, …) |
| `Stock_Data/` | Scrapers for prices, fundamentals, earnings, sentiment |
| `Find_Stocks/` | Screeners that score / rank stocks |
| `Stock_Analysis/` | Pattern & statistical analysis tools |
| `Technical_Indicators/` | ~140 TA indicators (TA-Lib based) |
| `Regime_Analysis/` | Agent-ready scripts for end-to-end GMM regime analysis |

---

## Key Files for Regime Analysis

```
Portfolio_Strategies/
  financial_signal_processing.py   # Core GMM volatility-regime detection
  regime_income_strategies.py      # Bull/Neutral income strategies (full backtest)

Regime_Analysis/
  regime_agent_runner.py           # ONE-COMMAND orchestrator for agents (see below)
```

---

## How to Run Regime Analysis (one command)

```bash
# Analyse SPY over the last 5 years (saves PNG + prints metrics)
python Regime_Analysis/regime_agent_runner.py

# Custom ticker, lookback, and output folder
python Regime_Analysis/regime_agent_runner.py \
  --ticker QQQ \
  --years 3 \
  --output-dir /tmp/regime_output
```

The script is **non-interactive** (no `input()` calls, no GUI pop-ups).  
Output artefacts are written to the `--output-dir` directory.

---

## Python Environment

```bash
pip install -r requirements.txt   # install all dependencies
```

Core packages used by regime analysis:

| Package | Usage |
|---|---|
| `yfinance` | Download OHLCV price data |
| `scikit-learn` | `GaussianMixture` regime detection |
| `numpy`, `pandas` | Data manipulation |
| `matplotlib` | Chart generation |

---

## Coding Conventions

* **No `if __name__ == "__main__"` guards** in `Portfolio_Strategies/` — scripts
  execute at import time.  Use the `Regime_Analysis/regime_agent_runner.py`
  wrapper instead when calling from an agent.
* All plots are saved as `.png` files (never displayed interactively in agent
  mode — use `matplotlib.use('Agg')` if needed).
* Ticker symbols are **uppercase** throughout.

---

## How to Use Claude Agents for Regime Analysis

### What is a Claude Agent?

A Claude agent is Claude (the AI) given a set of **tools** — the ability to run
shell commands, read/write files, search the web, call APIs — and a high-level
**goal**.  Instead of answering in one shot, it plans and executes iteratively
until the task is done.

### Avoiding the "Allow" Button

By default, Claude Code asks for your approval before each tool call.  
This project ships a **`.claude/settings.json`** that pre-approves the safe
tools used for data analysis:

```json
{
  "allowedTools": ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)", "Glob(*)", "Grep(*)"]
}
```

With this in place, Claude will run analysis commands without prompting.

> **Tip — Claude Code CLI flag:**  
> You can also launch Claude Code with `--dangerously-skip-permissions` if you
> are inside a sandboxed CI environment and want zero prompts.  Do **not** use
> this flag on a machine with access to sensitive credentials or production
> systems.

### Letting an Agent Work All Day (Autonomous Mode)

You can give Claude a multi-hour task and let it run unattended:

```bash
# Example: ask Claude Code to run a full multi-asset regime sweep
claude --max-turns 200 "
Analyse the following tickers for current market regime using GMM:
SPY, QQQ, IWM, GLD, TLT, HYG, EEM.

For each ticker:
1. Run: python Regime_Analysis/regime_agent_runner.py --ticker <TICKER> --output-dir /tmp/regime_sweep
2. Collect the printed performance metrics.
3. Write a summary table to /tmp/regime_sweep/summary.md comparing
   Sharpe ratios and current regime labels across all tickers.
"
```

Claude will iterate through each ticker, execute the analysis, capture
output, and write the final summary — all without further input.

### Structuring Good Agent Prompts for Regime Analysis

| Instead of … | Ask … |
|---|---|
| "Do regime analysis" | "Run GMM regime analysis on SPY and QQQ for the last 3 years.  Save charts to /tmp/out and print Sharpe ratios." |
| "Improve my strategy" | "In `regime_income_strategies.py`, add a Bear regime (high vol) with a short-vol strategy using XIV proxy.  Backtest and compare Sharpe to the current combined strategy." |
| "Find good stocks" | "Screen the tickers in `russell3000_tickers.csv` for those currently in bull regime (GMM vol < median).  Save the list to /tmp/bull_stocks.csv." |

### Example Agent Task: Daily Regime Dashboard

```
Every trading day, at 18:00 ET:
1. python Regime_Analysis/regime_agent_runner.py --ticker SPY --output-dir /tmp/daily
2. Append current regime + Sharpe to /tmp/daily/regime_log.csv
3. If regime changed from previous day, print an alert.
```

Schedule this with `cron`, GitHub Actions, or any task scheduler.  
Claude itself can write and install the cron entry if you ask it to.

---

## Security Notes

* The `.claude/settings.json` grants Bash access.  Only run Claude agents on
  this repo inside a sandboxed environment (Docker, VM, or CI runner).
* Never store API keys in this repository.  Use environment variables or a
  secrets manager instead.
* The `--dangerously-skip-permissions` flag bypasses **all** safety checks.
  Reserve it for disposable CI environments only.
