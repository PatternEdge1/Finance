# Daily Regime Dashboard Video Generator

Fully automated system that generates professional YouTube-ready videos analyzing market volatility regimes across multiple tickers using Gaussian Mixture Models (GMM).

## 📊 Overview

This system builds on the regime analysis work in `Portfolio_Strategies/financial_signal_processing.py` to produce complete ~1-minute MP4 videos daily, ready to upload to YouTube.

### What It Does

- **Fetches Data**: Downloads 3 years of historical price data for multiple tickers
- **Regime Analysis**: Uses GMM to classify market volatility into "CALM" and "STORM" regimes
- **Visual Generation**: Creates 6 professional chart frames (1920x1080, dark theme)
- **Voiceover**: Generates British English narration using Google Text-to-Speech (gTTS)
- **Video Compilation**: Combines frames and audio into a polished MP4 video
- **Metadata Tracking**: Saves JSON metadata for each run

### Default Tickers

SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLV (customizable via command line)

## 🎬 The 6 Video Scenes

1. **Title/Hook Card**: Date, regime status, market breadth, primary ticker price
2. **Primary Ticker Chart**: Price colored by regime (blue=calm, red=storm)
3. **Volatility & Returns**: Rolling 22-day metrics, annualized
4. **Regime Timeline**: Multi-ticker regime history visualization
5. **Stats Dashboard**: Comprehensive table with price, change%, regime, volatility, skew, kurtosis, VaR
6. **Trader Insights**: Dynamic recommendations based on regime, volatility, skew, kurtosis, and breadth

## 🚀 Setup

### 1. Install Dependencies

```bash
cd Regime_Analysis
pip install -r requirements.txt
```

### 2. First Run (Manual Test)

```bash
# Run with default tickers
python daily_regime_video.py

# Run with custom tickers
python daily_regime_video.py AAPL MSFT GOOGL TSLA
```

### 3. Output Structure

```
Regime_Analysis/
├── output/
│   └── YYYY-MM-DD/
│       ├── frame_1_title.png
│       ├── frame_2_price_regime.png
│       ├── frame_3_vol_returns.png
│       ├── frame_4_timeline.png
│       ├── frame_5_stats.png
│       ├── frame_6_insights.png
│       ├── audio_1.mp3
│       ├── audio_2.mp3
│       ├── ... (6 audio files)
│       ├── daily_regime_dashboard.mp4  ← Final video
│       └── metadata.json
```

## ⚙️ Automation (Windows Task Scheduler)

### Setup Task Scheduler

1. Open Task Scheduler (`taskschd.msc`)
2. Create New Task (not Basic Task)
3. **General**:
   - Name: "Daily Regime Dashboard"
   - Run whether user is logged on or not
4. **Triggers**:
   - Daily at 7:00 PM (after market close)
5. **Actions**:
   - Start a program: `C:\path\to\Regime_Analysis\schedule_daily.bat`
   - Start in: `C:\path\to\Regime_Analysis`
6. **Settings**:
   - Allow task to be run on demand: Yes
   - Stop if runs longer than: 1 hour

### Batch File Configuration

Edit `schedule_daily.bat` to:
- Activate your Python environment (conda/venv)
- Customize tickers if needed
- Enable YouTube auto-upload (optional)

## 📤 YouTube Auto-Upload (Optional)

### Setup

1. **Enable YouTube Data API v3**:
   - Go to https://console.cloud.google.com/
   - Create a project
   - Enable YouTube Data API v3
   - Create OAuth 2.0 credentials (Desktop app)
   - Download credentials as `credentials.json` and place in `Regime_Analysis/`

2. **Install Google API Libraries**:
   ```bash
   pip install google-auth google-auth-oauthlib google-api-python-client
   ```

3. **First Upload (Manual)**:
   ```bash
   python auto_upload.py
   ```
   - Browser will open for OAuth consent
   - Token saved to `token.pickle` for future automated uploads

4. **Enable in Batch File**:
   - Uncomment YouTube upload section in `schedule_daily.bat`

### Upload Features

- **Title**: `📊 Daily Regime Dashboard — {date} | Market is {REGIME}`
- **Description**: Detailed regime breakdown for all tickers, methodology, metrics, disclaimer
- **Tags**: stocks, trading, investing, regime analysis, volatility, SPY, etc.
- **Privacy**: Public (configurable in `auto_upload.py`)
- **Resumable Upload**: Handles network interruptions

