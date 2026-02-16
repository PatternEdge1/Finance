#!/usr/bin/env python3
"""
Daily Regime Dashboard Video Generator
Generates automated YouTube-ready videos with regime analysis for multiple tickers
"""

import os
import sys
import json
import datetime
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yfinance as yf
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for automation
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from sklearn.mixture import GaussianMixture
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TICKERS = ['SPY', 'QQQ', 'IWM', 'DIA', 'XLF', 'XLK', 'XLE', 'XLV']
LOOKBACK_YEARS = 3
ROLLING_WINDOW = 22
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 24

# Dark theme colors (GitHub dark theme inspired)
COLORS = {
    'bg': '#0d1117',
    'card': '#161b22',
    'text': '#c9d1d9',
    'calm': '#58a6ff',
    'storm': '#f85149',
    'green': '#3fb950',
    'orange': '#f0883e',
    'border': '#30363d'
}


class RegimeAnalyzer:
    """Fetches data and performs GMM regime analysis"""
    
    def __init__(self, tickers, lookback_years=LOOKBACK_YEARS, window=ROLLING_WINDOW):
        self.tickers = tickers
        self.lookback_years = lookback_years
        self.window = window
        self.data = {}
        self.regime_data = {}
        
    def fetch_data(self):
        """Fetch historical data for all tickers"""
        start_date = datetime.date.today() - datetime.timedelta(days=int(365.25 * self.lookback_years))
        
        print(f"Fetching data for {len(self.tickers)} tickers from {start_date}...")
        
        for ticker in self.tickers:
            try:
                yf_data = yf.download(ticker, start=start_date, progress=False)
                if not yf_data.empty:
                    # Handle MultiIndex columns from yfinance
                    if isinstance(yf_data.columns, pd.MultiIndex):
                        yf_data.columns = yf_data.columns.droplevel(1)
                    self.data[ticker] = yf_data
                    print(f"  ✓ {ticker}: {len(yf_data)} days")
                else:
                    print(f"  ✗ {ticker}: No data")
            except Exception as e:
                print(f"  ✗ {ticker}: Error - {e}")
        
        return len(self.data) > 0
    
    def analyze_ticker(self, ticker):
        """Perform regime analysis on a single ticker"""
        if ticker not in self.data:
            return None
        
        df = self.data[ticker].copy()
        prices = df['Adj Close'] if 'Adj Close' in df.columns else df['Close']
        
        # Calculate returns
        returns = prices.apply(np.log).diff(1)
        
        # Rolling signals
        rolling_mean = returns.rolling(self.window).mean()
        rolling_std = returns.rolling(self.window).std()
        rolling_skew = returns.rolling(self.window).skew()
        rolling_kurt = returns.rolling(self.window).kurt()
        
        # Volatility for regime detection
        vol = rolling_std.dropna()
        
        # GMM regime detection
        gmm = GaussianMixture(n_components=2, random_state=42)
        labels = gmm.fit_predict(vol.values.reshape(-1, 1))
        
        # Determine which label is "calm" (lower vol) and which is "storm" (higher vol)
        vol_by_label = {0: vol[labels == 0].mean(), 1: vol[labels == 1].mean()}
        calm_label = 0 if vol_by_label[0] < vol_by_label[1] else 1
        storm_label = 1 - calm_label
        
        # Reindex prices to match volatility index
        prices_aligned = prices.reindex(vol.index)
        
        # Calculate stats
        current_regime = 'CALM' if labels[-1] == calm_label else 'STORM'
        current_vol = vol.iloc[-1] * np.sqrt(252) * 100  # Annualized vol %
        current_price = prices_aligned.iloc[-1]
        prev_price = prices_aligned.iloc[-2]
        price_change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # Calculate regime duration
        regime_duration = 1
        for i in range(len(labels) - 2, -1, -1):
            if labels[i] == labels[-1]:
                regime_duration += 1
            else:
                break
        
        # Calculate VaR (95% confidence)
        returns_aligned = returns.reindex(vol.index)
        var_95 = np.percentile(returns_aligned.dropna(), 5) * 100
        
        return {
            'ticker': ticker,
            'prices': prices_aligned,
            'returns': returns_aligned,
            'vol': vol,
            'rolling_mean': rolling_mean.reindex(vol.index),
            'rolling_std': rolling_std.reindex(vol.index),
            'rolling_skew': rolling_skew.reindex(vol.index),
            'rolling_kurt': rolling_kurt.reindex(vol.index),
            'labels': labels,
            'calm_label': calm_label,
            'storm_label': storm_label,
            'current_regime': current_regime,
            'current_vol': current_vol,
            'current_price': current_price,
            'price_change_pct': price_change_pct,
            'regime_duration': regime_duration,
            'current_skew': rolling_skew.reindex(vol.index).iloc[-1],
            'current_kurt': rolling_kurt.reindex(vol.index).iloc[-1],
            'var_95': var_95
        }
    
    def analyze_all(self):
        """Analyze all tickers"""
        print("\nAnalyzing regimes...")
        for ticker in self.tickers:
            result = self.analyze_ticker(ticker)
            if result:
                self.regime_data[ticker] = result
                print(f"  ✓ {ticker}: {result['current_regime']}")
        
        return self.regime_data


