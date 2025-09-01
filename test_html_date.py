#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the HTML date display formatting
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add the current directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather_email_clean import WeatherEmail

def test_html_date_display():
    """Test that HTML date display uses Beijing time"""
    print("Testing HTML date display...")
    
    weather_email = WeatherEmail()
    
    # Mock weather data for testing
    mock_weather = {
        'current': {
            'temp': 25,
            'text': 'Sunny',
            'humidity': 60,
            'windScale': '2',
            'windDir': '北风',
            'vis': '10'
        },
        'forecast': [],
        'air_quality': None
    }
    
    # Generate HTML content
    html_content = weather_email.format_weather_html(mock_weather)
    
    # Get Beijing time for comparison
    beijing_time = weather_email.get_beijing_time()
    expected_date = beijing_time.strftime('%Y年%m月%d日 %A')
    
    print(f"Beijing time: {beijing_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Expected date format: {expected_date}")
    
    # Check if the date appears in the HTML
    if expected_date in html_content:
        print("✅ HTML date display correctly uses Beijing time")
        return True
    else:
        print("❌ HTML date display does not use Beijing time")
        print("HTML content snippet:")
        # Find the date div in HTML
        import re
        date_match = re.search(r'<div class="date">(.*?)</div>', html_content)
        if date_match:
            print(f"Found date in HTML: {date_match.group(1)}")
        return False

def main():
    """Run HTML date test"""
    print("Testing HTML date display...\n")
    
    test_passed = test_html_date_display()
    
    print(f"\nHTML date test: {'PASS' if test_passed else 'FAIL'}")
    
    if test_passed:
        print("\n🎉 HTML date test passed!")
        return 0
    else:
        print("\n❌ HTML date test failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())