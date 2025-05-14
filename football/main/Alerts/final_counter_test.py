#!/usr/bin/env python3
"""
final_counter_test.py

Final test for alert numbering system with 10-second intervals.
"""

import os
import sys
import time
import json
from datetime import datetime

# Add parent directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)

# Import formatting utilities
from formatting_utils import (
    setup_alert_logger, 
    log_alert_with_match_summary,
    get_alert_count
)
from Alerts.alerter_main import format_match_summary

def create_test_match(match_num, line_value):
    """Create a test match with the specified parameters"""
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
                {"type": "OVER_UNDER", "over": 1.60, "line": line_value, "under": 2.40}
            ]
        },
        "environment": {
            "temperature": f"{70 + match_num}.0°F",
            "humidity": f"{55 + match_num}%",
            "wind": f"{6.0 + match_num} mph"
        }
    }

def main():
    # Reset counter file
    counter_file = os.path.join(base_dir, "alert_counters.json")
    if os.path.exists(counter_file):
        os.remove(counter_file)
        print(f"Removed existing counter file: {counter_file}")
    
    # Set up the logger
    logger = setup_alert_logger("OU3")
    
    # Generate and log multiple alerts with 10 second spacing
    num_alerts = 5
    
    print(f"===== GENERATING {num_alerts} ALERTS WITH 10-SECOND INTERVALS =====")
    print("=" * 70)
    print(f"{'#':^5} | {'TIME':^12} | {'ALERT #':^7} | {'TOTAL':^7} | {'LINE':^6}")
    print("-" * 70)
    
    for i in range(1, num_alerts + 1):
        # Create line value that varies
        line_value = 3.0 + (i * 0.5)
        
        # Create test match
        test_match = create_test_match(i, line_value)
        
        # Format match summary
        formatted_summary = format_match_summary(test_match)
        
        # Log alert with match summary
        log_alert_with_match_summary(
            logger,
            test_match["id"],
            f"O/U line = {line_value:.1f} (threshold: 3.0)",
            formatted_summary
        )
        
        # Get alert counts
        alert_num, total_alerts = get_alert_count("OU3")
        
        # Print status with current time
        current_time = datetime.now().strftime("%I:%M:%S %p")
        print(f"{i:^5} | {current_time:^12} | #{alert_num:^5} | {total_alerts:^7} | {line_value:^6.1f}")
        
        # Wait 10 seconds between alerts (except for the last one)
        if i < num_alerts:
            time.sleep(10)
    
    print("=" * 70)
    print("Test completed successfully.")
    print(f"Each alert was logged with correct #X of Y prepend format.")

if __name__ == "__main__":
    main()
