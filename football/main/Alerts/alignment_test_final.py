#!/usr/bin/env python3
# alignment_test_final.py - Final test for column alignment

import os
import sys

# Create test file to visualize alignment options
TEST_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "alignment_visual.txt")

def write_lines_to_file(title, lines):
    with open(TEST_FILE, 'a') as f:
        f.write(f"\n=== {title} ===\n")
        for line in lines:
            f.write(line + "\n")
        f.write("\n")

# Clear file
with open(TEST_FILE, 'w') as f:
    f.write("# ODDS ALIGNMENT VISUALIZATION\n")
    f.write("# Character counts shown for each label\n")

# Character count test
label_counts = [
    "Home (4 chars) + ':' = 5 chars",
    "Draw (4 chars) + ':' = 5 chars",
    "Away (4 chars) + ':' = 5 chars",
    "Hcap (4 chars) + ':' = 5 chars", 
    "Line (4 chars) + ':' = 5 chars",
    "Under (5 chars) + ':' = 6 chars"
]
write_lines_to_file("CHARACTER COUNTS", label_counts)

# Current implementation (spaces after each colon)
current = [
    "│ Home : +195 │ Draw : +350 │ Away : +400 │",
    "│ Home : +180 │ Hcap : -1.0 │ Away : +210 │",
    "│ Over : +190 │ Line : 3.5  │ Under : +200 │"
]
write_lines_to_file("CURRENT IMPLEMENTATION (SPACE AFTER EACH COLON)", current)

# Option 1: Pad shorter labels with spaces
padded = [
    "│ Home  : +195 │ Draw  : +350 │ Away  : +400 │",
    "│ Home  : +180 │ Hcap  : -1.0 │ Away  : +210 │",
    "│ Over  : +190 │ Line  : 3.5  │ Under : +200 │"
]
write_lines_to_file("OPTION 1: PAD SHORTER LABELS WITH SPACES", padded)

# Option 2: Right align values with fixed width
fixed = [
    "│ Home :  +195 │ Draw :  +350 │ Away :  +400 │",
    "│ Home :  +180 │ Hcap :  -1.0 │ Away :  +210 │",
    "│ Over :  +190 │ Line :   3.5 │ Under:  +200 │"
]
write_lines_to_file("OPTION 2: RIGHT ALIGN VALUES WITH FIXED WIDTH", fixed)

# Option 3: No spaces after colons
no_spaces = [
    "│ Home: +195 │ Draw: +350 │ Away: +400 │",
    "│ Home: +180 │ Hcap: -1.0 │ Away: +210 │",
    "│ Over: +190 │ Line: 3.5  │ Under: +200 │"
]
write_lines_to_file("OPTION 3: NO SPACES AFTER COLONS (ORIGINAL)", no_spaces)

print(f"Created alignment visualization at {TEST_FILE}")
print("\nCHARACTER COUNTS:")
for line in label_counts:
    print(line)

print("\nOPTION 1: PAD ALL LABELS TO MATCH 'UNDER' (RECOMMENDED)")
for line in padded:
    print(line)
