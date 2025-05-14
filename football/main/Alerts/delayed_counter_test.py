#!/usr/bin/env python3
"""
delayed_counter_test.py

Test the alert counters with 10-second delays between each alert.
"""

import os
import sys
import time
import logging
import json
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import formatting utilities
from formatting_utils import (
    setup_alert_logger, 
    log_alert_with_match_summary,
    get_alert_count,
    ALERT_COUNTER_FILE
)
from Alerts.alerter_main import format_match_summary

def create_test_match(match_id, line_value):
    """Create a test match with the specified parameters"""
    return {
        "id": match_id,
        "competition": {"name": "LaLiga", "country": "Spain", "id": "comp-test"},
        "home_team": {"name": "Barcelona"},
        "away_team": {"name": "Real Madrid"},
        "score": {"home": 1, "away": 1, "home_ht": 0, "away_ht": 0},
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
            "temperature": "74.0°F",
            "humidity": "55%",
            "wind": "6.2 mph"
        }
    }

def main():
    # Reset the alert counters
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    counter_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "alert_counters.json"
    )
    
    # Delete existing counter file if it exists
    if os.path.exists(counter_file):
        os.remove(counter_file)
        print(f"Deleted existing counter file: {counter_file}")
    
    # Create OU3 logger
    ou3_logger = setup_alert_logger("OU3")
    
    # Remove previous log files
    ou3_log_file = os.path.join(alerts_dir, "OU3.logger")
    if os.path.exists(ou3_log_file):
        os.remove(ou3_log_file)
        print(f"Removed existing log file: {ou3_log_file}")
    
    print("\nGenerating 5 OU3 alerts with 10-second delays between each...")
    
    # Generate 5 OU3 alerts with 10-second delays
    for i in range(1, 6):
        # Create line value
        line_value = 3.0 + (i * 0.3)
        match_id = f"OU3-DELAYED-{i:03d}"
        notice = f"O/U line = {line_value:.1f} (threshold: 3.0)"
        
        # Create match and format summary
        test_match = create_test_match(match_id, line_value)
        match_summary = format_match_summary(test_match)
        
        # Get current time before logging
        current_time = datetime.now().strftime("%I:%M:%S %p")
        
        # Log the alert
        log_alert_with_match_summary(
            ou3_logger,
            match_id,
            notice,
            match_summary
        )
        
        # Get alert count
        alert_num, total_alerts = get_alert_count("OU3")
        
        print(f"Alert #{i} logged at {current_time} - OU3 Alert #{alert_num} of {total_alerts}")
        
        # Only delay if not the last alert
        if i < 5:
            print(f"Waiting 10 seconds...")
            time.sleep(10)
    
    # Display counter file content
    if os.path.exists(counter_file):
        print("\n===== ALERT COUNTER FILE CONTENTS =====")
        with open(counter_file, 'r') as f:
            counter_data = json.load(f)
            print(json.dumps(counter_data, indent=2))
    
    # Show OU3.logger content
    print("\n===== OU3.LOGGER CONTENTS (LAST 10 LINES) =====")
    print("-" * 80)
    with open(ou3_log_file, 'r') as f:
        lines = f.readlines()
        for line in lines[-10:]:
            print(line.strip())
    print("-" * 80)
    
    print("\nTest complete. All alerts logged successfully with 10-second delays.")

if __name__ == "__main__":
    main()
