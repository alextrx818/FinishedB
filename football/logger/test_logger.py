#!/usr/bin/env python3
"""
Test script for main_logger.py to verify prepending format works correctly
"""

# Import main_logger to override builtins.print
# The import itself will create a new main.logger file
import main_logger

print("Test message 1: Regular print")
print("Test message 2: With special characters! @#$%^&*()")
print("Test message 3: Multi-line\nThis is a second line\nThis is a third line")

# Test match header (which should be handled specially)
print("MATCH: Team A vs Team B")

# Test buffer handling
# The handle_buffer_end function should format this as a chunk
print("==BUFFER_START==")
print("Buffer line 1")
print("Buffer line 2")
print("Buffer line 3")
print("==BUFFER_END==")

print("Test complete!")
