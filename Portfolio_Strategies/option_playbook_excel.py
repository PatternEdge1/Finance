"""
option_playbook_excel.py
------------------------
Generates a fully formatted Excel workbook (HF_Option_Income_Playbook.xlsx)
containing a professional Hedge Fund-grade Option Income Strategy Playbook.

The workbook contains 6 sheets:
    1_Regime_Identification  — 39 indicators across 8 categories
    2_Master_Playbook        — 18 strategy rows mapping Regime x VIX x IVR
    3_Entry_Checklist        — 15-point pre-trade checklist
    4_Position_Sizing        — NAV limits and tail hedge requirements per regime
    5_Exit_Roll_Rules        — 15 universal exit/roll rules with priority tags
    6_Composite_Scoring      — 5-level composite scoring model

Usage:
    python Portfolio_Strategies/option_playbook_excel.py

Output:
    HF_Option_Income_Playbook.xlsx  (saved in the current working directory)
"""

import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

# ── Color Palette ──────────────────────────────────────────────────
GREEN_DARK   = "1E8449"
GREEN_LIGHT  = "D5F5E3"
YELLOW_LIGHT = "FEF9E7"
ORANGE_LIGHT = "FDEBD0"
RED_LIGHT    = "FADBD8"
RED_DARK     = "E74C3C"
BLUE_LIGHT   = "D6EAF8"
GREY_LIGHT   = "F2F3F4"
WHITE        = "FFFFFF"
HEADER_FONT  = "FFFFFF"
DARK_TEXT    = "1C1C1C"

thin = Side(style="thin", color="BDBDBD")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

def header_fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def cell_fill(hex_color):
    return PatternFill("solid", fgColor=hex_color)

def style_header_row(ws, row_num, num_cols, bg=GREEN_DARK, fg=HEADER_FONT, sz=11):
    for c in range(1, num_cols + 1):
        cell = ws.cell(row=row_num, column=c)
        cell.fill      = header_fill(bg)
        cell.font      = Font(bold=True, color=fg, size=sz)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = border

def style_data_row(ws, row_num, num_cols, bg=WHITE):
    for c in range(1, num_cols + 1):
        cell = ws.cell(row=row_num, column=c)
        cell.fill      = cell_fill(bg)
        cell.font      = Font(color=DARK_TEXT, size=10)
        cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
        cell.border    = border

def set_col_widths(ws, widths):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

def write_title(ws, title, num_cols):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=num_cols)
    cell = ws.cell(row=1, column=1, value=title)
    cell.fill      = header_fill("1A5276")
    cell.font      = Font(bold=True, color=HEADER_FONT, size=13)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

# ══════════════════════════════════════════════════════════════════════
# SHEET 1 — REGIME IDENTIFICATION
# ══════════════════════════════════════════════════════════════════════
ws1 = wb.active
ws1.title = "1_Regime_Identification"
write_title(ws1, "REGIME IDENTIFICATION TABLE — SPX / VIX / TECHNICALS / MACRO", 5)

headers = ["Category", "Indicator", "Tool / Source", "BULL / Sell Premium Signal", "BEAR / Risk-Off Signal"]
for col, h in enumerate(headers, 1):
    ws1.cell(row=2, column=col, value=h)
style_header_row(ws1, 2, len(headers))
ws1.row_dimensions[2].height = 22
ws1.freeze_panes = "A3"

