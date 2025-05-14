#!/usr/bin/env python3
# test_ou3_logger.py - Direct test writing to OU3.logger

import os
import logging
import sys
from datetime import datetime

# Define logger path
ALERTS_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(ALERTS_DIR, "OU3.logger")

# Remove any existing log file to start fresh
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
    print(f"Removed existing {LOG_FILE}")

# Set up the logger specifically for OU3
logger = logging.getLogger("OU3")
logger.setLevel(logging.INFO)

# Create a file handler with timestamps
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(file_handler)

print(f"Creating new log entry in {LOG_FILE}...")

# Write the initial alert message with timestamp
logger.info("Alert triggered for match LIVE-12345: OU3 Alert with line 3.5!")

# Change formatter to remove timestamps for match summary
file_handler.setFormatter(logging.Formatter("%(message)s"))

# Log the match summary without timestamps
logger.info("\n" + "=" * 80)
logger.info("ALERT TRIGGERED: OU3")
logger.info("=" * 80)
logger.info("")
logger.info("----- MATCH SUMMARY -----")
logger.info("Timestamp: 05/14/2025 12:23:00 PM EDT")
logger.info("Match ID: LIVE-12345")
logger.info("Competition ID: comp-epl")
logger.info("Competition: English Premier League (England)")
logger.info("Match: Manchester United vs Liverpool FC")
logger.info("Score: 2 - 1 (HT: 2 - 1)")
logger.info("Status: Half-time (Status ID: 3)")
logger.info("")
logger.info("--- MATCH BETTING ODDS ---")
logger.info("│ Home: +195 │ Draw: +350 │ Away : +400 │ (@4')")
logger.info("│ Home: +180 │ Hcap: -1.0 │ Away : +210 │ (@4')")
logger.info("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')")
logger.info("")
logger.info("--- MATCH ENVIRONMENT ---")
logger.info("Temperature: 64.4°F")
logger.info("Humidity: 72%")
logger.info("Wind: 10.0 mph")

# Restore the original formatter
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

# Final message with timestamp
logger.info("Alert processing complete")

print(f"\nSuccessfully created log entry in {LOG_FILE}")
print("\nContents of OU3.logger:")
print("-" * 50)

# Display the contents of the log file
with open(LOG_FILE, 'r') as f:
    print(f.read())
    
print("-" * 50)
print("\nVerify that the column alignment in the odds display looks correct:")
