#!/usr/bin/env python3
"""
Simple isolated test for OU3 and alerter_main integration.
This script tests just the alert detection without external dependencies.
"""

import json
import logging
import os
from OU3 import OverUnderAlert

# Configure root logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('simple_test')

# Create sample match data for testing
def create_test_matches():
    """Create test match objects with different O/U values"""
    return [
        # Match 1: Should trigger alert (O/U = 3.5, status_id = 3)
        {
            "match_id": "123456",
            "status_id": 3,  # Halftime
            "status": "Halftime",
            "home_team": {"name": "Home Team A"},
            "away_team": {"name": "Away Team B"},
            "competition": {"name": "Test League"},
            "odds": {
                "markets": [
                    {"type": "OVER_UNDER", "line": "3.5"}
                ]
            }
        },
        # Match 2: Should NOT trigger (O/U = 2.5, below threshold)
        {
            "match_id": "234567",
            "status_id": 2,  # First Half
            "status": "1H",
            "home_team": {"name": "Home Team C"},
            "away_team": {"name": "Away Team D"},
            "competition": {"name": "Test League"},
            "odds": {
                "markets": [
                    {"type": "OVER_UNDER", "line": "2.5"}
                ]
            }
        },
        # Match 3: Should NOT trigger (status_id = 1, not active)
        {
            "match_id": "345678",
            "status_id": 1,  # Not started
            "status": "Not Started",
            "home_team": {"name": "Home Team E"},
            "away_team": {"name": "Away Team F"},
            "competition": {"name": "Test League"},
            "odds": {
                "markets": [
                    {"type": "OVER_UNDER", "line": "3.5"}
                ]
            }
        },
        # Match 4: Should trigger (O/U = 4.0, status_id = 4)
        {
            "match_id": "456789",
            "status_id": 4,  # Second Half
            "status": "2H",
            "home_team": {"name": "Home Team G"},
            "away_team": {"name": "Away Team H"},
            "competition": {"name": "Test League"},
            "odds": {
                "markets": [
                    {"type": "OVER_UNDER", "line": "4.0"}
                ]
            }
        }
    ]

def test_ou3_directly():
    """Test the OU3 alert directly"""
    logger.info("Starting direct OU3 test")
    
    # Create the alert with threshold 3.0
    alert = OverUnderAlert(threshold=3.0)
    test_matches = create_test_matches()
    
    # Test each match
    for idx, match in enumerate(test_matches):
        result = alert.check(match)
        status = "TRIGGERED ALERT" if result else "did NOT trigger"
        logger.info(f"Match {idx+1} (ID: {match.get('match_id')}, Status: {match.get('status')}, O/U: {get_ou_value(match)}): {status}")
        if result:
            logger.info(f"Alert message: {result}")
    
    logger.info("OU3 test complete - check if the alerts were triggered correctly")

def get_ou_value(match):
    """Extract the O/U value from a match for logging purposes"""
    # Try the odds.markets structure
    odds = match.get("odds", {})
    for market in odds.get("markets", []):
        if market.get("type") == "OVER_UNDER":
            try:
                return float(market.get("line"))
            except (TypeError, ValueError):
                pass
                
    # Try alternative structure
    ou = match.get("betting", {}).get("over_under", {})
    line = ou.get("line")
    try:
        return float(line)
    except (TypeError, ValueError):
        return None

if __name__ == "__main__":
    logger.info("-" * 50)
    logger.info("SIMPLE ALERT TEST - Testing OU3.py in isolation")
    logger.info("-" * 50)
    
    # Run the test
    test_ou3_directly()
    
    # Show where logs would be written
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"In production, alerts would log to: {os.path.join(alerts_dir, 'OverUnderAlert.logger')}")
    logger.info(f"In production, seen IDs would be stored in: {os.path.join(alerts_dir, 'OverUnderAlert.seen.json')}")
    logger.info("-" * 50)
