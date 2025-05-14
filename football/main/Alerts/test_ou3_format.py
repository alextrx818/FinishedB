#!/usr/bin/env python3
"""
test_ou3_format.py

Test the formatting standards for the OU3 alert specifically.
"""

import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the core system
from Alerts.alerter_main import format_match_summary
from formatting_utils import setup_alert_logger, log_alert_with_match_summary

def main():
    # Create a test logger - specifically for OU3
    logger = setup_alert_logger("OU3")
    
    # First, clear any existing OU3 logger file
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    logger_path = os.path.join(alerts_dir, "OU3.logger")
    
    if os.path.exists(logger_path):
        os.remove(logger_path)
        print(f"Removed existing {logger_path}")
    
    # Create a test match with relevant data for OU3 alert
    test_match = {
        "id": "TEST-OU3-123",
        "competition": {
            "id": "comp-laliga",
            "name": "LaLiga", 
            "country": "Spain"
        },
        "home_team": {
            "name": "Barcelona"
        },
        "away_team": {
            "name": "Real Madrid"
        },
        "score": {
            "home": 1,
            "away": 1,
            "home_ht": 0,
            "away_ht": 0
        },
        "status": "Second Half",
        "status_id": 4,
        "odds": {
            "markets": [
                {
                    "type": "MONEYLINE",
                    "home": 1.40,
                    "draw": 2.90,
                    "away": 3.50
                },
                {
                    "type": "SPREAD",
                    "home": 1.25,
                    "handicap": -0.5,
                    "away": 1.80
                },
                {
                    "type": "OVER_UNDER",
                    "over": 1.60,
                    "line": 4.5,
                    "under": 2.40
                }
            ]
        },
        "environment": {
            "temperature": "74.0°F",
            "humidity": "55%",
            "wind": "6.2 mph"
        }
    }
    
    # Format the match summary using the core system's formatter
    match_summary = format_match_summary(test_match)
    
    # Log the alert with the formatted match summary
    log_alert_with_match_summary(
        logger,
        "TEST-OU3-123",
        "O/U line = 4.5 (threshold: 3.0)",
        match_summary
    )
    
    # Display the OU3.logger contents
    print("\nContents of OU3.logger:")
    print("-" * 60)
    with open(logger_path, 'r') as file:
        print(file.read())
    print("-" * 60)

if __name__ == "__main__":
    main()
