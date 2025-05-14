#!/usr/bin/env python3
"""
Test script for the pretty-formatted alert output
"""

import os
import sys
import json
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from OU3.py
from OU3 import OverUnderAlert

# Configure root logger
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Sample test match with all the necessary data for pretty formatting
test_match = {
    "match_id": "ednm9whwke2zryo",
    "status_id": 2,  # First half
    "status": "First half",
    "home_team": {"name": "Al-Gharafa"},
    "away_team": {"name": "Al-Sadd"},
    "competition": {
        "id": "kjw2r09hlx4rz84",
        "name": "Qatar Prince Cup",
        "country": "Qatar"
    },
    "score": {
        "home": 0,
        "away": 0,
        "home_ht": 0,
        "away_ht": 0
    },
    "odds": {
        "markets": [
            {
                "type": "MONEYLINE",
                "home": 4.0,    # +300 in American odds
                "draw": 4.0,    # +300 in American odds
                "away": 1.66,   # -152 in American odds
                "minute": 4
            },
            {
                "type": "SPREAD",
                "home": 1.92,  # -109 in American odds
                "line": -0.75,
                "away": 1.87,  # -115 in American odds
                "minute": 4
            },
            {
                "type": "OVER_UNDER",
                "over": 1.92,  # -109 in American odds
                "line": 3.25,
                "under": 1.87, # -115 in American odds
                "minute": 4
            }
        ]
    },
    "environment": {
        "weather": 5,           # 5 = Foggy
        "temperature": "100.4°F",
        "humidity": "27%",
        "wind": "8.9mph",
        "pressure": "762mmHg"
    }
}

# Function to manually import alerter_main without triggering imports
def run_alert_test():
    print("\n" + "=" * 80)
    print("ALERT SYSTEM TEST WITH PRETTY FORMATTING")
    print("=" * 80)
    
    # Create and test the OU3 alert directly first
    alert = OverUnderAlert(threshold=3.0)
    result = alert.check(test_match)
    
    if result:
        print(f"\nOU3 alert triggered with message: {result}\n")
    else:
        print(f"\nOU3 alert did not trigger. Match line: {test_match['odds']['markets'][2]['line']}\n")
    
    # Save test match to a temporary JSON file
    with open('test_match.json', 'w') as f:
        json.dump([test_match], f)
    
    print("\nNow run this command to see the full pretty-formatted output:")
    print("\ncd /root/CascadeProjects/sports_bot/football/main/Alerts && python3 -c \"\"\"")
    print("import sys, os, json; sys.path.append('..')")
    print("from OU3 import OverUnderAlert")
    print("from alerter_main import AlerterMain, send_notification")
    print("with open('test_match.json') as f: matches = json.load(f)")
    print("# Mock notification to avoid actual Telegram messages")
    print("def mock_send(msg): print(f'\\nTELEGRAM MSG SENT:\\n{msg[:100]}...')")
    print("send_notification = mock_send")
    print("# Run alerter with test match")
    print("alerts = [OverUnderAlert(threshold=3.0)]")
    print("alerter = AlerterMain(alerts=alerts)")
    print("alerter.merged_matches = matches")
    print("alerter.run()")
    print("\"\"\"")
    
    print("\nYou will see the pretty-formatted match data when an alert triggers!")

if __name__ == "__main__":
    run_alert_test()
