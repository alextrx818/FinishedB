#!/usr/bin/env python3
"""
alert_numbering_test.py

Test the new alert numbering system that shows "#X of Y" for alerts triggered during the day.
This demonstrates how alerts will be numbered and tracked across multiple triggers.
"""

import os
import sys
import logging
import time
from datetime import datetime

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
    API_DATETIME_FORMAT
)

def create_sample_match_summary():
    """Create a sample match summary for testing"""
    # Create betting odds lines
    ml_odds = format_moneyline_odds("1.95", "3.50", "4.00", "4")
    hc_odds = format_handicap_odds("1.80", "-1.0", "2.10", "4")
    ou_odds = format_overunder_odds("1.90", "3.5", "2.00", "4")
    
    # Create basic match summary
    summary = [
        "",
        MATCH_SUMMARY_HEADER,
        f"Timestamp: {datetime.now().strftime(API_DATETIME_FORMAT)}",
        "Match ID: TEST-123",
        "Competition ID: comp-test",
        "Competition: Test League (Test Country)",
        "Match: Test Home vs Test Away",
        "Score: 2 - 1 (HT: 1 - 0)",
        "Status: In Progress (45')",
        "",
        ml_odds,
        hc_odds,
        ou_odds,
        "",
        "--- MATCH ENVIRONMENT ---",
        "Temperature: 68.0°F",
        "Humidity: 60%",
        "Wind: 5.0 mph"
    ]
    
    return summary

def test_alert_numbering():
    """Test the alert numbering system by creating multiple alerts"""
    print("\n=== TESTING ALERT NUMBERING SYSTEM ===")
    print("Creating multiple alerts to demonstrate the numbering system...")
    
    # Create three different alert types
    alert_types = ["OU3", "GOAL", "MATCHEND"]
    
    for alert_type in alert_types:
        # Setup logger
        logger = setup_alert_logger(alert_type)
        
        # Create multiple alerts for each type
        for i in range(2):  # Create 2 alerts of each type
            # Customize notice based on alert type
            if alert_type == "OU3":
                notice = f"O/U line = 3.5 (threshold: 3.0)"
            elif alert_type == "GOAL":
                notice = f"Goal scored! New score: 2-1"
            else:
                notice = f"Match has ended with final score: 2-1"
            
            # Log the alert with match summary
            match_id = f"TEST-{alert_type}-{i+1}"
            print(f"Logging {alert_type} alert #{i+1} for match {match_id}...")
            log_alert_with_match_summary(
                logger,
                match_id,
                notice,
                create_sample_match_summary()
            )
            
            # Add a small delay to separate alerts
            time.sleep(0.5)
    
    # Get the counter file location
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    counter_file = os.path.join(alerts_dir, "alert_counters.json")
    
    print("\nAlert counter file created at:")
    print(f"  {counter_file}")
    
    # Show the contents of the counter file
    try:
        import json
        with open(counter_file, 'r') as f:
            counters = json.load(f)
        
        print("\nAlert counters for today:")
        today = datetime.now().strftime("%Y-%m-%d")
        print(json.dumps(counters[today], indent=2))
        
        total = sum(counters[today].values())
        print(f"\nTotal alerts today: {total}")
    except Exception as e:
        print(f"Error reading counter file: {e}")
    
    # Show the log files
    print("\nGenerated logger files:")
    for alert_type in alert_types:
        log_file = os.path.join(alerts_dir, f"{alert_type}.logger")
        if os.path.exists(log_file):
            print(f"  {log_file}")
            
            # Show the header from the most recent alert
            print("\nMost recent alert header from", alert_type)
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if "ALERT TRIGGERED" in line:
                        print("  " + lines[i-1].strip())  # Print the === line
                        print("  " + line.strip())        # Print the alert line
                        print("  " + lines[i+1].strip())  # Print the === line
                        break
            print()
    
    print("\n✅ Test complete!")
    print("The alerts now include a numbering system showing '#X of Y' before 'ALERT TRIGGERED'")
    print("and a timestamp after the alert name.")

if __name__ == "__main__":
    test_alert_numbering()
