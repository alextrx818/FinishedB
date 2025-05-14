#!/usr/bin/env python3
"""
formatting_standard_test.py

Test script to demonstrate the standardized formatting utilities
and verify they produce output that complies with FORMATTING_STANDARDS.md
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path to import formatting_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the formatting utilities
from formatting_utils import (
    format_moneyline_odds,
    format_handicap_odds, 
    format_overunder_odds,
    format_odds_display,
    format_environment_data,
    setup_alert_logger,
    log_alert_with_match_summary,
    get_eastern_time,
    API_DATETIME_FORMAT,
    MATCH_SUMMARY_HEADER,
    BETTING_ODDS_HEADER,
    ENVIRONMENT_HEADER
)

def test_odds_formatting():
    """Test the standardized odds formatting functions"""
    print("\n=== TESTING STANDARDIZED ODDS FORMATTING ===")
    
    # Test moneyline odds
    ml_odds = format_moneyline_odds("1.95", "3.50", "4.00", "4")
    print("\nMoneyline odds formatting:")
    print(ml_odds)
    
    # Test handicap odds
    hc_odds = format_handicap_odds("1.80", "-1.0", "2.10", "4")
    print("\nHandicap odds formatting:")
    print(hc_odds)
    
    # Test over/under odds
    ou_odds = format_overunder_odds("1.90", "3.5", "2.00", "4")
    print("\nOver/Under odds formatting:")
    print(ou_odds)
    
    # Test combined odds display
    odds_lines = [ml_odds, hc_odds, ou_odds]
    formatted_odds = format_odds_display(odds_lines)
    print("\nComplete odds section formatting:")
    print(formatted_odds)
    
    # Verify alignment
    print("\nVerifying column alignment:")
    for line in odds_lines:
        # Extract column positions for analysis
        positions = [pos for pos, char in enumerate(line) if char == "│"]
        print(f"Column positions: {positions}")
    
    return odds_lines

def test_environment_formatting():
    """Test the standardized environment formatting function"""
    print("\n=== TESTING ENVIRONMENT FORMATTING ===")
    
    # Sample environment data
    env_data = {
        "weather": 1,
        "temperature": "19°C",
        "wind": "1.8m/s",
        "humidity": "76%",
        "pressure": "762mmHg"
    }
    
    # Format environment data
    env_lines = format_environment_data(env_data)
    print("\nFormatted environment data:")
    for line in env_lines:
        print(line)
    
    return env_lines

def test_alert_logger():
    """Test the standardized alert logger setup and formatting"""
    print("\n=== TESTING ALERT LOGGER FORMATTING ===")
    
    # Create a test logger
    logger_name = "FORMAT_TEST"
    logger = setup_alert_logger(logger_name)
    
    # Create a complete match summary
    odds_lines = test_odds_formatting()
    env_lines = test_environment_formatting()
    
    # Combine into a full match summary
    match_summary = [
        "",
        MATCH_SUMMARY_HEADER,
        f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}",
        "Match ID: FORMAT-TEST-123",
        "Competition ID: comp-test",
        "Competition: Test League (Test Country)",
        "Match: Test Home vs Test Away",
        "Score: 2 - 1 (HT: 1 - 0)",
        "Status: In Progress (45')",
        ""
    ]
    
    # Add the odds and environment sections
    match_summary.extend(odds_lines)
    match_summary.append("")
    match_summary.extend(env_lines)
    
    # Log the alert with properly formatted match summary
    log_alert_with_match_summary(
        logger, 
        "FORMAT-TEST-123", 
        "Formatting standards test alert", 
        match_summary
    )
    
    # Display the location of the log file
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(alerts_dir, f"{logger_name}.logger")
    print(f"\nAlert logged to: {log_file}")
    
    # Display the contents of the log file
    print("\nLog file contents:")
    print("-" * 50)
    try:
        with open(log_file, 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"Error reading log file: {e}")
    print("-" * 50)
    
    print("\n✅ Test complete! Verify that the formatting meets the standards defined in FORMATTING_STANDARDS.md")
    
if __name__ == "__main__":
    test_alert_logger()
