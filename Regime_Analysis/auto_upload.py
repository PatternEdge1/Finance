#!/usr/bin/env python3
"""
YouTube Auto-Uploader for Daily Regime Dashboard Videos
Requires YouTube Data API v3 credentials
"""

import os
import sys
import json
import pickle
import datetime
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    print("Warning: Google API libraries not installed.")
    print("Install with: pip install google-auth google-auth-oauthlib google-api-python-client")

# OAuth2 scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.pickle')
CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')


class YouTubeUploader:
    """Handles YouTube video uploads with OAuth2 authentication"""
    
    def __init__(self):
        self.credentials = None
        self.youtube = None
        
    def authenticate(self):
        """Authenticate with YouTube using OAuth2"""
        # Check for existing token
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # Refresh or get new credentials
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                print("Refreshing access token...")
                self.credentials.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    print(f"Error: {CREDENTIALS_FILE} not found!")
                    print("\nTo set up YouTube upload:")
                    print("1. Go to https://console.cloud.google.com/")
                    print("2. Create a project and enable YouTube Data API v3")
                    print("3. Create OAuth 2.0 credentials (Desktop app)")
                    print("4. Download credentials and save as 'credentials.json'")
                    return False
                
                print("Starting OAuth2 flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                self.credentials = flow.run_local_server(port=0)
            
            # Save credentials for future use
            with open(TOKEN_FILE, 'wb') as token:
                pickle.dump(self.credentials, token)
            print("✓ Credentials saved")
        
        # Build YouTube service
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        print("✓ Authenticated with YouTube")
        return True
    
    def upload_video(self, video_path, metadata_path):
        """Upload video to YouTube with metadata"""
        if not self.youtube:
            print("Error: Not authenticated!")
            return None
        
        # Load metadata
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Build title
        date_str = datetime.datetime.fromisoformat(metadata['date']).strftime("%B %d, %Y")
        primary_ticker = metadata['tickers'][0]
        primary_regime = metadata['regime_summary'][primary_ticker]['regime']
        
        title = f"📊 Daily Regime Dashboard — {date_str} | Market is {primary_regime}"
        
        # Build description
        description_lines = [
            f"Daily Regime Dashboard for {date_str}",
            "",
            "📈 MARKET OVERVIEW:",
            ""
        ]
        
        for ticker, stats in metadata['regime_summary'].items():
            description_lines.append(
                f"{ticker}: ${stats['price']:.2f} ({stats['change_pct']:+.2f}%) - "
                f"{stats['regime']} regime for {stats['duration']} days"
            )
        
        description_lines.extend([
            "",
            "🎯 METHODOLOGY:",
            "- Gaussian Mixture Model (GMM) for regime detection",
            "- 22-day rolling window for statistical signals",
            "- 3-year historical lookback period",
            "",
            "📊 METRICS TRACKED:",
            "- Volatility regimes (calm vs storm)",
            "- Rolling returns and volatility",
            "- Skewness, kurtosis, and VaR",
            "- Regime duration and market breadth",
            "",
            "⚠️ DISCLAIMER:",
            "This video is for educational and informational purposes only.",
            "Not financial advice. Always do your own research.",
            "",
            "#stocks #trading #investing #volatility #SPY #technicalanalysis"
        ])
        
        description = "\n".join(description_lines)
        
        # Build tags
        tags = [
            "stocks", "trading", "investing", "regime analysis",
            "volatility", "market analysis", "technical analysis",
            "SPY", "QQQ", "stock market", "finance"
        ] + metadata['tickers']
        
        # Video metadata
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': 'public',  # or 'private' or 'unlisted'
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Create media upload
        media = MediaFileUpload(
            video_path,
            mimetype='video/mp4',
            resumable=True,
            chunksize=1024*1024  # 1MB chunks
        )
        
        print(f"\nUploading video: {os.path.basename(video_path)}")
        print(f"Title: {title}")
        print(f"Size: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
        
        # Execute upload with resumable support
        request = self.youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"  Upload progress: {progress}%", end='\r')
        
        print("\n✓ Upload complete!")
        
        video_id = response['id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        
        print(f"Video ID: {video_id}")
        print(f"Video URL: {video_url}")
        
        return video_url


def main():
    """Main execution"""
    if not YOUTUBE_API_AVAILABLE:
        print("\nError: Required libraries not installed!")
        return 1
    
    print("=" * 60)
    print("YouTube Auto-Uploader")
    print("=" * 60)
    
    # Get video path from command line or use today's output
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        output_dir = os.path.dirname(video_path)
    else:
        # Use today's date
        date_str = datetime.date.today().strftime("%Y-%m-%d")
        output_dir = os.path.join(BASE_DIR, 'output', date_str)
        video_path = os.path.join(output_dir, 'daily_regime_dashboard.mp4')
    
    metadata_path = os.path.join(output_dir, 'metadata.json')
    
    # Check files exist
    if not os.path.exists(video_path):
        print(f"Error: Video not found: {video_path}")
        return 1
    
    if not os.path.exists(metadata_path):
        print(f"Error: Metadata not found: {metadata_path}")
        return 1
    
    # Upload
    uploader = YouTubeUploader()
    
    if not uploader.authenticate():
        return 1
    
    video_url = uploader.upload_video(video_path, metadata_path)
    
    if video_url:
        print("\n" + "=" * 60)
        print("✓ SUCCESS! Video uploaded to YouTube.")
        print("=" * 60)
        return 0
    else:
        print("\n✗ Upload failed!")
        return 1


if __name__ == '__main__':
    sys.exit(main())
