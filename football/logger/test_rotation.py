#!/usr/bin/env python3

from json_logger import json_logger, force_rotation
import json
import time

print("Testing JSON logger midnight rotation...")

# First, add some test data to the current log
for i in range(3):
    print(f"Adding test match #{i+1}...")
    
    # Create a test match block
    header = "="*50
    json_logger.debug(header)
    json_logger.debug(f"ROTATION TEST MATCH #{i+1}")
    json_logger.debug(header)
    
    # Log some test data
    match_data = {
        "match_id": f"rotation_test_{i+1}",
        "test_field": f"Testing rotation {i+1}",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Log the JSON data
    json_logger.debug(json.dumps(match_data, indent=2))
    json_logger.debug("")
    
    # Add small delay
    time.sleep(1)

# Now force a log rotation
print("\nForcing log rotation to simulate midnight rollover...")
force_rotation()

# Add some data to the new log file
print("Adding test data to the new log file...")
json_logger.debug("="*50)
json_logger.debug("POST-ROTATION TEST")
json_logger.debug("="*50)
json_logger.debug(json.dumps({"status": "success", "message": "Log rotation complete"}, indent=2))
json_logger.debug("")

print("\nTest complete. Check the log files:")
print("1. json.log - Should contain only post-rotation data")
print("2. json.log.YYYY-MM-DD - Should contain pre-rotation data")
