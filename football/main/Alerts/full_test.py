#!/usr/bin/env python3
"""
Full integration test for alerter_main.py and OU3.py.
This test simulates the full alert system workflow including file generation.
"""

import json
import logging
import os
import sys
import importlib.util

# Configure root logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('full_test')

# Load the alerter_main module
alerter_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alerter_main.py")
spec = importlib.util.spec_from_file_location("alerter_main", alerter_path)
alerter_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(alerter_module)

# Load real dependencies to replace with mocks
class MockFetchCache:
    @staticmethod
    def fetch_and_cache():
        logger.info("Mock fetch_and_cache called")
        return create_test_matches()

class MockMergeLogic:
    @staticmethod
    def merge_all(raw_data):
        logger.info(f"Mock merge_all called with {len(raw_data)} matches")
        return raw_data

class MockCombinedSummary:
    @staticmethod
    def format_summary(match):
        return json.dumps({
            "match_id": match.get("match_id"),
            "teams": f"{match.get('home_team', {}).get('name', match.get('home', 'Unknown'))} vs {match.get('away_team', {}).get('name', match.get('away', 'Unknown'))}",
            "competition": match.get('competition', {}).get('name', 'Unknown League'),
            "status": match.get('status'),
            "odds": match.get('odds')
        }, indent=2)

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

def patch_dependencies():
    """Patch the dependencies in alerter_main.py with our mocks"""
    # Replace the fetch_and_cache function
    alerter_module.fetch_and_cache = MockFetchCache.fetch_and_cache
    
    # Replace the merge_all function
    alerter_module.merge_all = MockMergeLogic.merge_all
    
    # Replace the format_summary function
    alerter_module.format_summary = MockCombinedSummary.format_summary
    
    # Replace the send_notification function to avoid actual Telegram messages
    def mock_send_notification(message):
        logger.info(f"MOCK NOTIFICATION SENT: {message[:100]}...")
        return True
    
    alerter_module.send_notification = mock_send_notification
    
    logger.info("Dependencies patched with test mocks")

def reset_test_files():
    """Delete any existing test files to start fresh"""
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Files to reset
    test_files = [
        "OverUnderAlert.logger",
        "OverUnderAlert.seen.json",
        "FutureAlert.logger",
        "FutureAlert.seen.json"
    ]
    
    for filename in test_files:
        filepath = os.path.join(alerts_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Removed existing test file: {filepath}")

def check_generated_files():
    """Check if the expected files were generated"""
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Files to check
    expected_files = {
        "OverUnderAlert.logger": "Alert log file",
        "OverUnderAlert.seen.json": "Seen match IDs file",
        "FutureAlert.logger": "Alert log file",
        "FutureAlert.seen.json": "Seen match IDs file"
    }
    
    for filename, description in expected_files.items():
        filepath = os.path.join(alerts_dir, filename)
        if os.path.exists(filepath):
            # Get file size and content summary
            size = os.path.getsize(filepath)
            
            if filename.endswith('.json'):
                try:
                    with open(filepath, 'r') as f:
                        content = json.load(f)
                    logger.info(f"✅ {description} {filepath} exists ({size} bytes) - Contains {len(content)} IDs: {content}")
                except Exception as e:
                    logger.error(f"❌ Error reading {filepath}: {e}")
            else:
                # For log files, read and count lines
                try:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                    logger.info(f"✅ {description} {filepath} exists ({size} bytes) - Contains {len(lines)} log entries")
                    # Show first few log lines
                    if lines:
                        logger.info(f"Sample log content: {lines[0].strip()}")
                except Exception as e:
                    logger.error(f"❌ Error reading {filepath}: {e}")
        else:
            logger.warning(f"❌ {description} {filepath} was NOT created")

def run_full_test():
    """Run a full test of the alerter_main.py with our test data"""
    logger.info("-" * 60)
    logger.info("STARTING FULL ALERTER_MAIN TEST")
    logger.info("-" * 60)
    
    # Reset any existing test files
    reset_test_files()
    
    # Patch dependencies
    patch_dependencies()
    
    # Register the alerts
    from OU3 import OverUnderAlert
    alerts = [
        OverUnderAlert(threshold=3.0),
        alerter_module.FutureAlert()
    ]
    
    # Create the AlerterMain instance
    manager = alerter_module.AlerterMain(alerts=alerts)
    
    # Run the alerter
    logger.info("Running alerter_main.run()...")
    manager.run()
    
    # Check if files were generated
    logger.info("Checking generated files...")
    check_generated_files()
    
    # Run a second time to test the duplicate prevention
    logger.info("\nRunning alerter_main.run() a second time to test duplicate prevention...")
    manager.run()
    
    logger.info("-" * 60)
    logger.info("FULL TEST COMPLETE")
    logger.info("-" * 60)

if __name__ == "__main__":
    run_full_test()
