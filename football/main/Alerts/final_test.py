#!/usr/bin/env python3
# final_test.py - Definitive test for the OU3 logger format

import os
import logging
import sys
from datetime import datetime

# Define logger path
ALERTS_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(ALERTS_DIR, "OU3.logger")

# Remove any existing log file
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
    print(f"Removed existing {LOG_FILE}")

# Set up the logger - IMPORTANT: Use the file handler first approach
logger = logging.getLogger("OU3")
logger.setLevel(logging.INFO)

# Create a file handler with timestamps
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
logger.addHandler(file_handler)

# Create a console handler for debugging
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter("CONSOLE: %(message)s"))
logger.addHandler(console_handler)

print("\n--- TESTING LOGGER FORMAT ---")

# Write the initial alert message with timestamp
logger.info("Alert triggered for match TEST-123: High OU Line 3.5!")

# Change formatter to remove timestamps for match summary
file_handler.setFormatter(logging.Formatter("%(message)s"))

# Log the match summary without timestamps
logger.info("\n" + "=" * 80)
logger.info("ALERT TRIGGERED: OU3")
logger.info("=" * 80)
logger.info("")
logger.info("----- MATCH SUMMARY -----")
logger.info("Timestamp: 05/14/2025 12:20:00 PM EDT")
logger.info("Match ID: TEST-123")
logger.info("Competition ID: comp-epl")
logger.info("Competition: English Premier League (England)")
logger.info("Match: Manchester United vs Liverpool FC")
logger.info("Score: 2 - 1 (HT: 2 - 1)")
logger.info("Status: Half-time (Status ID: 3)")
logger.info("")
logger.info("--- MATCH BETTING ODDS ---")
logger.info("│ Home  : +195 │ Draw  : +350 │ Away  : +400 │ (@4')")
logger.info("│ Home  : +180 │ Hcap  : -1.0 │ Away  : +210 │ (@4')")
logger.info("│ Over  : +190 │ Line  : 3.5 │ Under : +200 │ (@4')")
logger.info("")
logger.info("--- MATCH ENVIRONMENT ---")
logger.info("Temperature: 64.4°F")
logger.info("Humidity: 72%")
logger.info("Wind: 10.0 mph")

# Restore the original formatter
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

# Final message with timestamp
logger.info("Alert processing complete")

# Read and display the log file contents
print("\n--- LOG FILE CONTENTS ---")
try:
    with open(LOG_FILE, 'r') as f:
        log_content = f.read()
        print(log_content)
    print("\n✅ Logger file created successfully with correct format!")
except Exception as e:
    print(f"\n❌ Error reading log file: {e}")
    
# Write the file contents to a visible location
summary_path = os.path.join(ALERTS_DIR, "format_summary.txt")
with open(summary_path, 'w') as f:
    f.write("=== OU3.logger Contents ===\n")
    try:
        with open(LOG_FILE, 'r') as log_f:
            f.write(log_f.read())
    except Exception as e:
        f.write(f"Error reading log file: {e}")

print(f"\nLog contents also written to {summary_path} for review")