rows_s1 = [
    ("VOLATILITY", "VIX Level",                    "CBOE",                   "VIX < 17",                            "VIX > 20",                            GREEN_LIGHT),
    ("VOLATILITY", "VIX vs 20-day MA",             "CBOE",                   "VIX < its own 20-day MA",             "VIX > its own 20-day MA",             GREEN_LIGHT),
    ("VOLATILITY", "VIX Term Structure",           "CBOE Futures",           "Contango (front < back month)",       "Backwardation (front > back month)",  GREEN_LIGHT),
    ("VOLATILITY", "VVIX (Vol of Vol)",            "CBOE",                   "VVIX < 90 (stable vol regime)",       "VVIX > 100 (vol is unstable)",        GREEN_LIGHT),
    ("VOLATILITY", "VIX9D vs VIX",                "CBOE",                   "VIX9D < VIX (calm near-term)",        "VIX9D > VIX (imminent event risk)",   GREEN_LIGHT),
    ("VOLATILITY", "IV Rank (IVR)",               "TastyTrade / ToS",       "IVR > 50 (rich premium, sell)",       "IVR < 30 (cheap, avoid selling)",     GREEN_LIGHT),
    ("VOLATILITY", "Realized Vol vs IV (VRP)",    "Bloomberg / TastyTrade", "IV > RV by 3+ pts",                   "RV > IV (dont sell premium)",         GREEN_LIGHT),
    ("TECHNICALS", "SPX vs 200-day MA",            "SMA.py",                 "Price above 200 MA",                  "Price below 200 MA",                  YELLOW_LIGHT),
    ("TECHNICALS", "SPX 20 MA vs 50 MA",          "SMA.py",                 "20 MA > 50 MA (Golden Cross)",        "20 MA < 50 MA (Death Cross)",         YELLOW_LIGHT),
    ("TECHNICALS", "ATR (14-day)",                "avg_true_range.py",      "ATR contracting (quiet regime)",      "ATR expanding (volatile regime)",     YELLOW_LIGHT),
    ("TECHNICALS", "ROC (12-day)",                "ROC.py",                 "ROC > 0 and rising",                  "ROC < 0 and falling",                 YELLOW_LIGHT),
    ("TECHNICALS", "Bollinger Band Width",        "extended_market.py",     "Bands squeezing (low vol)",           "Bands expanding (high vol)",          YELLOW_LIGHT),
    ("TECHNICALS", "Keltner Channel",             "strong_backtest.py",     "Price in mid-upper KC",               "Price below lower KC",                YELLOW_LIGHT),
    ("TECHNICALS", "Candlestick Pattern",         "japanese_candles.py",    "Bullish Engulfing / Swing",           "Bearish Engulfing / Pinbar",          YELLOW_LIGHT),
    ("TECHNICALS", "MACD Signal",                 "macd_accuracy.py",       "MACD above signal line",              "MACD below signal line",              YELLOW_LIGHT),
    ("MACRO",      "Fed Policy Stance",           "Fed Dot Plot / FOMC",    "Cutting or Paused (risk-on)",         "Hiking or Hawkish surprise (risk-off)",ORANGE_LIGHT),
    ("MACRO",      "2Y-10Y Yield Curve",          "US Treasury / Bloomberg","Steepening / Positive slope",         "Deeply inverted (recession signal)",  ORANGE_LIGHT),
    ("MACRO",      "10Y Real Yield (TIPS)",       "FRED / Bloomberg",       "Real yield falling (equity positive)","Real yield rising sharply",           ORANGE_LIGHT),
    ("MACRO",      "DXY (USD Index)",             "Bloomberg / TradingView","USD weakening (global risk-on)",       "USD surging (liquidity stress)",       ORANGE_LIGHT),
    ("MACRO",      "CPI / PCE Surprise",          "BLS / BEA",              "In-line or below (no Fed shock)",     "Hot print = vol spike risk",          ORANGE_LIGHT),
    ("MACRO",      "ISM Manufacturing PMI",       "ISM",                    "PMI > 50 and rising",                 "PMI < 50 and falling",                ORANGE_LIGHT),
    ("CREDIT",     "HY Credit Spreads (HYG/JNK)","Bloomberg / FRED",       "Spreads tightening (<350 bps)",       "Spreads widening (>450 bps = stress)",RED_LIGHT),
    ("CREDIT",     "IG Credit Spreads (LQD)",    "Bloomberg / FRED",       "Spreads stable / tightening",         "Spreads widening rapidly",            RED_LIGHT),
    ("CREDIT",     "CDX IG Index",               "Markit",                 "CDX tightening",                      "CDX widening >5 bps/week",            RED_LIGHT),
    ("CREDIT",     "TED Spread",                 "Bloomberg",              "TED < 30 bps (no stress)",            "TED > 50 bps (funding stress)",       RED_LIGHT),
    ("BREADTH",    "NYSE A/D Line",              "StockCharts",            "A/D line making new highs",           "A/D diverging from SPX (red flag)",   BLUE_LIGHT),
    ("BREADTH",    "% SPX stocks above 200 MA",  "Bloomberg / Finviz",     "> 60% (broad participation)",         "< 40% (narrow/fragile rally)",        BLUE_LIGHT),
    ("BREADTH",    "Equal Weight vs Cap Weight", "RSP vs SPY ratio",       "EW outperforming (breadth strong)",   "EW underperforming (mega-cap led)",   BLUE_LIGHT),
    ("POSITIONING","COT: Non-Comm Net Futures",  "CFTC COT / COT_sentiment.py","Net long SPX futures",           "Net short SPX futures",               GREY_LIGHT),
    ("POSITIONING","Dealer Gamma (GEX)",         "SpotGamma / SqueezeMetrics","Positive GEX (dealers buy dips)", "Negative GEX (dealers sell dips)",    GREY_LIGHT),
    ("POSITIONING","COT: Lev Money Position",    "COT_sentiment.py",       "Lev money net long",                  "Lev money net short",                 GREY_LIGHT),
    ("SKEW",       "25-Delta Put Skew (1M)",     "Bloomberg / CBOE",       "Skew flat or declining",              "Skew steep (smart money hedging)",    GREEN_LIGHT),
    ("SKEW",       "Term Structure (1M vs 3M IV)","Bloomberg",             "1M IV < 3M IV (calm near term)",      "1M IV > 3M IV (event risk near-term)",GREEN_LIGHT),
    ("SENTIMENT",  "AAII Bull/Bear Survey",      "AAII",                   "Bull%-Bear% < 10 (fear/neutral)",     "Bull%-Bear% > 30 (excessive optimism)",YELLOW_LIGHT),
    ("SENTIMENT",  "CNN Fear & Greed",           "CNN Markets",            "Score 20-45 (fear = opportunity)",    "Score > 75 (greed = complacency)",    YELLOW_LIGHT),
    ("SENTIMENT",  "Put/Call Ratio (5-day avg)", "CBOE",                   "P/C < 0.80",                          "P/C > 1.20 (panic)",                  YELLOW_LIGHT),
    ("SEASONALITY","Calendar Month",             "Historical CBOE data",   "Feb Mar Apr Nov Dec (favorable)",     "Sep Oct (worst for premium sellers)", ORANGE_LIGHT),
    ("SEASONALITY","FOMC Meeting Week",          "Fed Calendar",           "Post-FOMC (vol crush)",               "Day before FOMC (vol spike risk)",    ORANGE_LIGHT),
    ("SEASONALITY","OpEx Week",                  "CBOE Calendar",          "After OpEx (vol often drops)",        "Week of OpEx (pinning + vol risk)",   ORANGE_LIGHT),
]

