#!/usr/bin/env python3
# raw_json_test.py - Test the new match summary formatting with raw JSON

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

# Import the alerter_main and its dependencies
from OU3 import OverUnderAlert
from alerter_main import (
    format_match_summary,
    send_notification,
    AlerterMain
)

# Sample raw JSON data - structure similar to what would come from the API
raw_json_data = {
    "matches": [
        {
            "match_id": "12345",
            "id": "12345",  # Some systems use 'id' instead of 'match_id'
            "status_id": 3,  # 3 = Halftime
            "status": "Half-time",
            "home_team": {
                "id": "team_1001",
                "name": "Barcelona FC",
                "short_name": "BAR",
                "country": "Spain"
            },
            "away_team": {
                "id": "team_1002",
                "name": "Real Madrid",
                "short_name": "RMA",
                "country": "Spain"
            },
            "competition": {
                "id": "comp_10",
                "name": "La Liga",
                "country": "Spain"
            },
            "score": {
                "home": 2,
                "away": 1,
                "home_ht": 2,
                "away_ht": 0
            },
            "odds": {
                "markets": [
                    {
                        "type": "MONEYLINE",
                        "home": 2.10,
                        "draw": 3.40,
                        "away": 3.80
                    },
                    {
                        "type": "SPREAD",
                        "handicap": -0.75,
                        "home": 2.05,
                        "away": 1.95
                    },
                    {
                        "type": "OVER_UNDER",
                        "line": "3.5",
                        "over": 1.85,
                        "under": 2.05
                    }
                ]
            },
            "environment": {
                "stadium": "Camp Nou",
                "capacity": 99354,
                "city": "Barcelona",
                "country": "Spain",
                "weather": {
                    "temperature": 22,
                    "condition": "Clear",
                    "humidity": 65,
                    "wind_speed": 8
                },
                "pitch": {
                    "condition": "Excellent",
                    "type": "Grass"
                }
            }
        },
        {
            "match_id": "67890",
            "status_id": 2,  # 2 = First Half
            "status": "First Half",
            "home_team": {
                "id": "team_2001",
                "name": "Bayern Munich",
                "short_name": "BAY",
                "country": "Germany"
            },
            "away_team": {
                "id": "team_2002",
                "name": "Borussia Dortmund",
                "short_name": "DOR",
                "country": "Germany"
            },
            "competition": {
                "id": "comp_20",
                "name": "Bundesliga",
                "country": "Germany"
            },
            "score": {
                "home": 1,
                "away": 0,
                "home_ht": 0,
                "away_ht": 0
            },
            "odds": {
                "markets": [
                    {
                        "type": "MONEYLINE",
                        "home": 1.85,
                        "draw": 3.60,
                        "away": 4.50
                    },
                    {
                        "type": "SPREAD",
                        "handicap": -1.0,
                        "home": 2.00,
                        "away": 1.90
                    },
                    {
                        "type": "OVER_UNDER",
                        "line": "2.5",
                        "over": 1.90,
                        "under": 2.00
                    }
                ]
            },
            "environment": {
                "stadium": "Allianz Arena",
                "capacity": 75000,
                "city": "Munich",
                "country": "Germany",
                "weather": {
                    "temperature": 15,
                    "condition": "Light Rain",
                    "humidity": 80,
                    "wind_speed": 12
                },
                "pitch": {
                    "condition": "Good",
                    "type": "Grass"
                }
            }
        }
    ]
}

# Mock the required functions to avoid external dependencies
def mock_send_notification(message):
    """Mock notification to avoid actual Telegram sends"""
    print("\n=== MOCK NOTIFICATION WOULD BE SENT ===")
    print(message)
    print("=======================================\n")

# Override the real notification function
send_notification = mock_send_notification

# ----------------------------------------------------------------------
# TEST 1: Test direct use of format_match_summary function
# ----------------------------------------------------------------------
def test_direct_formatting():
    """Test the format_match_summary function directly"""
    print("\n" + "=" * 80)
    print("TEST 1: DIRECT FORMATTING FUNCTION TEST")
    print("=" * 80)
    
    # Get first match
    match = raw_json_data["matches"][0]
    
    print("Formatting match:")
    print(f"  ID: {match['match_id']}")
    print(f"  Teams: {match['home_team']['name']} vs {match['away_team']['name']}")
    print(f"  Status: {match['status']}")
    print(f"  Score: {match['score']['home']} - {match['score']['away']}")
    print("\nFormatted Output:")
    print("-" * 40)
    
    # Use the formatting function
    formatted_lines = format_match_summary(match)
    for line in formatted_lines:
        print(line)

# ----------------------------------------------------------------------
# TEST 2: Test OU3 alert with formatted match summary
# ----------------------------------------------------------------------
def test_ou3_alert():
    """Test the OU3 alert with a match that should trigger it"""
    print("\n" + "=" * 80)
    print("TEST 2: OU3 ALERT WITH FORMATTED MATCH SUMMARY")
    print("=" * 80)
    
    # Get the match with the high O/U line (3.5)
    match = raw_json_data["matches"][0]
    
    print(f"Testing OU3 alert with match {match['match_id']}")
    print(f"Over/Under line: {match['odds']['markets'][2]['line']}")
    print(f"OU3 threshold: 3.0")
    
    # Create and test the alert
    ou3_alert = OverUnderAlert(threshold=3.0)
    result = ou3_alert.check(match)
    
    if result:
        print("\nALERT TRIGGERED 🔔")
        print("-" * 40)
        print(result)
    else:
        print("\nAlert did not trigger.")

# ----------------------------------------------------------------------
# TEST 3: Test full AlerterMain with multiple alerts
# ----------------------------------------------------------------------
def test_alerter_main():
    """Test the full AlerterMain class with our sample data"""
    print("\n" + "=" * 80)
    print("TEST 3: FULL ALERTER MAIN WITH MULTIPLE ALERTS")
    print("=" * 80)
    
    # Set up the mock data
    def mock_fetch_and_cache():
        return raw_json_data
    
    def mock_merge_all(data):
        return data.get("matches", [])
    
    # Patch the required functions
    import alerter_main
    alerter_main.fetch_and_cache = mock_fetch_and_cache
    alerter_main.merge_all = mock_merge_all
    
    # Create alerts and run the system
    alerts = [
        OverUnderAlert(threshold=3.0),  # Should trigger for match 1 (O/U 3.5)
    ]
    
    print("Running AlerterMain with 2 sample matches")
    manager = AlerterMain(alerts=alerts)
    manager.run()

# ----------------------------------------------------------------------
# Run the tests when executed directly
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # Configure a basic logger for this script
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run each test with clear separation
    test_direct_formatting()
    test_ou3_alert()
    test_alerter_main()
    
    # Success message
    print("\n" + "=" * 80)
    print("✅ All tests completed!")
    print("=" * 80)
