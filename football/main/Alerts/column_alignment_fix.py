#!/usr/bin/env python3
# column_alignment_fix.py - Test script for proper odds column alignment

import os
import logging
import sys

# Define test file
ALERTS_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_FILE = os.path.join(ALERTS_DIR, "column_fix.txt")

# Create test file to show proper column alignment
with open(TEST_FILE, 'w') as f:
    # Write header
    f.write("\n--- MATCH BETTING ODDS ALIGNMENT OPTIONS ---\n\n")
    
    # Option 1: Current alignment
    f.write("CURRENT:\n")
    f.write("│ Home: +195 │ Draw: +350 │ Away: +400 │ (@4')\n")
    f.write("│ Home: +180 │ Hcap: -1.0 │ Away: +210 │ (@4')\n")
    f.write("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')\n\n")
    
    # Option 2: Consistent column width for final column
    f.write("OPTION 1 - FIX COLUMN WIDTH:\n")
    f.write("│ Home: +195 │ Draw: +350 │ Away : +400 │ (@4')\n")
    f.write("│ Home: +180 │ Hcap: -1.0 │ Away : +210 │ (@4')\n")
    f.write("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')\n\n")
    
    # Option 3: Right align all values
    f.write("OPTION 2 - FIXED WIDTH WITH PADDING:\n")
    f.write("│ Home:  +195 │ Draw:  +350 │ Away:  +400 │ (@4')\n")
    f.write("│ Home:  +180 │ Hcap:  -1.0 │ Away:  +210 │ (@4')\n")
    f.write("│ Over:  +190 │ Line:   3.5 │ Under: +200 │ (@4')\n\n")

print(f"Created column alignment test file: {TEST_FILE}")
print("\nOPTION 1 - ADD A SPACE AFTER 'AWAY:'")
print("│ Home: +195 │ Draw: +350 │ Away : +400 │ (@4')")
print("│ Home: +180 │ Hcap: -1.0 │ Away : +210 │ (@4')")
print("│ Over: +190 │ Line: 3.5 │ Under: +200 │ (@4')")

print("\nOPTION 2 - USE FIXED WIDTH WITH CONSISTENT SPACING")
print("│ Home:  +195 │ Draw:  +350 │ Away:  +400 │ (@4')")
print("│ Home:  +180 │ Hcap:  -1.0 │ Away:  +210 │ (@4')")
print("│ Over:  +190 │ Line:   3.5 │ Under: +200 │ (@4')")

print("\nWhich option would you prefer? Option 1 adds a space after 'Away:' to match")
print("the width of 'Under:'. Option 2 uses consistent two-space padding after each label.")