for i, row in enumerate(rows_s1, start=3):
    for col, val in enumerate(row[:5], 1):
        ws1.cell(row=i, column=col, value=val)
    style_data_row(ws1, i, 5, bg=row[5])
    ws1.row_dimensions[i].height = 20

set_col_widths(ws1, [14, 28, 26, 36, 36])

# ══════════════════════════════════════════════════════════════════════
# SHEET 2 — MASTER PLAYBOOK
# ══════════════════════════════════════════════════════════════════════
ws2 = wb.create_sheet("2_Master_Playbook")
write_title(ws2, "MASTER OPTION INCOME PLAYBOOK — REGIME x VIX x STRATEGY", 11)

h2 = ["Regime", "SPX Trend", "VIX Level", "IVR", "Composite Score",
      "Income Strategy", "Directional Bet", "DTE", "Position Size", "Weekly Income Target", "Stop / Exit Rule"]
for col, h in enumerate(h2, 1):
    ws2.cell(row=2, column=col, value=h)
style_header_row(ws2, 2, len(h2))
ws2.row_dimensions[2].height = 22
ws2.freeze_panes = "A3"

rows_s2 = [
    ("Bull Quiet",          "Strong above 20/50/200 MA","< 13",        "< 40", "+8 to +10", "Jade Lizard",                         "Long Call Diagonal (buy 6mo ITM, sell 30D OTM call)",   "21-30",  "75% normal", "0.75-1.0%",  "Close at 50% profit; roll if within 1% of short strike",  GREEN_LIGHT),
    ("Bull Quiet",          "Strong above 20/50/200 MA","< 13",        "< 40", "+8 to +10", "Put BWB (net credit, skewed below mkt)","Bull Call Spread (1-2% OTM, defined risk)",            "30-45",  "75% normal", "0.75-1.25%", "BWB: 75% profit; Call Spread: close at 2x loss",          GREEN_LIGHT),
    ("Bull Normal",         "Moderate above 50 & 200 MA","13-17",      "40-60","+5 to +7",  "Jade Lizard",                         "Bull Put Spread (sell below support)",                  "21-30",  "Full",       "1.0-1.5%",   "50% profit rule; stop at 200% credit loss",               GREEN_LIGHT),
    ("Bull Normal",         "Moderate above 50 & 200 MA","13-17",      "40-60","+5 to +7",  "Iron Condor (skewed wider put side)", "Long Call (30 delta 30-45 DTE) or PMCC",               "30-45",  "Full",       "1.0-1.5%",   "Roll tested leg at 21 DTE; stop condor at 2x credit",     GREEN_LIGHT),
    ("Bull Normal",         "Moderate above 50 & 200 MA","13-17",      "40-60","+5 to +7",  "Put Credit Spread (Delta 20-25 short)","Diagonal Call Spread (bullish)",                       "21-30",  "Full",       "1.0-1.5%",   "Close at 50% profit or 200% loss",                        GREEN_LIGHT),
    ("Range Bound",         "Sideways ATR flat ROC ~0",  "14-18",      "45-65","+2 to +4",  "Iron Condor (tight 0.75 SD wings)",   "Iron Fly (ATM strangle, max theta)",                   "21-30",  "Full",       "1.5-2.0%",   "Adjust if SPX breaches short strike by 0.5%; 2x credit",  YELLOW_LIGHT),
    ("Range Bound",         "Sideways ATR flat ROC ~0",  "14-18",      "45-65","+2 to +4",  "Short Strangle (hedged with far wings)","Calendar Spread (ATM long vol play)",                 "Short 14 / Long 30","Full", "1.5-2.0%", "Hard stop at 3x credit received",                        YELLOW_LIGHT),
    ("Range Bound",         "Sideways ATR flat ROC ~0",  "14-18",      "45-65","+2 to +4",  "1-1-2 Spread",                        "Double Diagonal (long outer short inner)",              "30-45",  "Full",       "1.5-2.0%",   "Close inner at 50%; hold outer for vol expansion",        YELLOW_LIGHT),
    ("Volatile Bull",       "Choppy above 200 MA only",  "18-25",      "55-75","0 to +2",   "Jade Lizard (wider put wider cushion)","Bull Put Spread (deep OTM wide cushion)",              "21-30",  "60% normal", "1.5-2.0%",   "Defined risk only; close at 50% or 200% loss",            ORANGE_LIGHT),
    ("Volatile Bull",       "Choppy above 200 MA only",  "18-25",      "55-75","0 to +2",   "Put BWB (wide 3 strikes below market)","Call Ratio Backspread (sell 1 ATM buy 2 OTM calls)",  "30-45",  "60% normal", "1.5-2.0%",   "BWB: take profit at 75%; Backspread: ride the move",       ORANGE_LIGHT),
    ("Volatile Bull",       "Choppy above 200 MA only",  "18-25",      "55-75","0 to +2",   "Big Lizard (sell ATM straddle + buy call)","Diagonal Spread (bullish bias)",                  "21-30",  "50% normal", "1.5-2.5%",   "Close Big Lizard if loss reaches 1.5x credit",            ORANGE_LIGHT),
    ("Bearish / Correction","Below 50 MA testing 200 MA","20-30",      "60-80","-1 to -4",  "Bear Call Spread",                    "Long Put Spread (buy ATM put sell lower)",              "21-30",  "50% normal", "1.0-1.5%",   "No naked shorts; spreads only; 50% profit or 200% loss",  RED_LIGHT),
    ("Bearish / Correction","Below 50 MA testing 200 MA","20-30",      "60-80","-1 to -4",  "Wide Put Spread (funds tail hedge)",   "Long Straddle or Long Put (directional)",               "30-45",  "40% normal", "0.5-1.0%",   "Tail hedge mandatory; size down 50%; stop 1.5x credit",   RED_LIGHT),
    ("Bearish / Correction","Below 50 MA testing 200 MA","20-30",      "60-80","-1 to -4",  "Call BWB (sell call sell 2 higher buy far)","Bear Call Spread (sell the rally)",              "21-30",  "40% normal", "1.0-1.5%",   "Close if SPX reverses 3% to upside",                      RED_LIGHT),
    ("High Vol / Panic",    "Erratic below all MAs",     "> 30",       "> 80", "< -5",      "NO SHORT PREMIUM - Flatten all shorts","Long Put (near ATM 30-60 DTE) or Long Straddle",       "30-60",  "20% normal", "PRESERVATION","Max loss = 1% NAV per directional bet",                    RED_DARK),
    ("High Vol / Panic",    "Erratic below all MAs",     "> 30",       "> 80", "< -5",      "Hold tail hedges (far OTM SPX puts)", "VIX Call Spread (profit from spike)",                  "30-60",  "20% normal", "HEDGING",     "Let it ride - these are your insurance",                   RED_DARK),
    ("Vol Mean Reversion",  "Post-spike VIX rolling over","25-35 falling","70-90","0 to +3", "Short Strangle post-spike (best R/R)", "Bull Put Spread (buy the dip structurally)",           "30-45",  "60% normal", "2.5-4.0%",   "Enter ONLY after VIX peaks and rolls over; 2x credit stop",BLUE_LIGHT),
    ("Vol Mean Reversion",  "Post-spike VIX rolling over","25-35 falling","70-90","0 to +3", "Iron Condor (wide wings massive premium)","Long Call Spread (OTM 45 DTE ride recovery)",      "30-45",  "60% normal", "2.5-3.5%",   "Best entry = 3-5 days after VIX peak",                    BLUE_LIGHT),
]

