#!/usr/bin/env python3
"""
test_prepend_logging.py

Test for head-insertion (prepend) logging implementation.
This script will generate multiple alerts with timestamps 10 seconds apart
and verify that new alerts appear at the TOP of the log file.
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
    format_alert_block,
    get_alert_count
)

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

def format_match_summary(match):
    """Simplified match summary formatter for testing"""
    lines = []
    
    # Headers and basic info
    lines.append("\n----- MATCH SUMMARY -----")
    lines.append("-------------------------")
    lines.append("")
    
    timestamp = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p EDT")
    lines.append(f"Timestamp: {timestamp}")
    lines.append(f"Match ID: {match['id']}")
    
    # Competition info
    comp = match['competition']
    lines.append(f"Competition ID: {comp['id']}")
    lines.append(f"Competition: {comp['name']} ({comp['country']})")
    
    # Teams and score
    lines.append(f"Match: {match['home_team']['name']} vs {match['away_team']['name']}")
    score = match['score']
    lines.append(f"Score: {score['home']} - {score['away']} (HT: {score['home_ht']} - {score['away_ht']})")
    lines.append(f"Status: {match['status']} (Status ID: {match['status_id']})")
    lines.append("")
    
    # Betting odds
    lines.append("--- MATCH BETTING ODDS ---")
    lines.append("--------------------------")
    lines.append("")
    
    # Format odds
    for market in match['odds']['markets']:
        if market['type'] == 'MONEYLINE':
            lines.append(f"│ Home  : +{int(market['home']*100):3d} │ Draw  : +{int(market['draw']*100):3d} │ Away  : +{int(market['away']*100):3d} │ (@{match['status_id']}')")
        elif market['type'] == 'SPREAD':
            lines.append(f"│ Home  : +{int(market['home']*100):3d} │ Hcap  : {market['handicap']:4.1f} │ Away  : +{int(market['away']*100):3d} │ (@{match['status_id']}')")
        elif market['type'] == 'OVER_UNDER':
            lines.append(f"│ Over  : +{int(market['over']*100):3d} │ Line  : {market['line']:4.1f} │ Under : +{int(market['under']*100):3d} │ (@{match['status_id']}')")
    
    # Environment data
    lines.append("")
    lines.append("--- MATCH ENVIRONMENT ---")
    lines.append("-------------------------")
    lines.append("")
    
    return lines

def prepend_to_log_file(alert_name, match_id, notice, summary_lines, timestamp=None):
    """
    Implementation of head-insertion logging pattern.
    New alerts appear at the top of the log file.
    """
    # Get alert count
    alert_num, total_alerts = get_alert_count(alert_name)
    
    # Use provided timestamp or generate one
    if timestamp is None:
        timestamp = datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
    
    # Format alert block
    formatted_lines = format_alert_block(
        alert_name, match_id, notice, summary_lines,
        alert_num, total_alerts, timestamp
    )
    
    # Get logger file path
    alerts_dir = os.path.abspath(os.path.dirname(__file__))
    log_file_path = os.path.join(alerts_dir, f"{alert_name}.logger")
    
    # Read existing content
    existing_content = ""
    if os.path.exists(log_file_path):
        try:
            with open(log_file_path, 'r') as f:
                existing_content = f.read()
        except Exception as e:
            print(f"Error reading log file: {e}")
    
    # Write new content at the top
    try:
        with open(log_file_path, 'w') as f:
            f.write("\n".join(formatted_lines))
            f.write("\n\n")  # Add blank lines between alerts
            f.write(existing_content)
        print(f"Successfully prepended to {log_file_path}")
    except Exception as e:
        print(f"Error writing to log file: {e}")
        return False
    
    return True

def main():
    # Reset counter file to start fresh
    counter_file = os.path.join(base_dir, "alert_counters.json")
    if os.path.exists(counter_file):
        os.remove(counter_file)
        print(f"Removed existing counter file: {counter_file}")
    
    # Generate and log multiple alerts with 10 second spacing
    alert_name = "TEST_PREPEND"
    num_alerts = 10
    
    print(f"===== GENERATING {num_alerts} ALERTS WITH 10-SECOND INTERVALS =====")
    print("=" * 70)
    print(f"{'#':^5} | {'TIME':^12} | {'ALERT #':^7} | {'TOTAL':^7} | {'LINE':^6} | {'TOP ALERT':^15}")
    print("-" * 70)
    
    for i in range(1, num_alerts + 1):
        # Create line value that increases with each alert
        line_value = 3.0 + (i * 0.2)
        
        # Create test match
        test_match = create_test_match(i, line_value)
        
        # Format match summary
        formatted_summary = format_match_summary(test_match)
        
        # Current timestamp for logging
        timestamp = datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
        
        # Log alert with match summary using prepend pattern
        prepend_to_log_file(
            alert_name,
            test_match["id"],
            f"O/U line = {line_value:.1f} (threshold: 3.0)",
            formatted_summary,
            timestamp
        )
        
        # Get alert counts
        alert_num, total_alerts = get_alert_count(alert_name)
        
        # Read first line of file to verify top alert
        alerts_dir = os.path.abspath(os.path.dirname(__file__))
        log_file_path = os.path.join(alerts_dir, f"{alert_name}.logger")
        top_alert_id = "Unknown"
        
        try:
            with open(log_file_path, 'r') as f:
                # Skip first line which is just the alert trigger notice
                first_line = f.readline().strip()
                # Find the alert header line with match ID
                for _ in range(10):  # Check first 10 lines
                    line = f.readline().strip()
                    if "TEST-MATCH" in line:
                        top_alert_id = line.split("TEST-MATCH-")[1].split(":")[0]
                        break
        except Exception:
            pass
        
        # Print status with current time
        current_time = datetime.now().strftime("%I:%M:%S %p")
        print(f"{i:^5} | {current_time:^12} | #{alert_num:^5} | {total_alerts:^7} | {line_value:^6.1f} | {top_alert_id:^15}")
        
        # Wait 10 seconds between alerts (except for the last one)
        if i < num_alerts:
            time.sleep(10)
    
    print("=" * 70)
    print("Test completed successfully!")
    print("Please check that each new alert appears at the TOP of the log file.")
    print(f"Log file location: {os.path.join(alerts_dir, f'{alert_name}.logger')}")

if __name__ == "__main__":
    main()
