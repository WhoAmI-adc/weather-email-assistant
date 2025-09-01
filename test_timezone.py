#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test script to validate Beijing timezone conversion
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add the current directory to path to import the module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from weather_email_clean import WeatherEmail

def test_beijing_time():
    """Test that Beijing time conversion works correctly"""
    print("Testing Beijing time conversion...")
    
    weather_email = WeatherEmail()
    beijing_time = weather_email.get_beijing_time()
    utc_time = datetime.now(timezone.utc)
    
    print(f"Current UTC time: {utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Beijing time: {beijing_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Check that Beijing time is 8 hours ahead of UTC
    time_diff = beijing_time.replace(tzinfo=None) - utc_time.replace(tzinfo=None)
    expected_diff = timedelta(hours=8)
    
    if abs(time_diff - expected_diff) < timedelta(minutes=1):
        print("✅ Beijing time conversion is correct (8 hours ahead of UTC)")
        return True
    else:
        print(f"❌ Beijing time conversion failed. Difference: {time_diff}, Expected: {expected_diff}")
        return False

def test_monthly_greeting_logic():
    """Test the monthly greeting logic with different dates"""
    print("\nTesting monthly greeting logic...")
    
    weather_email = WeatherEmail()
    
    # Test with mock weather data
    mock_weather = {
        'current': {'temp': 25, 'text': 'sunny', 'humidity': 60, 'windScale': '2'},
        'forecast': [],
        'air_quality': None
    }
    
    # Get current Beijing time to see if we get monthly greeting
    beijing_time = weather_email.get_beijing_time()
    advice = weather_email.get_clothing_advice(mock_weather)
    
    print(f"Current Beijing date: {beijing_time.strftime('%Y-%m-%d')}")
    print(f"Day of month: {beijing_time.day}")
    
    # Check if monthly greeting is present
    monthly_greeting = None
    for item in advice:
        if "月快乐！黄雨珏同学！" in item:
            monthly_greeting = item
            break
    
    if beijing_time.day == 1:
        if monthly_greeting:
            print(f"✅ Monthly greeting correctly triggered: {monthly_greeting}")
            return True
        else:
            print("❌ Monthly greeting should be triggered but wasn't found")
            return False
    else:
        if not monthly_greeting:
            print(f"✅ Monthly greeting correctly not triggered (day {beijing_time.day})")
            return True
        else:
            print(f"❌ Monthly greeting triggered when it shouldn't be: {monthly_greeting}")
            return False

def main():
    """Run all tests"""
    print("Running timezone conversion tests...\n")
    
    test1_passed = test_beijing_time()
    test2_passed = test_monthly_greeting_logic()
    
    print(f"\nTest results:")
    print(f"Beijing time conversion: {'PASS' if test1_passed else 'FAIL'}")
    print(f"Monthly greeting logic: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())