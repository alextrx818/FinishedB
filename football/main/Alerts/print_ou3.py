#!/usr/bin/env python3
"""
Simple script to test the OU3 formatting standards.
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import formatting utilities
from formatting_utils import setup_alert_logger, log_alert_with_match_summary
from Alerts.alerter_main import format_match_summary

def main():
    # Get the absolute path for the logger file
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    logger_file = os.path.join(alerts_dir, "OU3.logger")
    
    # Setup the logger - this creates OU3.logger in the Alerts directory
    logger = setup_alert_logger("OU3")
    
    # Create a test match with OU3-specific data
    test_match = {
        "id": "MATCH-12345",
        "competition": {"name": "LaLiga", "country": "Spain", "id": "comp-laliga"},
        "home_team": {"name": "Barcelona"},
        "away_team": {"name": "Real Madrid"},
        "score": {"home": 1, "away": 1, "home_ht": 0, "away_ht": 0},
        "status": "Second Half",
        "status_id": 4,
        "odds": {
            "markets": [
                {"type": "MONEYLINE", "home": 1.40, "draw": 2.90, "away": 3.50},
                {"type": "SPREAD", "home": 1.25, "handicap": -0.5, "away": 1.80},
                {"type": "OVER_UNDER", "over": 1.60, "line": 4.5, "under": 2.40}
            ]
        },
        "environment": {
            "temperature": "74.0°F",
            "humidity": "55%",
            "wind": "6.2 mph"
        }
    }
    
    # Format the match summary
    formatted_summary = format_match_summary(test_match)
    
    # Log the alert with the formatted match summary
    log_alert_with_match_summary(
        logger, 
        "MATCH-12345", 
        "O/U line = 4.5 (threshold: 3.0)",
        formatted_summary
    )
    
    # Print a direct console message showing the formatted alert
    print("\n==== Formatted OU3 Alert ====")
    current_time = datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
    print("=" * 80)
    print(f"#X of Y ALERT TRIGGERED: OU3 @ {current_time}")
    print("=" * 80)
    print()
    
    for line in formatted_summary:
        print(line)
    
    # Now check if the logger file exists and show its contents
    if os.path.exists(logger_file):
        print(f"\nLogger file created at: {logger_file}")
        print("-" * 60)
        with open(logger_file, 'r') as f:
            print(f.read())
        print("-" * 60)
    else:
        print(f"\nWARNING: Logger file not found at expected location: {logger_file}")
        print("Looking for OU3.logger in other locations...")
        os.system("find /root/CascadeProjects/sports_bot/football -name OU3.logger")

if __name__ == "__main__":
    main()
