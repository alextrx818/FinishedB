#!/usr/bin/env python3
"""
multiple_alerts_test.py

Generate multiple alerts with timestamps to demonstrate the prepending rule.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import formatting utilities
from formatting_utils import setup_alert_logger, log_alert_with_match_summary
from Alerts.alerter_main import format_match_summary

def generate_match(match_num, odds_value):
    """Generate a test match with appropriate values"""
    return {
        "id": f"TEST-MATCH-{match_num:03d}",
        "competition": {"name": "LaLiga", "country": "Spain", "id": "comp-laliga"},
        "home_team": {"name": "Barcelona"},
        "away_team": {"name": "Real Madrid"},
        "score": {"home": match_num % 3, "away": (match_num + 1) % 3, "home_ht": 0, "away_ht": 0},
        "status": "Second Half",
        "status_id": 4,
        "odds": {
            "markets": [
                {"type": "MONEYLINE", "home": 1.40, "draw": 2.90, "away": 3.50},
                {"type": "SPREAD", "home": 1.25, "handicap": -0.5, "away": 1.80},
                {"type": "OVER_UNDER", "over": 1.60, "line": odds_value, "under": 2.40}
            ]
        },
        "environment": {
            "temperature": f"{match_num + 70}.0°F",
            "humidity": f"{50 + (match_num % 10)}%",
            "wind": f"{5 + (match_num % 5)}.2 mph"
        }
    }

def main():
    # Clear existing OU3.logger file
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    logger_file = os.path.join(alerts_dir, "OU3.logger")
    
    if os.path.exists(logger_file):
        os.remove(logger_file)
        print(f"Removed existing {logger_file}")
    
    # Set up a fresh logger
    logger = setup_alert_logger("OU3")
    
    # Generate and log multiple alerts with increasing timestamps
    num_alerts = 12  # Will generate 12 alerts
    spacing_seconds = 10  # Each alert is 10 seconds apart
    
    print(f"Generating {num_alerts} test alerts with {spacing_seconds} second spacing...")
    
    for i in range(1, num_alerts + 1):
        # Generate different line values
        line_value = 3.0 + (i * 0.2)  # Start at 3.2 and increase
        
        # Generate match with appropriate values
        test_match = generate_match(i, line_value)
        
        # Format match summary
        formatted_summary = format_match_summary(test_match)
        
        # Log alert with increasing timestamp
        log_alert_with_match_summary(
            logger,
            test_match["id"],
            f"O/U line = {line_value:.1f} (threshold: 3.0)",
            formatted_summary
        )
        
        print(f"Logged alert #{i} with line value {line_value:.1f}")
        
        # Sleep to simulate time passing between alerts
        if i < num_alerts:
            print(f"Waiting {spacing_seconds} seconds...")
            time.sleep(spacing_seconds)
    
    print(f"\nAll alerts logged to {logger_file}")
    print("\nFirst 10 lines of OU3.logger:")
    print("-" * 60)
    with open(logger_file, 'r') as f:
        for i, line in enumerate(f):
            if i < 10:
                print(line.strip())
    print("-" * 60)
    
    print("\nLast 10 lines of OU3.logger:")
    print("-" * 60)
    with open(logger_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(line.strip())
    print("-" * 60)

if __name__ == "__main__":
    main()
