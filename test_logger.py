#!/usr/bin/env python3
"""
Test script to verify the universal logger formatting rules
"""

from football.logger.main_logger import setup_logger
import time

# Create a test block with header, content and blank line ending
print("="*50)
print("TEST HEADER: UNIVERSAL FORMATTING RULES")
print("="*50)
print("This is line 1 of the test block")
print("This is line 2 of the test block")
print("This is line 3 of the test block")
print("")  # Blank line to trigger flushing

# Wait a moment
time.sleep(1)

# Create a second test block
print("="*50)
print("TEST HEADER: SECOND BLOCK")
print("="*50)
print("Second block line 1")
print("Second block line 2")
print("")  # Blank line to trigger flushing

# Print something outside a block
print("This is outside any block and should use the normal logging")
