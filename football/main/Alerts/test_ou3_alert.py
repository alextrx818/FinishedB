#!/usr/bin/env python3
# test_ou3_alert.py - Test script for OU3 alert with mock data

import os
import sys
import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

# Setup path so imports work correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Before importing, let's create simple mocks for the dependencies
# These are normally imported from combined_match_summary
def get_eastern_time():
    return datetime.now(ZoneInfo("America/New_York"))

def format_odds_display(formatted_odds):
    return "Odds display mock"

def summarize_environment(env):
    return ["Environment summary mock"]

def get_status_description(status_id):
    return f"Status {status_id}"

def transform_odds(raw_odds, odds_type=None):
    return []

API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p %Z"

# Now define these in the modules that expect them
import sys
modules_to_patch = {
    'combined_match_summary': {
        'get_eastern_time': get_eastern_time,
        'format_odds_display': format_odds_display,
        'summarize_environment': summarize_environment,
        'get_status_description': get_status_description,
        'transform_odds': transform_odds,
        'API_DATETIME_FORMAT': API_DATETIME_FORMAT
    }
}

for module_name, attrs in modules_to_patch.items():
    if module_name not in sys.modules:
        sys.modules[module_name] = type(module_name, (), {})()
    for attr_name, attr_value in attrs.items():
        setattr(sys.modules[module_name], attr_name, attr_value)

# Now we can import our target modules
from OU3 import OverUnderAlert

# Define mock_match first so it can be used in the mock functions
# Mock a match with a high O/U line to trigger the alert
mock_match = {
    "match_id": "test123",
    "status_id": 3,  # Halftime
    "status": "Halftime",
    "home_team": {"name": "Test Home Team"},
    "away_team": {"name": "Test Away Team"},
    "competition": {"name": "Test League", "country": "Test Country", "id": "test-comp"},
    "score": {"home": 1, "away": 1, "home_ht": 1, "away_ht": 1},
    "odds": {
        "markets": [
            {
                "type": "OVER_UNDER",
                "line": "4.5"  # High O/U line to trigger the alert
            }
        ]
    },
    "environment": {
        "stadium": "Test Stadium",
        "weather": {"temperature": 20, "condition": "Clear"}
    }
}

# Mock the external functions used by alerter_main
def mock_fetch_and_cache():
    """Mock function to return test data"""
    return {"matches": [mock_match]}

def mock_merge_all(data):
    """Mock function to return matches"""
    return data.get("matches", [])

# Add these to sys.modules
sys.modules['pure_json_fetch_cache'] = type('pure_json_fetch_cache', (), {})()
sys.modules['pure_json_fetch_cache'].fetch_and_cache = mock_fetch_and_cache

sys.modules['merge_logic'] = type('merge_logic', (), {})()
sys.modules['merge_logic'].merge_all = mock_merge_all

# Now we can import AlerterMain
from alerter_main import AlerterMain

# Disable actual Telegram sending
def mock_send_notification(message):
    print(f"MOCK NOTIFICATION: {message}")

import alerter_main
alerter_main.send_notification = mock_send_notification

# mock_match is defined above

# Remove any existing OU3.logger file to see if it gets recreated
logger_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OU3.logger")
if os.path.exists(logger_path):
    os.remove(logger_path)
    print(f"Removed existing {logger_path}")
    print("This demonstrates AlerterMain's ability to automatically create a new logger")
else:
    print("No existing OU3.logger found - AlerterMain will create one automatically when triggered")

# Set up alerts with OU3
alerts = [OverUnderAlert(threshold=3.0)]  # Will trigger for our 4.5 line
  
# Initialize and run the alerter
print("Testing OU3 alert with mock data...")
manager = AlerterMain(alerts=alerts)
manager.run()

# Check if the logger file was created
if os.path.exists(logger_path):
    print(f"\nSUCCESS: {logger_path} was created!")
    with open(logger_path, 'r') as f:
        print("\nLogger contents:")
        print(f.read())
else:
    print(f"\nFAILURE: {logger_path} was not created!")
