#!/usr/bin/env python3
# simple_logger_test.py - Test logger formatting with a simplified approach

import os
import logging
import sys

# Define constants
ALERTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_LOGGER_PATH = os.path.join(ALERTS_DIR, "OU3.logger")

# Remove any existing logger file
if os.path.exists(TEST_LOGGER_PATH):
    os.remove(TEST_LOGGER_PATH)
    print(f"Removed existing {TEST_LOGGER_PATH}")

# Create a simple formatter
simple_formatter = logging.Formatter("%(asctime)s - %(message)s")

# Setup the logger
logger = logging.getLogger("OU3")
logger.setLevel(logging.INFO)

# Create a file handler with the simple formatter
file_handler = logging.FileHandler(TEST_LOGGER_PATH)
file_handler.setFormatter(simple_formatter)
logger.addHandler(file_handler)

# Log the initial alert with timestamp
logger.info("Alert triggered for match TEST-123: OU3 Alert!")

# Create a clean formatter (no timestamp)
clean_formatter = logging.Formatter("%(message)s")

# Switch to the clean formatter for the match summary
file_handler.setFormatter(clean_formatter)

# Log the match summary without timestamps
logger.info("\n" + "=" * 80)
logger.info("ALERT TRIGGERED: OU3")
logger.info("=" * 80)

# Log the formatted match summary
logger.info("")
logger.info("----- MATCH SUMMARY -----")
logger.info("Timestamp: 05/14/2025 12:15:00 PM EDT")
logger.info("Match ID: TEST-123")
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

# Switch back to the original formatter
file_handler.setFormatter(simple_formatter)

# Log final message with timestamp
logger.info("Alert processing complete")

# Verify the file was created
if os.path.exists(TEST_LOGGER_PATH):
    print(f"\nSuccessfully created {TEST_LOGGER_PATH}")
    print("\nLogger contents:")
    print("-" * 40)
    with open(TEST_LOGGER_PATH, "r") as f:
        print(f.read())
else:
    print(f"\nFailed to create {TEST_LOGGER_PATH}")