## 🎨 Styling & Theme

### Dark Theme Colors
- Background: `#0d1117` (GitHub dark)
- Cards: `#161b22`
- Text: `#c9d1d9`
- Calm regime: `#58a6ff` (blue)
- Storm regime: `#f85149` (red)
- Positive: `#3fb950` (green)
- Warning: `#f0883e` (orange)

### Video Specs
- Resolution: 1920x1080 (Full HD)
- Frame rate: 24 fps
- Codec: libx264 (H.264)
- Audio: AAC

## 🔗 Connection to Existing Code

This system extends `Portfolio_Strategies/financial_signal_processing.py`:

**Original Code**:
```python
# GMM regime detection on single ticker
vol = rs.rolling(22).std()
labels = GaussianMixture(2).fit_predict(vol.values.reshape(-1,1))
prices[labels==0].plot(style='bo', alpha=0.2)  # Calm
prices[labels==1].plot(style='ro', alpha=0.2)  # Storm
```

**This System**:
- Scales to multiple tickers
- Adds comprehensive statistics (skew, kurtosis, VaR)
- Generates professional visualizations
- Adds voiceover narration
- Produces YouTube-ready MP4 videos
- Fully automated via Task Scheduler

## 📊 Key Metrics Explained

### Regime (CALM vs STORM)
- Detected via GMM on rolling 22-day volatility
- **CALM**: Lower volatility regime (blue) → Trend-following strategies
- **STORM**: Higher volatility regime (red) → Mean-reversion strategies

### Rolling Window (22 days ≈ 1 trading month)
- **Volatility**: Standard deviation of returns (annualized %)
- **Returns**: Mean returns (annualized %)
- **Skewness**: Distribution asymmetry (< 0 = downside risk)
- **Kurtosis**: Fat tails indicator (> 3 = expect outliers)

### Value at Risk (VaR95)
- Expected maximum loss at 95% confidence level
- Calculated from historical return distribution

### Regime Duration
- Number of consecutive days in current regime
- Helps assess regime stability

## 🛠️ Troubleshooting

### "No module named 'moviepy'"
```bash
pip install moviepy
```

### "gTTS Connection Error"
- Check internet connection (gTTS requires online access)
- Try again (temporary API issues)

### "Font not found" warning
- System will use default font (functionality not affected)
- To use custom fonts, install TrueType fonts in system

### Video generation takes long time
- First run downloads 3 years of data
- Subsequent runs reuse cached data from yfinance
- Each video takes ~2-5 minutes depending on CPU

### Task Scheduler not running
- Check Windows Event Viewer → Task Scheduler logs
- Ensure Python is in PATH or batch file activates environment
- Test batch file manually first

## 📝 Customization

### Change Tickers
```bash
python daily_regime_video.py AAPL MSFT GOOGL TSLA AMZN
```

### Change Lookback Period
Edit `daily_regime_video.py`:
```python
LOOKBACK_YEARS = 5  # Default is 3
```

### Change Rolling Window
```python
ROLLING_WINDOW = 44  # Default is 22 (approximately 2 months)
```

### Change Video Duration
Adjust voiceover scripts in `VoiceoverGenerator.generate_scripts()`

### Change Color Theme
Modify `COLORS` dictionary in `daily_regime_video.py`

## 📦 Dependencies

### Required
- **numpy**: Numerical computations
- **pandas**: Data manipulation
- **yfinance**: Market data download
- **scikit-learn**: GMM implementation
- **matplotlib**: Chart generation
- **moviepy**: Video compilation
- **gTTS**: Text-to-speech voiceover
- **Pillow**: Image processing

### Optional (YouTube Upload)
- **google-auth**: OAuth2 authentication
- **google-auth-oauthlib**: OAuth2 flow
- **google-api-python-client**: YouTube API client

## 🎯 Use Cases

- **Daily Market Analysis**: Automated regime tracking
- **YouTube Content**: Ready-to-upload market commentary
- **Trading Research**: Historical regime patterns
- **Portfolio Management**: Regime-aware position sizing
- **Risk Management**: Volatility monitoring across sectors

## ⚠️ Disclaimer

This software is for educational and informational purposes only. It is not financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions.

## 📄 License

Follows the repository's main LICENSE file.

## 🤝 Contributing

This is part of the larger Finance repository. Contributions should align with the overall project structure and coding standards.

---

**Questions or Issues?** Open an issue in the main repository: https://github.com/PatternEdge1/Finance
