#!/usr/bin/env python3
"""
Post-processor for live.py output that converts wind speed from m/s to mph
without modifying the original live.py file.
"""

import sys
import re

# Conversion factor from m/s to mph
MS_TO_MPH = 2.237

def convert_wind_to_mph(line):
    """
    Convert wind readings from m/s to mph if found in the line.
    Format: Wind: X.Xm/s --> Wind: X.X m/s (Y.Y mph)
    """
    wind_pattern = r'Wind: (\d+\.\d+)m/s'
    match = re.search(wind_pattern, line)
    
    if match:
        wind_ms = float(match.group(1))
        wind_mph = wind_ms * MS_TO_MPH
        return line.replace(f"Wind: {wind_ms}m/s", f"Wind: {wind_ms}m/s ({wind_mph:.1f} mph)")
    
    return line

def process_output():
    """
    Process the input from stdin line by line,
    converting wind speeds and printing the result.
    """
    for line in sys.stdin:
        # Remove trailing newline
        line = line.rstrip()
        
        # Convert wind speed if found
        line = convert_wind_to_mph(line)
        
        # Print the processed line
        print(line)

if __name__ == "__main__":
    process_output()