for i, row in enumerate(rows_s2, start=3):
    for col, val in enumerate(row[:11], 1):
        ws2.cell(row=i, column=col, value=val)
    style_data_row(ws2, i, 11, bg=row[11])
    ws2.row_dimensions[i].height = 28

set_col_widths(ws2, [18, 26, 14, 8, 14, 34, 36, 16, 12, 18, 44])

# ══════════════════════════════════════════════════════════════════════
# SHEET 3 — PRE-TRADE ENTRY CHECKLIST
# ══════════════════════════════════════════════════════════════════════
ws3 = wb.create_sheet("3_Entry_Checklist")
write_title(ws3, "PRE-TRADE ENTRY CHECKLIST - Run Before Every Trade", 4)

h3 = ["#", "Check", "Condition Required", "Tool / Source"]
for col, h in enumerate(h3, 1):
    ws3.cell(row=2, column=col, value=h)
style_header_row(ws3, 2, len(h3))
ws3.row_dimensions[2].height = 22
ws3.freeze_panes = "A3"

rows_s3 = [
    (1,  "VIX Term Structure",              "Must be in Contango to sell premium",                    "CBOE VIX Futures",          GREEN_LIGHT),
    (2,  "IVR > 50",                        "Implied vol must be rich vs. 52W range",                 "TastyTrade / ToS",          GREEN_LIGHT),
    (3,  "IV > 30D Realized Vol (VRP +ve)", "Vol risk premium must be positive",                      "Bloomberg / TastyTrade",    GREEN_LIGHT),
    (4,  "SPX above 200 MA",                "For any net short put position",                         "SMA.py",                    YELLOW_LIGHT),
    (5,  "ATR not expanding rapidly",       "ATR must be stable or contracting",                      "avg_true_range.py",         YELLOW_LIGHT),
    (6,  "ROC positive or flattening",      "Momentum must not be deeply negative",                   "ROC.py",                    YELLOW_LIGHT),
    (7,  "MACD not in bearish crossover",   "MACD above or crossing up through signal",               "macd_accuracy.py",          YELLOW_LIGHT),
    (8,  "Candlestick - no reversal signal","No bearish engulfing / pinbar at resistance",            "japanese_candles.py",       YELLOW_LIGHT),
    (9,  "COT Lev Money not aggressively short","Smart money not positioned against you",             "COT_sentiment.py",          ORANGE_LIGHT),
    (10, "HY Credit Spreads not widening",  "HYG/JNK spreads stable or tightening",                  "Bloomberg / FRED",          ORANGE_LIGHT),
    (11, "No major macro event in 7 days",  "FOMC, CPI, NFP - reduce size or skip entirely",         "Fed / BLS / BEA Calendar",  ORANGE_LIGHT),
    (12, "Dealer GEX positive",             "Positive GEX = dealers buy dips = lower realized vol",  "SpotGamma / SqueezeMetrics",ORANGE_LIGHT),
    (13, "Composite regime score > 0",      "At least neutral before selling any premium",            "Your scoring model",         RED_LIGHT),
    (14, "VIX not in backwardation",        "Front month VIX futures must be below back month",       "CBOE Futures",              RED_LIGHT),
    (15, "Not in OpEx week (for new trades)","Avoid opening new trades during OpEx week",            "CBOE Calendar",             RED_LIGHT),
]

