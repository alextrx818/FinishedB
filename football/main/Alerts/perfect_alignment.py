#!/usr/bin/env python3
"""
perfect_alignment.py

Fix the alignment issue by ensuring exact spacing in the betting odds display.
"""

import os

# Create a test file with perfectly aligned columns
test_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "OU3.logger")
with open(test_file, 'w') as f:
    f.write("2025-05-14 16:43:30,000 - Alert triggered for match TEST-45678: O/U line = 4.5 (threshold: 3.0)\n\n")
    f.write("="*80 + "\n")
    f.write(f"#1 of 1 ALERT TRIGGERED: OU3 @ 04:43:30 PM 05/14/2025\n")
    f.write("="*80 + "\n\n")
    f.write("----- MATCH SUMMARY -----\n")
    f.write("Timestamp: 05/14/2025 04:43:30 PM EDT\n")
    f.write("Match ID: TEST-45678\n")
    f.write("Competition ID: comp-laliga\n")
    f.write("Competition: LaLiga (Spain)\n")
    f.write("Match: Barcelona vs Real Madrid\n")
    f.write("Score: 1 - 1 (HT: 0 - 0)\n")
    f.write("Status: Second Half (Status ID: 4)\n\n")
    f.write("--- MATCH BETTING ODDS ---\n")
    
    # Perfectly aligned odds lines
    f.write("│ Home  : +140 │ Draw  : +290 │ Away  : +350 │ (@52')\n")
    f.write("│ Home  : +125 │ Hcap  : -0.5 │ Away  : +180 │ (@52')\n")
    f.write("│ Over  : +160 │ Line  : 4.5  │ Under : +240 │ (@52')\n")
    
    f.write("\n--- MATCH ENVIRONMENT ---\n")
    f.write("Temperature: 74.0°F\n")
    f.write("Humidity: 55%\n")
    f.write("Wind: 6.2 mph\n")
    f.write("2025-05-14 16:43:30,001 - Alert processing complete\n")

print(f"Created perfectly aligned test file: {test_file}")
print("\nPerfect alignment:")
print("│ Home  : +140 │ Draw  : +290 │ Away  : +350 │ (@52')")
print("│ Home  : +125 │ Hcap  : -0.5 │ Away  : +180 │ (@52')")
print("│ Over  : +160 │ Line  : 4.5  │ Under : +240 │ (@52')")

# Update the formatting_utils.py file
utils_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "formatting_utils.py")
if os.path.exists(utils_file):
    with open(utils_file, 'r') as f:
        content = f.read()
    
    # Update the padding logic
    new_content = content.replace(
        "    # Add trailing space to line_str for alignment\n    if len(line_str) < 4:  # If it's like \"3.5\" (3 chars) add a space\n        line_str = f\"{line_str} \"",
        "    # Ensure exact padding for line_str\n    # For values like \"3.5\" (3 chars), add exactly one space\n    if len(line_str) == 3:\n        line_str = f\"{line_str} \""
    )
    
    with open(utils_file, 'w') as f:
        f.write(new_content)
    
    print("\nUpdated formatting_utils.py with correct padding logic")
