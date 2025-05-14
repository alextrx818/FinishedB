#!/usr/bin/env python3
"""
update_ou3_format.py

Update the OU3.logger file to use the new numbering system format.
"""

import os
import sys
import logging

# Add parent directory to path to import formatting_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the formatting utilities
from formatting_utils import (
    log_alert_with_match_summary,
    setup_alert_logger,
    format_moneyline_odds,
    format_handicap_odds,
    format_overunder_odds,
    MATCH_SUMMARY_HEADER,
    BETTING_ODDS_HEADER,
    ENVIRONMENT_HEADER,
    API_DATETIME_FORMAT,
    get_eastern_time
)

def main():
    # Clear existing OU3.logger file
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    ou3_logger_file = os.path.join(alerts_dir, "OU3.logger")
    
    if os.path.exists(ou3_logger_file):
        print(f"Removing existing {ou3_logger_file}")
        os.remove(ou3_logger_file)
    
    # Set up the logger
    logger = setup_alert_logger("OU3")
    
    # Create odds display lines
    ml_odds = format_moneyline_odds("1.40", "2.90", "3.50", "52")
    hc_odds = format_handicap_odds("1.25", "-0.5", "1.80", "52")
    ou_odds = format_overunder_odds("1.60", "4.5", "2.40", "52")
    
    # Create match summary
    match_summary = [
        "",
        MATCH_SUMMARY_HEADER,
        MATCH_SUMMARY_UNDERLINE,
        "",
        f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}",
        "Match ID: TEST-45678",
        "Competition ID: comp-laliga",
        "Competition: LaLiga (Spain)",
        "Match: Barcelona vs Real Madrid",
        "Score: 1 - 1 (HT: 0 - 0)",
        "Status: Second Half (Status ID: 4)",
        "",
        BETTING_ODDS_HEADER,
        BETTING_ODDS_UNDERLINE,
        "",
        ml_odds,
        hc_odds,
        ou_odds,
        "",
        ENVIRONMENT_HEADER,
        ENVIRONMENT_UNDERLINE,
        "",
        "Temperature: 74.0°F",
        "Humidity: 55%",
        "Wind: 6.2 mph"
    ]
    
    # Log the alert with match summary
    log_alert_with_match_summary(
        logger,
        "TEST-45678",
        "O/U line = 4.5 (threshold: 3.0)",
        match_summary
    )
    
    print(f"\nUpdated OU3.logger with new format!")
    
    # Display the contents of the OU3.logger file
    print("\nContents of OU3.logger (first 10 lines):")
    print("-" * 60)
    try:
        with open(ou3_logger_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:10]):
                print(line.strip())
    except Exception as e:
        print(f"Error reading OU3.logger: {e}")
    print("-" * 60)

if __name__ == "__main__":
    main()