for i, row in enumerate(rows_s3, start=3):
    for col, val in enumerate(row[:4], 1):
        ws3.cell(row=i, column=col, value=val)
    style_data_row(ws3, i, 4, bg=row[4])
    ws3.row_dimensions[i].height = 22

set_col_widths(ws3, [5, 30, 48, 28])

# ══════════════════════════════════════════════════════════════════════
# SHEET 4 — POSITION SIZING BY REGIME
# ══════════════════════════════════════════════════════════════════════
ws4 = wb.create_sheet("4_Position_Sizing")
write_title(ws4, "POSITION SIZING BY REGIME - NAV Limits & Tail Hedge Requirements", 5)

h4 = ["Regime", "VIX Level", "Max NAV in Short Premium", "Max Single Trade Size", "Tail Hedge Required"]
for col, h in enumerate(h4, 1):
    ws4.cell(row=2, column=col, value=h)
style_header_row(ws4, 2, len(h4))
ws4.row_dimensions[2].height = 22
ws4.freeze_panes = "A3"

rows_s4 = [
    ("Bull Quiet",           "< 13",         "3% NAV",  "1.0% NAV",  "Optional - 0.5% NAV in far OTM puts",       GREEN_LIGHT),
    ("Bull Normal",          "13-17",        "4% NAV",  "1.5% NAV",  "Yes - 1.0% NAV in far OTM SPX puts",        GREEN_LIGHT),
    ("Range Bound",          "14-18",        "4% NAV",  "1.5% NAV",  "Yes - 1.0% NAV in far OTM SPX puts",        YELLOW_LIGHT),
    ("Volatile Bull",        "18-25",        "2.5% NAV","1.0% NAV",  "Yes - 1.5% NAV; increase if ATR expanding", ORANGE_LIGHT),
    ("Bearish / Correction", "20-30",        "1.5% NAV","0.75% NAV", "MANDATORY - 2.0% NAV minimum",              RED_LIGHT),
    ("High Vol / Panic",     "> 30",         "0% NAV",  "0.5% NAV (long only)", "Already in - 2%+ NAV target",   RED_DARK),
    ("Vol Mean Reversion",   "25-35 falling","3% NAV",  "1.25% NAV", "Yes - 1.5% NAV; enter after VIX peaks",    BLUE_LIGHT),
]

