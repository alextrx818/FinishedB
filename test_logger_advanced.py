#!/usr/bin/env python3
"""
Advanced test script to verify the universal logger formatting rules
with multiple blocks and various content types
"""

from football.logger.main_logger import setup_logger
import time

# Test 1: Standard block with header and footer
print("="*50)
print("TEST 1: STANDARD BLOCK FORMAT")
print("="*50)
print("This is a standard block with various content")
print("Line with some numbers: 123, 456, 789")
print("Line with special characters: !@#$%^&*()")
print("")  # Blank line to trigger flushing

time.sleep(1)

# Test 2: Match-like format
print("="*50)
print("MATCH #99 OF 100")
print("="*50)
print("----- MATCH SUMMARY -----")
print("Timestamp: 05/05/2025 10:45:00 AM ET")
print("Match ID: test123456")
print("Competition: Test Competition")
print("Match: Home Team vs Away Team")
print("Score: 2 - 1")
print("")  # Blank line to trigger flushing

time.sleep(1)

# Test 3: Multiple sections in one block
print("="*50)
print("TEST 3: MULTIPLE SECTIONS")
print("="*50)
print("----- SECTION 1 -----")
print("Data for section 1")
print("More data for section 1")
print("----- SECTION 2 -----")
print("Data for section 2")
print("More data for section 2")
print("")  # Blank line to trigger flushing

# Print something outside a block to verify normal logging
print("This line is outside any block and should use normal logging")
