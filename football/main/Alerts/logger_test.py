#!/usr/bin/env python3
# logger_test.py - Test alerter_main.py's automatic logger creation

import os
import sys
import json
import logging
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Setup path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# First, define our test environment
ALERTER_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_LOGGER_FILE = os.path.join(ALERTER_DIR, "OU3.logger")

# Clean the test environment - remove existing logger file
if os.path.exists(TEST_LOGGER_FILE):
    os.remove(TEST_LOGGER_FILE)
    print(f"* Removed existing {TEST_LOGGER_FILE}")
    print("* AlerterMain should automatically create a new logger file when an alert triggers")
else:
    print(f"* No existing {TEST_LOGGER_FILE} found")
    print("* AlerterMain will create it automatically when an alert is triggered")

# Setup path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Create mock test data
test_match = {
    "match_id": "TEST-123",
    "status_id": 3,  # Halftime
    "status": "Half-time",
    "home_team": {
        "name": "Manchester United"
    },
    "away_team": {
        "name": "Liverpool FC"
    },
    "competition": {
        "id": "comp-epl",
        "name": "English Premier League",
        "country": "England"
    },
    "score": {
        "home": 2,
        "away": 1,
        "home_ht": 2,
        "away_ht": 1
    },
    "odds": {
        "markets": [
            {
                "type": "MONEYLINE",
                "home": 1.95,
                "draw": 3.50,
                "away": 4.00
            },
            {
                "type": "SPREAD",
                "handicap": -1.0,
                "home": 1.80,
                "away": 2.10
            },
            {
                "type": "OVER_UNDER",
                "line": "3.5",
                "over": 1.90,
                "under": 2.00
            }
        ]
    },
    "environment": {
        "weather": {
            "temperature": 18,  # Celsius
            "humidity": 72,
            "wind_speed": 10
        }
    }
}

# Mock functions for combined_match_summary.py
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p %Z"

def get_eastern_time():
    return datetime.now(ZoneInfo("America/New_York"))

def get_status_description(status_id):
    statuses = {
        1: "Not started",
        2: "First half",
        3: "Half-time break",
        4: "Second half",
        5: "Finished"
    }
    return statuses.get(status_id, f"Unknown ({status_id})")

# Mock other required functions
def transform_odds(data, format_type=None):
    return []

def format_odds_display(data):
    return "No odds"

def summarize_environment(env):
    return ["No environment data"]

# Patch modules
import sys
sys.modules['combined_match_summary'] = type('MockModule', (), {})
sys.modules['combined_match_summary'].API_DATETIME_FORMAT = API_DATETIME_FORMAT
sys.modules['combined_match_summary'].get_eastern_time = get_eastern_time
sys.modules['combined_match_summary'].get_status_description = get_status_description
sys.modules['combined_match_summary'].transform_odds = transform_odds
sys.modules['combined_match_summary'].format_odds_display = format_odds_display
sys.modules['combined_match_summary'].summarize_environment = summarize_environment

# Setup more mocks
def mock_fetch_and_cache():
    return {"matches": [test_match]}

def mock_merge_all(data):
    return data.get("matches", [])

# Replace functions in sys.modules
sys.modules['pure_json_fetch_cache'] = type('MockModule', (), {})
sys.modules['pure_json_fetch_cache'].fetch_and_cache = mock_fetch_and_cache

sys.modules['merge_logic'] = type('MockModule', (), {})
sys.modules['merge_logic'].merge_all = mock_merge_all

# Now import our modules - this will use the mocks we've set up
from OU3 import OverUnderAlert
from alerter_main import AlerterMain

print("\n" + "=" * 80)
print("TESTING ALERT DETECTION & LOGGER CREATION")
print("=" * 80)
print("1. Initializing OU3 alert with threshold 3.0 (test match has 3.5)")
print("2. AlerterMain will detect the alert and create OU3.logger if needed")
print("3. The full formatted match summary will be written to OU3.logger")

# Disable real notifications and use a mock
def mock_send_notification(message):
    print("\nMOCK NOTIFICATION:")
    print("-" * 40)
    print(message)
    print("-" * 40)

import alerter_main
alerter_main.send_notification = mock_send_notification

# Create AlerterMain and run
alerts = [OverUnderAlert(threshold=3.0)]
manager = AlerterMain(alerts=alerts)
manager.run()

# Check if logger file was created
if os.path.exists(TEST_LOGGER_FILE):
    print("\n✅ SUCCESS! Logger file was automatically created at:")
    print(f"   {TEST_LOGGER_FILE}")
    print("\nLogger contents:")
    print("-" * 60)
    with open(TEST_LOGGER_FILE, 'r') as f:
        print(f.read())
else:
    print("\n❌ ERROR: Logger file was not created")