for i, row in enumerate(rows_s4, start=3):
    for col, val in enumerate(row[:5], 1):
        ws4.cell(row=i, column=col, value=val)
    style_data_row(ws4, i, 5, bg=row[5])
    ws4.row_dimensions[i].height = 22

set_col_widths(ws4, [22, 16, 22, 22, 42])

# ══════════════════════════════════════════════════════════════════════
# SHEET 5 — EXIT & ROLL RULES
# ══════════════════════════════════════════════════════════════════════
ws5 = wb.create_sheet("5_Exit_Roll_Rules")
write_title(ws5, "UNIVERSAL EXIT & ROLL RULES - Apply in ALL Regimes", 3)

h5 = ["Rule", "Detail", "Priority"]
for col, h in enumerate(h5, 1):
    ws5.cell(row=2, column=col, value=h)
style_header_row(ws5, 2, len(h5))
ws5.row_dimensions[2].height = 22
ws5.freeze_panes = "A3"

rows_s5 = [
    ("Profit Taking",               "Close ALL income trades at 50% of max credit received - proven to improve Sharpe vs. holding to expiry",       "HIGH",   GREEN_LIGHT),
    ("Loss Stop",                   "Close at 200% of credit received. Never let a trade go to max loss",                                           "HIGH",   RED_LIGHT),
    ("Time Stop",                   "If position is at a loss at 21 DTE, roll or close - do NOT hold to expiry hoping for recovery",                "HIGH",   RED_LIGHT),
    ("Roll Rule",                   "Roll tested legs OUT in time (same strike). Never roll DOWN into more risk to chase a credit",                  "HIGH",   ORANGE_LIGHT),
    ("Regime Change Stop",          "If composite regime score drops 3+ points intraweek, reduce all short premium by 50% immediately",             "HIGH",   ORANGE_LIGHT),
    ("Weekly Drawdown Circuit Breaker","If weekly P&L hits -3% NAV, stop all new trades for the rest of that week. No exceptions",                  "HIGH",   RED_LIGHT),
    ("VIX Spike Alert",             "If VIX rises >20% in a single day, close all undefined risk positions immediately",                            "CRITICAL",RED_LIGHT),
    ("VIX Backwardation Alert",     "If VIX futures flip to backwardation, stop all new short premium. Begin flattening book",                      "CRITICAL",RED_DARK),
    ("GEX Flip Alert",              "If dealer gamma flips from positive to negative, reduce short put exposure by 50%",                            "HIGH",   ORANGE_LIGHT),
    ("Credit Spread Widening Alert","If HY spreads widen >50 bps in a week, move to defensive mode - bearish spreads + tail hedges only",          "HIGH",   RED_LIGHT),
    ("Post-FOMC Entry Rule",        "Best time to sell premium = day after FOMC (vol crush). Avoid selling premium day before FOMC",                "MEDIUM", YELLOW_LIGHT),
    ("Post-Earnings Vol Crush Rule","After major earnings seasons, IV collapses. Best window to enter diagonals and calendars",                     "MEDIUM", YELLOW_LIGHT),
    ("Tail Hedge Refresh Rule",     "Roll tail hedge (far OTM SPX puts, 90-120 DTE) every 30 days. Never let them expire without replacement",      "HIGH",   GREEN_LIGHT),
    ("Composite Score Rule",        "Re-score regime every Monday AM. If score changes by 3+ points, reassess ALL open positions that day",          "MEDIUM", YELLOW_LIGHT),
    ("Max Concurrent Structures",   "Never run more than 3 simultaneous structures in the same expiry cycle. Diversify across tenors",               "MEDIUM", GREEN_LIGHT),
]

