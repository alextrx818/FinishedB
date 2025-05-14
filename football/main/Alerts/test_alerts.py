#!/usr/bin/env python3
"""
Test script for OU3 and alerter_main integration.
This script tests the alert system in isolation from the main orchestrator.
"""

import json
import logging
import os
import sys

# Add the parent directory to sys.path for imports to work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure root logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_alerts')

# Import after logger setup
from Alerts.OU3 import OverUnderAlert
from Alerts.alerter_main import AlerterMain, FutureAlert, send_notification

# Mock the send_notification function to avoid actual Telegram messages
def mock_send_notification(message):
    logger.info(f"MOCK NOTIFICATION: {message}")
    return True

# Create sample match data simulating what merge_logic.py would produce
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
        },
        # Match 5: Should NOT trigger (alternative data structure, O/U = 2.0)
        {
            "match_id": "567890",
            "status_id": 3,  # Halftime
            "status": "Halftime",
            "home": "Home Team I",
            "away": "Away Team J",
            "competition": {"name": "Test League"},
            "betting": {
                "over_under": {"line": "2.0"}
            }
        },
        # Match 6: Should trigger (alternative data structure, O/U = 5.0)
        {
            "match_id": "678901",
            "status_id": 3,  # Halftime
            "status": "Halftime",
            "home": "Home Team K",
            "away": "Away Team L",
            "competition": {"name": "Test League"},
            "betting": {
                "over_under": {"line": "5.0"}
            }
        }
    ]

def test_alerter_main():
    """Test the full AlerterMain workflow"""
    logger.info("Starting AlerterMain test")
    
    # Register alerts
    alerts = [
        OverUnderAlert(threshold=3.0),
        FutureAlert()
    ]
    
    # Create AlerterMain instance
    manager = AlerterMain(alerts=alerts)
    
    # Check that loggers were created correctly
    logger.info(f"Alert loggers created: {', '.join([alert.__class__.__name__ for alert in alerts])}")
    
    # Override the send_notification method to avoid actual Telegram messages
    import Alerts.alerter_main
    Alerts.alerter_main.send_notification = mock_send_notification
    
    # Mock the fetch and merge functions
    test_matches = create_test_matches()
    
    def mock_fetch_and_cache():
        logger.info("Mock fetch_and_cache called")
        return {"raw_matches": test_matches}
    
    def mock_merge_all(raw_data):
        logger.info(f"Mock merge_all called with {len(raw_data['raw_matches'])} matches")
        return raw_data["raw_matches"]
    
    # Override the functions in alerter_main
    import Alerts.alerter_main
    Alerts.alerter_main.fetch_and_cache = mock_fetch_and_cache
    Alerts.alerter_main.merge_all = mock_merge_all
    
    # Mock format_summary
    def mock_format_summary(match):
        return json.dumps(match, indent=2)
    
    Alerts.alerter_main.format_summary = mock_format_summary
    
    # Run the alerter
    logger.info("Running alerter_main...")
    manager.run()
    
    # Check the logs
    for alert in alerts:
        name = alert.__class__.__name__
        log_path = os.path.join(manager.alerts_dir, f"{name}.logger")
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                content = f.read()
            logger.info(f"{name} log file contains {len(content.splitlines())} lines")
        else:
            logger.warning(f"{name} log file was not created")
    
    # Check the seen IDs persistence
    for alert in alerts:
        name = alert.__class__.__name__
        seen_path = os.path.join(manager.alerts_dir, f"{name}.seen.json")
        if os.path.exists(seen_path):
            with open(seen_path, 'r') as f:
                seen_ids = json.load(f)
            logger.info(f"{name} seen IDs file contains {len(seen_ids)} match IDs")
        else:
            logger.warning(f"{name} seen IDs file was not created")
    
    logger.info("Test complete")

def test_ou3_directly():
    """Test the OU3 alert directly without the full AlerterMain workflow"""
    logger.info("Starting direct OU3 test")
    
    alert = OverUnderAlert(threshold=3.0)
    test_matches = create_test_matches()
    
    # Test each match
    for idx, match in enumerate(test_matches):
        result = alert.check(match)
        if result:
            logger.info(f"Match {idx+1} (ID: {match['match_id']}) triggered alert: {result}")
        else:
            logger.info(f"Match {idx+1} (ID: {match['match_id']}) did NOT trigger alert")
    
    logger.info("Direct OU3 test complete")

if __name__ == "__main__":
    logger.info("Starting alert system tests")
    
    # Run the tests
    test_ou3_directly()
    logger.info("=" * 40)
    test_alerter_main()
    
    logger.info("All tests completed")
