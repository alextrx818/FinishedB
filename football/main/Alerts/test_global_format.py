#!/usr/bin/env python3
"""
test_global_format.py

Test the global formatting standards as implemented in alerter_main.py.
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
    # Create a test logger
    logger = setup_alert_logger("TEST_FORMAT")
    
    # Create a test match
    test_match = {
        "id": "TEST-FORMAT-123",
        "competition": {
            "id": "comp-test",
            "name": "Test League",
            "country": "Test Country"
        },
        "home_team": {
            "name": "Home Team"
        },
        "away_team": {
            "name": "Away Team"
        },
        "score": {
            "home": 2,
            "away": 1,
            "home_ht": 1,
            "away_ht": 0
        },
        "status": "In Progress",
        "status_id": 3,
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
        "TEST-FORMAT-123",
        "Global format test alert",
        match_summary
    )
    
    # Display the output location
    print(f"Global formatting test complete. Check the output at: Alerts/TEST_FORMAT.logger")

if __name__ == "__main__":
    main()
