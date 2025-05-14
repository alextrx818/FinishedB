#!/usr/bin/env python3
"""
alert_counter_test.py

Test the alert counters and show alerts in reverse chronological order (newest first).
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
    
    # Create different types of loggers to test the global counter
    ou3_logger = setup_alert_logger("OU3")
    goal_logger = setup_alert_logger("GOAL")
    matchend_logger = setup_alert_logger("MATCHEND")
    
    # Log a series of 15 alerts with different loggers
    print("\nGenerating 15 test alerts across different categories...")
    log_lines = []
    
    # Generate 15 alerts with different loggers and timestamps
    for i in range(1, 16):
        # Select logger based on alert type pattern
        if i % 3 == 0:
            logger = goal_logger
            alert_type = "GOAL"
            notice = f"Goal scored! Current score: {i//3}-{i//4}"
            match_id = f"GOAL-MATCH-{i:03d}"
            line_value = 2.5
        elif i % 5 == 0:
            logger = matchend_logger
            alert_type = "MATCHEND"
            notice = f"Match ended with score: {i//5}-{i//7}"
            match_id = f"END-MATCH-{i:03d}"
            line_value = 2.0
        else:
            logger = ou3_logger
            alert_type = "OU3"
            line_value = 3.0 + ((i % 7) * 0.2)
            notice = f"O/U line = {line_value:.1f} (threshold: 3.0)"
            match_id = f"OU3-MATCH-{i:03d}"
        
        # Create match and format summary
        test_match = create_test_match(match_id, line_value)
        match_summary = format_match_summary(test_match)
        
        # Log the alert
        log_alert_with_match_summary(
            logger,
            match_id,
            notice,
            match_summary
        )
        
        # Get current alert count
        alert_num, total_alerts = get_alert_count(logger.name)
        
        # Add to log lines for display
        timestamp = datetime.now()
        log_entry = {
            "num": i,
            "timestamp": timestamp.strftime("%I:%M:%S %p"),
            "alert_type": alert_type,
            "match_id": match_id,
            "notice": notice,
            "alert_num": alert_num,
            "total_alerts": total_alerts
        }
        log_lines.append(log_entry)
        
        print(f"Alert #{i}: {alert_type} - Alert #{alert_num} of {total_alerts}")
        time.sleep(0.5)  # Short delay between alerts
    
    # Display alerts in reverse order (newest first)
    print("\n===== ALERTS IN REVERSE CHRONOLOGICAL ORDER (NEWEST FIRST) =====")
    print("-" * 80)
    print(f"{'#':^3} | {'ALERT #':^7} | {'TOTAL':^5} | {'TYPE':^8} | {'TIME':^12} | NOTICE")
    print("-" * 80)
    
    for entry in reversed(log_lines):
        print(f"{entry['num']:3d} | #{entry['alert_num']:5d} | {entry['total_alerts']:5d} | {entry['alert_type']:8s} | {entry['timestamp']:12s} | {entry['notice']}")
    
    # Display counter file content
    if os.path.exists(counter_file):
        print("\n===== ALERT COUNTER FILE CONTENTS =====")
        with open(counter_file, 'r') as f:
            counter_data = json.load(f)
            print(json.dumps(counter_data, indent=2))
    
    print("\nTest complete. All alerts logged successfully.")

if __name__ == "__main__":
    main()