for i, row in enumerate(rows_s5, start=3):
    for col, val in enumerate(row[:3], 1):
        ws5.cell(row=i, column=col, value=val)
    style_data_row(ws5, i, 3, bg=row[3])
    ws5.row_dimensions[i].height = 28

priority_colors = {"CRITICAL": "E74C3C", "HIGH": "E8DAEF", "MEDIUM": "D5F5E3"}
priority_font   = {"CRITICAL": "FFFFFF", "HIGH": "6C3483", "MEDIUM": "1E8449"}
for i, row in enumerate(rows_s5, start=3):
    prio = row[2]
    cell = ws5.cell(row=i, column=3)
    cell.fill      = PatternFill("solid", fgColor=priority_colors.get(prio, WHITE))
    cell.font      = Font(bold=True, color=priority_font.get(prio, DARK_TEXT), size=10)
    cell.alignment = Alignment(horizontal="center", vertical="center")

set_col_widths(ws5, [30, 80, 12])

# ══════════════════════════════════════════════════════════════════════
# SHEET 6 — COMPOSITE SCORING MODEL
# ══════════════════════════════════════════════════════════════════════
ws6 = wb.create_sheet("6_Composite_Scoring")
write_title(ws6, "COMPOSITE REGIME SCORING MODEL - Score Before Every Trade", 4)

