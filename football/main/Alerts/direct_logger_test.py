#!/usr/bin/env python3
"""
Simple test to ensure the alert logger files are created properly
"""

import os
import logging
import json
from OU3 import OverUnderAlert

# Define a clear path for the logger file
alerts_dir = os.path.dirname(os.path.abspath(__file__))
log_file = os.path.join(alerts_dir, "OverUnderAlert.logger")

# Remove existing log file if it exists
if os.path.exists(log_file):
    os.remove(log_file)
    print(f"Removed existing log file: {log_file}")

# Set up dedicated file handler for the OverUnderAlert logger
alert_logger = logging.getLogger("OverUnderAlert")
alert_logger.setLevel(logging.INFO)

# Create a file handler that writes to the log file
file_handler = logging.FileHandler(log_file)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
alert_logger.addHandler(file_handler)

# Also set up console output
console_handler = logging.StreamHandler()
console_handler.setFormatter(file_formatter)
alert_logger.addHandler(console_handler)

# Create a test match that should trigger an alert
test_match = {
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
}

print(f"Creating alert with threshold 3.0")
alert = OverUnderAlert(threshold=3.0)

print(f"Checking match with O/U = 3.5...")
result = alert.check(test_match)

if result:
    print(f"Alert triggered! Message: {result}")
    alert_logger.info(f"TEST ALERT: {result}")
    alert_logger.info(f"Alert triggered for match {test_match['match_id']}")
else:
    print(f"No alert triggered.")

# Check if the log file was created
if os.path.exists(log_file):
    with open(log_file, 'r') as f:
        content = f.read()
    print(f"\n✅ SUCCESS: Log file created at {log_file}")
    print(f"File size: {os.path.getsize(log_file)} bytes")
    print(f"Contents:")
    print("-" * 50)
    print(content)
    print("-" * 50)
else:
    print(f"\n❌ ERROR: Log file was not created at {log_file}")

print("\nTest complete.")
