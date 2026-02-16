#!/usr/bin/env python3
"""
Unit tests for Daily Regime Dashboard components
Tests core functionality with mocked data
"""

import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from daily_regime_video import RegimeAnalyzer, ChartGenerator, VoiceoverGenerator

def create_mock_price_data(days=252, start_price=100):
    """Create synthetic price data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    # Create realistic price movement with volatility regimes
    returns = np.random.randn(days) * 0.01
    # Add some volatility clusters
    returns[100:150] *= 2.5  # High volatility period
    returns[200:220] *= 3.0  # Another storm period
    
    prices = start_price * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'Open': prices * 0.99,
        'High': prices * 1.01,
        'Low': prices * 0.98,
        'Close': prices,
        'Adj Close': prices,
        'Volume': np.random.randint(10000000, 50000000, days)
    }, index=dates)
    
    return df

def test_regime_analyzer():
    """Test RegimeAnalyzer with mocked data"""
    print("=" * 60)
    print("TEST: RegimeAnalyzer")
    print("=" * 60)
    
    # Create analyzer
    analyzer = RegimeAnalyzer(['SPY', 'QQQ'])
    
    # Mock data
    analyzer.data['SPY'] = create_mock_price_data(days=252 * 3, start_price=450)
    analyzer.data['QQQ'] = create_mock_price_data(days=252 * 3, start_price=350)
    
    print("✓ Mock data created")
    
    # Analyze
    regime_data = analyzer.analyze_all()
    
    assert 'SPY' in regime_data, "SPY not in regime data"
    assert 'QQQ' in regime_data, "QQQ not in regime data"
    
    for ticker, data in regime_data.items():
        print(f"\n{ticker}:")
        print(f"  Regime: {data['current_regime']}")
        print(f"  Price: ${data['current_price']:.2f}")
        print(f"  Change: {data['price_change_pct']:+.2f}%")
        print(f"  Volatility: {data['current_vol']:.2f}%")
        print(f"  Duration: {data['regime_duration']} days")
        
        # Validate data structure
        assert data['current_regime'] in ['CALM', 'STORM'], "Invalid regime"
        assert data['current_price'] > 0, "Invalid price"
        assert data['current_vol'] > 0, "Invalid volatility"
        assert data['regime_duration'] > 0, "Invalid duration"
        assert len(data['labels']) > 0, "No labels"
        
    print("\n✓ RegimeAnalyzer test passed")
    return regime_data

def test_chart_generator(regime_data):
    """Test ChartGenerator with regime data"""
    print("\n" + "=" * 60)
    print("TEST: ChartGenerator")
    print("=" * 60)
    
    output_dir = '/tmp/regime_test'
    os.makedirs(output_dir, exist_ok=True)
    
    generator = ChartGenerator(regime_data, output_dir)
    
    # Generate all frames
    frames = generator.generate_all_frames()
    
    assert len(frames) == 6, f"Expected 6 frames, got {len(frames)}"
    
    for i, frame in enumerate(frames, 1):
        assert os.path.exists(frame), f"Frame {i} not created"
        file_size = os.path.getsize(frame)
        print(f"  Frame {i}: {os.path.basename(frame)} ({file_size/1024:.1f} KB)")
        assert file_size > 1000, f"Frame {i} too small"
    
    print("\n✓ ChartGenerator test passed")
    return frames

def test_voiceover_generator(regime_data):
    """Test VoiceoverGenerator"""
    print("\n" + "=" * 60)
    print("TEST: VoiceoverGenerator")
    print("=" * 60)
    
    output_dir = '/tmp/regime_test'
    
    generator = VoiceoverGenerator(regime_data, output_dir)
    
    # Test script generation (no network needed)
    scripts = generator.generate_scripts()
    
    assert len(scripts) == 6, f"Expected 6 scripts, got {len(scripts)}"
    
    for i, script in enumerate(scripts, 1):
        print(f"  Script {i}: {len(script)} chars")
        assert len(script) > 20, f"Script {i} too short"
    
    print("\n✓ VoiceoverGenerator test passed")
    print("  (Audio generation skipped - requires network)")
    return scripts

def test_color_scheme():
    """Test that color scheme is properly defined"""
    print("\n" + "=" * 60)
    print("TEST: Color Scheme")
    print("=" * 60)
    
    from daily_regime_video import COLORS
    
    required_colors = ['bg', 'card', 'text', 'calm', 'storm', 'green', 'orange', 'border']
    
    for color in required_colors:
        assert color in COLORS, f"Missing color: {color}"
        assert COLORS[color].startswith('#'), f"Invalid color format: {COLORS[color]}"
        print(f"  {color}: {COLORS[color]}")
    
    print("\n✓ Color scheme test passed")

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("DAILY REGIME DASHBOARD - UNIT TESTS")
    print("=" * 60)
    
    try:
        # Test 1: Color scheme
        test_color_scheme()
        
        # Test 2: Regime analyzer
        regime_data = test_regime_analyzer()
        
        # Test 3: Chart generator
        frames = test_chart_generator(regime_data)
        
        # Test 4: Voiceover generator
        scripts = test_voiceover_generator(regime_data)
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 60)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(run_all_tests())