h6 = ["Score Range", "Regime Label", "Action", "Color Code"]
for col, h in enumerate(h6, 1):
    ws6.cell(row=2, column=col, value=h)
style_header_row(ws6, 2, len(h6))
ws6.row_dimensions[2].height = 22

scores = [
    ("+7 to +10", "Strong Bull / Low Vol",       "Full size. Aggressive premium selling. Jade Lizard + BWB + Diagonal combo",  "DARK GREEN",  "1E8449", HEADER_FONT),
    ("+3 to +6",  "Mild Bull / Normal Vol",       "Normal size. Standard structures. Iron Condor, PCS, Jade Lizard",            "GREEN",       "27AE60", HEADER_FONT),
    ("0 to +2",   "Neutral / Choppy",             "Reduced size (60%). Wider wings. Defined risk only. Monitor daily",          "YELLOW",      "F4D03F", DARK_TEXT),
    ("-1 to -4",  "Volatile / Risk-Off",           "Half size (50%). Spreads only. Add tail hedge. Bear Call Spreads ok",        "ORANGE",      "E67E22", HEADER_FONT),
    ("< -5",      "Bear / Panic",                  "NO short premium. Buy premium or go flat. Activate tail hedges",             "RED",         "C0392B", HEADER_FONT),
]

for i, row in enumerate(scores, start=3):
    score, label, action, color_name, hex_color, font_color = row
    ws6.cell(row=i, column=1, value=score)
    ws6.cell(row=i, column=2, value=label)
    ws6.cell(row=i, column=3, value=action)
    ws6.cell(row=i, column=4, value=color_name)
    for col in range(1, 5):
        cell = ws6.cell(row=i, column=col)
        cell.fill      = PatternFill("solid", fgColor=hex_color)
        cell.font      = Font(bold=True, color=font_color, size=11)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border    = border
    ws6.row_dimensions[i].height = 40

ws6.cell(row=9, column=1, value="SCORING LOGIC:")
ws6.cell(row=9, column=1).font = Font(bold=True, size=11, color="1A5276")
note = ("Each indicator in the Regime Identification sheet gets +1 (bullish), 0 (neutral), or -1 (bearish). "
        "Sum across all categories. Weight Credit, Vol Surface, and Macro signals 1.5x - they LEAD price by 3-10 days. "
        "Re-score every Monday morning and after any major macro event.")
ws6.merge_cells(start_row=10, start_column=1, end_row=10, end_column=4)
cell = ws6.cell(row=10, column=1, value=note)
cell.alignment = Alignment(wrap_text=True, vertical="top")
cell.font = Font(size=10, italic=True, color="555555")
ws6.row_dimensions[10].height = 60

set_col_widths(ws6, [14, 26, 62, 16])

# ══════════════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════════════
output_path = "HF_Option_Income_Playbook.xlsx"
wb.save(output_path)
print(f"Workbook saved: {output_path}")
print("Sheets: 1_Regime_Identification | 2_Master_Playbook | 3_Entry_Checklist | 4_Position_Sizing | 5_Exit_Roll_Rules | 6_Composite_Scoring")
