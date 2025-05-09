#!/usr/bin/env python3

import logging
import json
import time
import os

# Get the absolute path to the directory this script is in
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configure basic logging to see debug messages
logging.basicConfig(level=logging.DEBUG)

# Import the custom logger after setting up basic logging
from json_logger import json_logger

print("Testing JSON logger with universal prepending rule...")
print(f"Log file should be at: {os.path.join(script_dir, 'json.log')}")

# Test with multiple match blocks to verify newest-first ordering
for match_num in range(3, 0, -1):
    print(f"Creating test match block {match_num}...")
    
    # Create a test match block with the 50-character separator
    header = "="*50
    json_logger.debug(header)
    
    # Log match summary data
    json_logger.debug(f"MATCH #{match_num} TEST")
    json_logger.debug(header)
    
    # Log some match data in JSON format
    match_data = {
        "match_id": f"test_match_{match_num}",
        "home_team": f"Home Team {match_num}",
        "away_team": f"Away Team {match_num}",
        "score": f"{match_num}-{match_num-1}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Log the JSON data
    json_logger.debug(json.dumps(match_data, indent=2))
    
    # Log an empty line to trigger the end of block detection
    json_logger.debug("")
    
    # Add a small delay to ensure timestamps are different
    time.sleep(1)

print("Test complete. Checking if json.log file exists...")
log_path = os.path.join(script_dir, "json.log")
if os.path.exists(log_path):
    print(f"Log file exists at {log_path}")
    print(f"Log file size: {os.path.getsize(log_path)} bytes")
    # Print the first few lines of the log file
    try:
        with open(log_path, 'r') as f:
            contents = f.read(500)  # Read first 500 bytes
            print("\nLog file contents (first 500 bytes):")
            print(contents)
    except Exception as e:
        print(f"Error reading log file: {e}")
else:
    print(f"Log file not found at {log_path}")
