#!/usr/bin/env python3
"""
Simple direct test for OU3.py with file generation
This test focuses on generating the actual log files for alerts.
"""

import json
import logging
import os
from OU3 import OverUnderAlert

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('log_test')

# Create a class to simulate AlerterMain functionality but with simplified operation
class TestAlerter:
    def __init__(self, alerts):
        """Initialize with a list of alert objects"""
        self.alerts = alerts
        self.alerts_dir = os.path.dirname(os.path.abspath(__file__))
        self.seen_ids = {}
        
        # Set up loggers for each alert
        for alert in self.alerts:
            name = alert.__class__.__name__
            alert_logger = logging.getLogger(name)
            
            # Only add handler if it doesn't exist
            if not alert_logger.handlers:
                alert_logger.setLevel(logging.INFO)
                # Save log file in Alerts directory
                log_path = os.path.join(self.alerts_dir, f"{name}.logger")
                handler = logging.FileHandler(log_path)
                handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
                alert_logger.addHandler(handler)
            
            # Initialize seen IDs
            self.seen_ids[name] = set()
    
    def process_matches(self, matches):
        """Process each match through the alert system"""
        for match in matches:
            match_id = match.get("match_id", "unknown")
            logger.info(f"Processing match {match_id}")
            
            for alert in self.alerts:
                name = alert.__class__.__name__
                result = alert.check(match)
                
                if result and match_id not in self.seen_ids[name]:
                    # This would send a Telegram notification in the real system
                    logger.info(f"ALERT TRIGGERED: {result[:100]}...")
                    
                    # Log the result to the alert's log file
                    alert_logger = logging.getLogger(name)
                    alert_logger.info(f"Alert triggered for match {match_id}: {result}")
                    
                    # Add to seen IDs
                    self.seen_ids[name].add(match_id)
                    
                    # Save seen IDs to file
                    self._save_seen_ids(name)
    
    def _save_seen_ids(self, name):
        """Save seen IDs to a JSON file"""
        seen_file = os.path.join(self.alerts_dir, f"{name}.seen.json")
        try:
            with open(seen_file, 'w') as f:
                json.dump(list(self.seen_ids[name]), f)
        except Exception as e:
            logger.error(f"Failed to save seen IDs: {e}")

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

def check_generated_files():
    """Check if the expected files were generated"""
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Files to check
    expected_files = {
        "OverUnderAlert.logger": "Alert log file",
        "OverUnderAlert.seen.json": "Seen match IDs file"
    }
    
    for filename, description in expected_files.items():
        filepath = os.path.join(alerts_dir, filename)
        if os.path.exists(filepath):
            # Get file size
            size = os.path.getsize(filepath)
            
            if filename.endswith('.json'):
                try:
                    with open(filepath, 'r') as f:
                        content = json.load(f)
                    logger.info(f"✅ {description} {filepath} exists ({size} bytes) - Contains {len(content)} match IDs: {content}")
                except Exception as e:
                    logger.error(f"❌ Error reading {filepath}: {e}")
            else:
                # For log files, read and count lines
                try:
                    with open(filepath, 'r') as f:
                        lines = f.readlines()
                    logger.info(f"✅ {description} {filepath} exists ({size} bytes) - Contains {len(lines)} log entries")
                    
                    # Show contents of log file
                    logger.info("Log file contents:")
                    for line in lines:
                        logger.info(f"  {line.strip()}")
                except Exception as e:
                    logger.error(f"❌ Error reading {filepath}: {e}")
        else:
            logger.error(f"❌ {description} {filepath} was NOT created")

def reset_test_files():
    """Delete any existing test files to start fresh"""
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Files to reset
    test_files = [
        "OverUnderAlert.logger",
        "OverUnderAlert.seen.json"
    ]
    
    for filename in test_files:
        filepath = os.path.join(alerts_dir, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Removed existing test file: {filepath}")

def run_log_test():
    """Run a test that generates actual log files"""
    logger.info("-" * 60)
    logger.info("STARTING ALERT LOG FILE GENERATION TEST")
    logger.info("-" * 60)
    
    # Reset any existing test files
    reset_test_files()
    
    # Create alert instances
    alerts = [OverUnderAlert(threshold=3.0)]
    
    # Create test alerter
    alerter = TestAlerter(alerts)
    
    # Process test matches
    test_matches = create_test_matches()
    alerter.process_matches(test_matches)
    
    # Check generated files
    logger.info("\nChecking generated files after first run:")
    check_generated_files()
    
    # Run again to test duplicate prevention
    logger.info("\nRunning second time to test duplicate prevention...")
    alerter.process_matches(test_matches)
    
    logger.info("\nChecking files after second run (should have same number of alerts):")
    check_generated_files()
    
    logger.info("-" * 60)
    logger.info("LOG FILE GENERATION TEST COMPLETE")
    logger.info("-" * 60)

if __name__ == "__main__":
    run_log_test()
