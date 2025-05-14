#!/usr/bin/env python3
"""
Direct test for alerter_main.py that generates actual log files
by monkeypatching the imports directly.
"""

import json
import logging
import os
import sys
import importlib

# Configure root logger
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('direct_test')

# Create sample match data 
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
                    # Show first few log lines if any
                    if lines:
                        logger.info(f"Sample log content: {lines[0].strip()}")
                except Exception as e:
                    logger.error(f"❌ Error reading {filepath}: {e}")
        else:
            logger.warning(f"❌ {description} {filepath} was NOT created")

# Create mock modules for dependencies
class MockModule:
    pass

# Mock fetch_and_cache function
def mock_fetch_and_cache():
    logger.info("Mock fetch_and_cache called")
    return create_test_matches()

# Mock merge_all function
def mock_merge_all(data):
    logger.info(f"Mock merge_all called with {len(data)} matches")
    return data

# Mock format_summary function
def mock_format_summary(match):
    return json.dumps({
        "match_id": match.get("match_id"),
        "teams": f"{match.get('home_team', {}).get('name', match.get('home', 'Unknown'))} vs {match.get('away_team', {}).get('name', match.get('away', 'Unknown'))}",
        "competition": match.get('competition', {}).get('name', 'Unknown League'),
        "status": match.get('status'),
        "odds": match.get('odds')
    }, indent=2)

# Mock notification function
def mock_send_notification(message):
    logger.info(f"TELEGRAM NOTIFICATION SENT:\n{message[:300]}...")
    return True

def run_direct_test():
    """Run a direct test by monkeypatching the import system"""
    logger.info("-" * 60)
    logger.info("STARTING DIRECT ALERTER_MAIN TEST")
    logger.info("-" * 60)
    
    # Reset any existing test files
    reset_test_files()
    
    # Create mock modules
    sys.modules['pure_json_fetch_cache'] = MockModule()
    sys.modules['pure_json_fetch_cache'].fetch_and_cache = mock_fetch_and_cache
    
    sys.modules['merge_logic'] = MockModule()
    sys.modules['merge_logic'].merge_all = mock_merge_all
    
    sys.modules['combined_match_summary'] = MockModule()
    sys.modules['combined_match_summary'].format_summary = mock_format_summary
    
    # Now we can safely import alerter_main
    logger.info("Importing alerter_main with mocked dependencies...")
    
    # Save original imports for restoration
    orig_import = __builtins__.__import__
    
    # Patch the alerter_main.py imports dynamically
    def patched_import(name, *args, **kwargs):
        if name in ['pure_json_fetch_cache', 'merge_logic', 'combined_match_summary']:
            return sys.modules[name]
        return orig_import(name, *args, **kwargs)
    
    # Apply the patch
    __builtins__.__import__ = patched_import
    
    try:
        # Import from OU3 directly to avoid circular issues
        from OU3 import OverUnderAlert
        
        # Now import alerter_main and override send_notification
        import alerter_main
        alerter_main.send_notification = mock_send_notification
        
        # Create AlerterMain instance with our alerts
        alerts = [
            OverUnderAlert(threshold=3.0),
            alerter_main.FutureAlert()
        ]
        
        manager = alerter_main.AlerterMain(alerts=alerts)
        
        # Run the manager
        logger.info("Running alerter_main.run()...")
        manager.run()
        
        # Check generated files
        logger.info("\nChecking generated files...")
        check_generated_files()
        
        # Run again to test duplicate prevention
        logger.info("\nRunning a second time to test duplicate prevention...")
        manager.run()
        
        logger.info("-" * 60)
        logger.info("TEST COMPLETED SUCCESSFULLY")
        logger.info("-" * 60)
        
    finally:
        # Restore original import function
        __builtins__.__import__ = orig_import
        
        # Clean up mock modules
        for mod in ['pure_json_fetch_cache', 'merge_logic', 'combined_match_summary']:
            if mod in sys.modules:
                del sys.modules[mod]

if __name__ == "__main__":
    run_direct_test()
