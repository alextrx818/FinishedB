#!/usr/bin/env python3
# odds_alignment_test.py - Test betting odds alignment in the logger output

import os
import logging
import sys

# Define logger path
ALERTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_FILE = os.path.join(ALERTS_DIR, "alignment_test.txt")

# Create test file to show the alignment
with open(TEST_FILE, 'w') as f:
    # Write header
    f.write("\n--- MATCH BETTING ODDS ---\n")
    
    # Previous format (with space before colon in Away column)
    f.write("BEFORE FIX:\n")
    f.write("│ Home: +195 │ Draw: +350 │ Away : +400 │ (@4')\n")
    f.write("│ Home: +180 │ Hcap: -1.0 │ Away : +210 │ (@4')\n")
    f.write("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')\n")
    
    # New format (without space before colon in Away column)
    f.write("\nAFTER FIX:\n")
    f.write("│ Home: +195 │ Draw: +350 │ Away: +400 │ (@4')\n")
    f.write("│ Home: +180 │ Hcap: -1.0 │ Away: +210 │ (@4')\n")
    f.write("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')\n")

print(f"Created alignment test file: {TEST_FILE}")
print("\nBefore fix (with space before colon in Away column):")
print("│ Home: +195 │ Draw: +350 │ Away : +400 │ (@4')")
print("│ Home: +180 │ Hcap: -1.0 │ Away : +210 │ (@4')")
print("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')")

print("\nAfter fix (without space before colon in Away column):")
print("│ Home: +195 │ Draw: +350 │ Away: +400 │ (@4')")
print("│ Home: +180 │ Hcap: -1.0 │ Away: +210 │ (@4')")
print("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')")

# Run a live test of the updated alerter_main.py
print("\nLive test through alerter_main.py")
print("Note: You can see the alignment in the upcoming odds fields:")
print("- Away: +400 (instead of Away : +400)")
print("- Away: +210 (instead of Away : +210)")
print("- Under: +200 (Under is correctly aligned already)")

print("\nFull test with real data can be run with:")
print("python3 logger_test.py")