class ChartGenerator:
    """Generates all chart frames for the video"""
    
    def __init__(self, regime_data, output_dir):
        self.regime_data = regime_data
        self.output_dir = output_dir
        self.frames = []
        
    def generate_all_frames(self):
        """Generate all 6 frames"""
        print("\nGenerating frames...")
        self.frames.append(self.generate_frame_1_title())
        self.frames.append(self.generate_frame_2_primary_ticker())
        self.frames.append(self.generate_frame_3_volatility_returns())
        self.frames.append(self.generate_frame_4_regime_timeline())
        self.frames.append(self.generate_frame_5_stats_table())
        self.frames.append(self.generate_frame_6_trader_insights())
        return self.frames
    
    def generate_frame_1_title(self):
        """Frame 1: Title/Hook card with date, regime status, ticker prices"""
        filepath = os.path.join(self.output_dir, 'frame_1_title.png')
        
        # Create image with PIL for better text control
        img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), COLORS['bg'])
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fall back to default if not available
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
            subtitle_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 60)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
        except:
            title_font = subtitle_font = text_font = ImageFont.load_default()
        
        # Title
        date_str = datetime.date.today().strftime("%B %d, %Y")
        draw.text((VIDEO_WIDTH//2, 200), "📊 Daily Regime Dashboard", 
                  fill=COLORS['text'], font=title_font, anchor="mm")
        draw.text((VIDEO_WIDTH//2, 320), date_str, 
                  fill=COLORS['orange'], font=subtitle_font, anchor="mm")
        
        # Market status
        primary_ticker = list(self.regime_data.keys())[0]
        primary_regime = self.regime_data[primary_ticker]['current_regime']
        regime_color = COLORS['calm'] if primary_regime == 'CALM' else COLORS['storm']
        
        storm_count = sum(1 for d in self.regime_data.values() if d['current_regime'] == 'STORM')
        total_count = len(self.regime_data)
        
        status_text = f"Market is in {primary_regime} mode"
        draw.text((VIDEO_WIDTH//2, 500), status_text, 
                  fill=regime_color, font=subtitle_font, anchor="mm")
        
        breadth_text = f"{storm_count}/{total_count} tickers in STORM"
        draw.text((VIDEO_WIDTH//2, 600), breadth_text, 
                  fill=COLORS['text'], font=text_font, anchor="mm")
        
        # Quick stats for primary ticker
        y_pos = 750
        stats_text = f"{primary_ticker}: ${self.regime_data[primary_ticker]['current_price']:.2f} "
        stats_text += f"({self.regime_data[primary_ticker]['price_change_pct']:+.2f}%)"
        draw.text((VIDEO_WIDTH//2, y_pos), stats_text, 
                  fill=COLORS['green'] if self.regime_data[primary_ticker]['price_change_pct'] > 0 else COLORS['storm'],
                  font=text_font, anchor="mm")
        
        img.save(filepath)
        print(f"  ✓ Frame 1: {filepath}")
        return filepath
    
    def generate_frame_2_primary_ticker(self):
        """Frame 2: Primary ticker price colored by regime"""
        filepath = os.path.join(self.output_dir, 'frame_2_price_regime.png')
        
        primary_ticker = list(self.regime_data.keys())[0]
        data = self.regime_data[primary_ticker]
        
        fig, ax = plt.subplots(figsize=(19.2, 10.8), facecolor=COLORS['bg'])
        ax.set_facecolor(COLORS['bg'])
        
        # Plot prices by regime (mirroring original code pattern)
        calm_prices = data['prices'][data['labels'] == data['calm_label']]
        storm_prices = data['prices'][data['labels'] == data['storm_label']]
        
        ax.plot(calm_prices.index, calm_prices.values, 'o', 
                color=COLORS['calm'], alpha=0.3, markersize=3, label='CALM')
        ax.plot(storm_prices.index, storm_prices.values, 'o', 
                color=COLORS['storm'], alpha=0.3, markersize=3, label='STORM')
        
        ax.set_title(f'{primary_ticker} Price - Volatility Regimes (GMM)', 
                     fontsize=24, color=COLORS['text'], pad=20)
        ax.set_xlabel('Date', fontsize=16, color=COLORS['text'])
        ax.set_ylabel('Price ($)', fontsize=16, color=COLORS['text'])
        ax.tick_params(colors=COLORS['text'], labelsize=12)
        ax.legend(fontsize=14, loc='upper left', facecolor=COLORS['card'], edgecolor=COLORS['border'])
        ax.grid(True, alpha=0.2, color=COLORS['border'])
        
        # Spines
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS['border'])
        
        plt.tight_layout()
        plt.savefig(filepath, facecolor=COLORS['bg'], dpi=100)
        plt.close()
        
        print(f"  ✓ Frame 2: {filepath}")
        return filepath
    
    def generate_frame_3_volatility_returns(self):
        """Frame 3: Rolling volatility + rolling returns (22-day window, annualized)"""
        filepath = os.path.join(self.output_dir, 'frame_3_vol_returns.png')
        
        primary_ticker = list(self.regime_data.keys())[0]
        data = self.regime_data[primary_ticker]
        
        fig, axes = plt.subplots(2, 1, figsize=(19.2, 10.8), facecolor=COLORS['bg'])
        
        for ax in axes:
            ax.set_facecolor(COLORS['bg'])
            ax.tick_params(colors=COLORS['text'], labelsize=12)
            for spine in ax.spines.values():
                spine.set_edgecolor(COLORS['border'])
        
        # Annualized volatility
        vol_annualized = data['vol'] * np.sqrt(252) * 100
        axes[0].plot(vol_annualized.index, vol_annualized.values, 
                     color=COLORS['orange'], linewidth=2)
        axes[0].set_title(f'{primary_ticker} Rolling Volatility (22-day, Annualized)', 
                          fontsize=20, color=COLORS['text'], pad=15)
        axes[0].set_ylabel('Volatility (%)', fontsize=14, color=COLORS['text'])
        axes[0].grid(True, alpha=0.2, color=COLORS['border'])
        
        # Annualized returns
        returns_annualized = data['rolling_mean'] * 252 * 100
        axes[1].plot(returns_annualized.index, returns_annualized.values, 
                     color=COLORS['calm'], linewidth=2)
        axes[1].axhline(y=0, color=COLORS['text'], linestyle='--', alpha=0.5)
        axes[1].set_title(f'{primary_ticker} Rolling Returns (22-day, Annualized)', 
                          fontsize=20, color=COLORS['text'], pad=15)
        axes[1].set_xlabel('Date', fontsize=14, color=COLORS['text'])
        axes[1].set_ylabel('Returns (%)', fontsize=14, color=COLORS['text'])
        axes[1].grid(True, alpha=0.2, color=COLORS['border'])
        
        plt.tight_layout()
        plt.savefig(filepath, facecolor=COLORS['bg'], dpi=100)
        plt.close()
        
        print(f"  ✓ Frame 3: {filepath}")
        return filepath
    
    def generate_frame_4_regime_timeline(self):
        """Frame 4: Regime timeline bars for all tickers"""
        filepath = os.path.join(self.output_dir, 'frame_4_timeline.png')
        
        fig, ax = plt.subplots(figsize=(19.2, 10.8), facecolor=COLORS['bg'])
        ax.set_facecolor(COLORS['bg'])
        
        tickers = list(self.regime_data.keys())
        n_tickers = len(tickers)
        
        # Get common date range
        all_dates = []
        for data in self.regime_data.values():
            all_dates.extend(data['vol'].index.tolist())
        date_range = pd.DatetimeIndex(sorted(set(all_dates)))
        
        # Plot each ticker's regime timeline
        for i, ticker in enumerate(tickers):
            data = self.regime_data[ticker]
            y_pos = n_tickers - i - 1
            
            # Create colored segments
            for j, (date, label) in enumerate(zip(data['vol'].index, data['labels'])):
                color = COLORS['calm'] if label == data['calm_label'] else COLORS['storm']
                ax.add_patch(Rectangle((j, y_pos - 0.4), 1, 0.8, 
                                       facecolor=color, edgecolor='none', alpha=0.8))
        
        ax.set_xlim(0, len(date_range))
        ax.set_ylim(-0.5, n_tickers - 0.5)
        ax.set_yticks(range(n_tickers))
        ax.set_yticklabels(tickers[::-1], fontsize=14, color=COLORS['text'])
        ax.set_xlabel('Trading Days (Recent History)', fontsize=14, color=COLORS['text'])
        ax.set_title('Regime Timeline (Blue = CALM, Red = STORM)', 
                     fontsize=24, color=COLORS['text'], pad=20)
        ax.tick_params(axis='x', colors=COLORS['text'], labelsize=10)
        ax.grid(True, axis='y', alpha=0.2, color=COLORS['border'])
        
        for spine in ax.spines.values():
            spine.set_edgecolor(COLORS['border'])
        
        plt.tight_layout()
        plt.savefig(filepath, facecolor=COLORS['bg'], dpi=100)
        plt.close()
        
        print(f"  ✓ Frame 4: {filepath}")
        return filepath
    
    def generate_frame_5_stats_table(self):
        """Frame 5: Multi-ticker dashboard stats table"""
        filepath = os.path.join(self.output_dir, 'frame_5_stats.png')
        
        # Prepare data for table
        table_data = []
        for ticker, data in self.regime_data.items():
            table_data.append([
                ticker,
                f"${data['current_price']:.2f}",
                f"{data['price_change_pct']:+.2f}%",
                data['current_regime'],
                f"{data['regime_duration']}d",
                f"{data['current_vol']:.1f}%",
                f"{data['current_skew']:.2f}",
                f"{data['current_kurt']:.2f}",
                f"{data['var_95']:.2f}%"
            ])
        
        fig, ax = plt.subplots(figsize=(19.2, 10.8), facecolor=COLORS['bg'])
        ax.axis('off')
        
        # Create table
        columns = ['Ticker', 'Price', 'Change', 'Regime', 'Duration', 'Vol', 'Skew', 'Kurt', 'VaR95']
        table = ax.table(cellText=table_data, colLabels=columns, 
                        cellLoc='center', loc='center',
                        colWidths=[0.08, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10])
        
        table.auto_set_font_size(False)
        table.set_fontsize(16)
        table.scale(1, 3)
        
        # Style header
        for i in range(len(columns)):
            cell = table[(0, i)]
            cell.set_facecolor(COLORS['card'])
            cell.set_text_props(weight='bold', color=COLORS['text'])
        
        # Style data cells
        for i in range(len(table_data)):
            regime = table_data[i][3]
            regime_color = COLORS['calm'] if regime == 'CALM' else COLORS['storm']
            
            for j in range(len(columns)):
                cell = table[(i + 1, j)]
                cell.set_facecolor(COLORS['bg'])
                
                if j == 3:  # Regime column
                    cell.set_text_props(color=regime_color, weight='bold')
                elif j == 2:  # Change column
                    change_val = float(table_data[i][2].replace('%', '').replace('+', ''))
                    color = COLORS['green'] if change_val > 0 else COLORS['storm']
                    cell.set_text_props(color=color)
                else:
                    cell.set_text_props(color=COLORS['text'])
                
                cell.set_edgecolor(COLORS['border'])
        
        ax.set_title('Market Dashboard - Current Statistics', 
                     fontsize=28, color=COLORS['text'], pad=20, y=0.98)
        
        plt.tight_layout()
        plt.savefig(filepath, facecolor=COLORS['bg'], dpi=100)
        plt.close()
        
        print(f"  ✓ Frame 5: {filepath}")
        return filepath
    
    def generate_frame_6_trader_insights(self):
        """Frame 6: Trader action card with dynamic insights"""
        filepath = os.path.join(self.output_dir, 'frame_6_insights.png')
        
        # Analyze market conditions
        storm_count = sum(1 for d in self.regime_data.values() if d['current_regime'] == 'STORM')
        total_count = len(self.regime_data)
        storm_breadth = storm_count / total_count
        
        primary_ticker = list(self.regime_data.keys())[0]
        primary_data = self.regime_data[primary_ticker]
        
        avg_vol = np.mean([d['current_vol'] for d in self.regime_data.values()])
        avg_skew = np.mean([d['current_skew'] for d in self.regime_data.values()])
        avg_kurt = np.mean([d['current_kurt'] for d in self.regime_data.values()])
        
        # Generate insights
        insights = []
        
        # Regime-based strategy
        if storm_breadth > 0.5:
            insights.append("⚡ High volatility regime detected")
            insights.append("→ Consider mean-reversion strategies")
            insights.append("→ Tighter stops recommended")
        else:
            insights.append("📈 Calm regime dominates")
            insights.append("→ Trend-following strategies favored")
            insights.append("→ Normal position sizing appropriate")
        
        # Volatility guidance
        if avg_vol > 25:
            insights.append(f"⚠ Elevated volatility ({avg_vol:.1f}%)")
            insights.append("→ Reduce position size by 25-50%")
        elif avg_vol < 15:
            insights.append(f"✓ Low volatility ({avg_vol:.1f}%)")
            insights.append("→ Standard position sizing OK")
        
        # Skew analysis
        if avg_skew < -0.5:
            insights.append(f"📉 Negative skew ({avg_skew:.2f})")
            insights.append("→ Downside tail risk elevated")
            insights.append("→ Consider protective puts")
        elif avg_skew > 0.5:
            insights.append(f"📈 Positive skew ({avg_skew:.2f})")
            insights.append("→ Upside potential biased")
        
        # Kurtosis (fat tails)
        if avg_kurt > 3:
            insights.append(f"⚠ Fat tails detected (kurt={avg_kurt:.1f})")
            insights.append("→ Expect potential outsized moves")
        
        # Create image with PIL
        img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT), COLORS['bg'])
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
            text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except:
            title_font = text_font = ImageFont.load_default()
        
        # Title
        draw.text((VIDEO_WIDTH//2, 150), "💡 Trader Focus", 
                  fill=COLORS['text'], font=title_font, anchor="mm")
        
        # Draw insights
        y_pos = 300
        for insight in insights:
            draw.text((VIDEO_WIDTH//2, y_pos), insight, 
                      fill=COLORS['text'], font=text_font, anchor="mm")
            y_pos += 70
        
        img.save(filepath)
        print(f"  ✓ Frame 6: {filepath}")
        return filepath


class VoiceoverGenerator:
    """Generates voiceover scripts and audio files"""
    
    def __init__(self, regime_data, output_dir):
        self.regime_data = regime_data
        self.output_dir = output_dir
        self.audio_files = []
        
    def generate_all_audio(self):
        """Generate audio for all scenes"""
        print("\nGenerating voiceovers...")
        scripts = self.generate_scripts()
        
        for i, script in enumerate(scripts, 1):
            filepath = os.path.join(self.output_dir, f'audio_{i}.mp3')
            try:
                tts = gTTS(text=script, lang='en', tld='co.uk')  # British English
                tts.save(filepath)
                self.audio_files.append(filepath)
                print(f"  ✓ Audio {i}: {len(script)} chars")
            except Exception as e:
                print(f"  ✗ Audio {i}: Error - {e}")
                # Create silent audio as fallback
                self.audio_files.append(None)
        
        return self.audio_files
    
    def generate_scripts(self):
        """Generate scripts for all scenes"""
        primary_ticker = list(self.regime_data.keys())[0]
        primary_data = self.regime_data[primary_ticker]
        
        storm_count = sum(1 for d in self.regime_data.values() if d['current_regime'] == 'STORM')
        total_count = len(self.regime_data)
        
        date_str = datetime.date.today().strftime("%B %d, %Y")
        
        scripts = [
            # Scene 1: Title
            f"Welcome to today's Daily Regime Dashboard for {date_str}. "
            f"The market is currently in {primary_data['current_regime']} mode, "
            f"with {storm_count} out of {total_count} tickers showing elevated volatility.",
            
            # Scene 2: Price chart
            f"Looking at {primary_ticker}, we can see the price action colored by volatility regime. "
            f"Blue dots represent calm periods, while red dots indicate storm conditions. "
            f"The current price is ${primary_data['current_price']:.2f}, "
            f"{primary_data['price_change_pct']:+.2f} percent for the day.",
            
            # Scene 3: Volatility and returns
            f"The rolling 22-day volatility is currently {primary_data['current_vol']:.1f} percent annualized. "
            f"Rolling returns show the momentum profile over the same window.",
            
            # Scene 4: Timeline
            f"The regime timeline shows how all tickers have transitioned between calm and storm states. "
            f"This helps identify market-wide volatility patterns.",
            
            # Scene 5: Stats table
            f"The dashboard displays key statistics for all tickers: "
            f"current prices, daily changes, regime status, duration, volatility, "
            f"skewness, kurtosis, and value at risk.",
            
            # Scene 6: Trader insights
            f"For traders, the key takeaway is: "
            f"{'Focus on mean-reversion strategies and tighter risk controls' if storm_count > total_count/2 else 'Trend-following strategies are favorable with standard position sizing'}. "
            f"Monitor volatility closely and adjust your approach accordingly."
        ]
        
        return scripts


class VideoCompiler:
    """Compiles frames and audio into final MP4 video"""
    
    def __init__(self, frames, audio_files, output_dir):
        self.frames = frames
        self.audio_files = audio_files
        self.output_dir = output_dir
        
    def compile(self):
        """Compile video with frames and audio"""
        print("\nCompiling video...")
        
        clips = []
        
        for i, (frame_path, audio_path) in enumerate(zip(self.frames, self.audio_files), 1):
            try:
                # Determine duration from audio or use default
                if audio_path and os.path.exists(audio_path):
                    audio_clip = AudioFileClip(audio_path)
                    duration = audio_clip.duration
                else:
                    duration = 5.0  # Default 5 seconds if no audio
                    audio_clip = None
                
                # Create image clip
                img_clip = ImageClip(frame_path, duration=duration)
                
                # Add audio if available
                if audio_clip:
                    img_clip = img_clip.set_audio(audio_clip)
                
                clips.append(img_clip)
                print(f"  ✓ Scene {i}: {duration:.1f}s")
                
            except Exception as e:
                print(f"  ✗ Scene {i}: Error - {e}")
        
        if not clips:
            print("  ✗ No clips to compile!")
            return None
        
        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Output path
        output_path = os.path.join(self.output_dir, 'daily_regime_dashboard.mp4')
        
        # Write video file
        print(f"\nWriting video to: {output_path}")
        final_video.write_videofile(
            output_path,
            fps=VIDEO_FPS,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile=os.path.join(self.output_dir, 'temp_audio.m4a'),
            remove_temp=True,
            logger=None  # Suppress moviepy verbose output
        )
        
        print(f"✓ Video saved: {output_path}")
        print(f"  Duration: {final_video.duration:.1f}s")
        print(f"  Size: {os.path.getsize(output_path) / (1024*1024):.1f} MB")
        
        return output_path


def save_metadata(regime_data, output_dir, video_path):
    """Save metadata about the run"""
    metadata = {
        'date': datetime.date.today().isoformat(),
        'timestamp': datetime.datetime.now().isoformat(),
        'tickers': list(regime_data.keys()),
        'video_path': video_path,
        'regime_summary': {
            ticker: {
                'regime': data['current_regime'],
                'price': float(data['current_price']),
                'change_pct': float(data['price_change_pct']),
                'volatility': float(data['current_vol']),
                'duration': int(data['regime_duration'])
            }
            for ticker, data in regime_data.items()
        }
    }
    
    metadata_path = os.path.join(output_dir, 'metadata.json')
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\n✓ Metadata saved: {metadata_path}")
    return metadata_path


def main():
    """Main execution"""
    print("=" * 60)
    print("Daily Regime Dashboard Video Generator")
    print("=" * 60)
    
    # Get tickers from command line or use defaults
    if len(sys.argv) > 1:
        tickers = sys.argv[1:]
    else:
        tickers = DEFAULT_TICKERS
    
    print(f"\nTickers: {', '.join(tickers)}")
    
    # Create output directory with today's date
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    output_dir = os.path.join(BASE_DIR, 'output', date_str)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")
    
    # Step 1: Analyze regimes
    analyzer = RegimeAnalyzer(tickers)
    if not analyzer.fetch_data():
        print("\n✗ Failed to fetch data!")
        return 1
    
    regime_data = analyzer.analyze_all()
    if not regime_data:
        print("\n✗ Failed to analyze regimes!")
        return 1
    
    # Step 2: Generate charts
    chart_gen = ChartGenerator(regime_data, output_dir)
    frames = chart_gen.generate_all_frames()
    
    # Step 3: Generate voiceovers
    voice_gen = VoiceoverGenerator(regime_data, output_dir)
    audio_files = voice_gen.generate_all_audio()
    
    # Step 4: Compile video
    compiler = VideoCompiler(frames, audio_files, output_dir)
    video_path = compiler.compile()
    
    if not video_path:
        print("\n✗ Failed to compile video!")
        return 1
    
    # Step 5: Save metadata
    save_metadata(regime_data, output_dir, video_path)
    
    print("\n" + "=" * 60)
    print("✓ SUCCESS! Video generation complete.")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
