#!/usr/bin/env python3
"""
Quick test script for main_logger.py
"""

# Import the logger module which will initialize everything
import football.logger.main_logger

# Print a header that will trigger the buffer mechanism
print("="*50)
print("TEST HEADER BLOCK")
print("="*50)

# Print some content that will be part of the buffer
print("Test log entry content 1")
print("Test log entry content 2")
print("Test log entry content 3")

# Print blank line to flush the buffer and trigger the listener
print("")

# Wait a moment to allow the listener to process
import time
time.sleep(2)

print("Test completed")
