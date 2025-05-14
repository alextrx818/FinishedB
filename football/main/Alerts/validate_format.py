#!/usr/bin/env python3
"""
validate_format.py

Validate that all section headers in the match summary have proper underlines.
"""

import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary formatting utilities
from formatting_utils import (
    MATCH_SUMMARY_HEADER,
    BETTING_ODDS_HEADER,
    ENVIRONMENT_HEADER
)

# Import the match formatting function from alerter_main
from Alerts.alerter_main import format_match_summary

def main():
    # Create a simple test match
    test_match = {
        "id": "TEST-ID",
        "competition": {
            "id": "comp-test",
            "name": "Test League",
            "country": "Test Country"
        },
        "home_team": "Home Team",
        "away_team": "Away Team",
        "status": "In Progress",
        "status_id": 3,
        "score": {"home": 1, "away": 0, "home_ht": 0, "away_ht": 0},
        "odds": {
            "markets": [
                {
                    "type": "MONEYLINE",
                    "home": 1.50,
                    "draw": 2.50,
                    "away": 3.50
                }
            ]
        },
        "environment": {
            "temperature": "20°C"
        }
    }
    
    # Get formatted match summary
    formatted_lines = format_match_summary(test_match)
    
    # Print the actual formatted output
    print("\n=== FORMATTED MATCH SUMMARY ===")
    for line in formatted_lines:
        print(f"{line}")
    
    # Find the section headers and check for underlines
    headers_with_underlines = 0
    for i, line in enumerate(formatted_lines):
        line = line.strip()
        if line == MATCH_SUMMARY_HEADER and i+1 < len(formatted_lines):
            underline = formatted_lines[i+1].strip()
            print(f"\nFound Match Summary Header at line {i}")
            print(f"Next line is: '{underline}'")
            print(f"Expected: '{'-' * len(MATCH_SUMMARY_HEADER)}'")
            print(f"Match: {underline == '-' * len(MATCH_SUMMARY_HEADER)}")
            if underline == '-' * len(MATCH_SUMMARY_HEADER):
                headers_with_underlines += 1
        
        if line == BETTING_ODDS_HEADER and i+1 < len(formatted_lines):
            underline = formatted_lines[i+1].strip()
            print(f"\nFound Betting Odds Header at line {i}")
            print(f"Next line is: '{underline}'")
            print(f"Expected: '{'-' * len(BETTING_ODDS_HEADER)}'")
            print(f"Match: {underline == '-' * len(BETTING_ODDS_HEADER)}")
            if underline == '-' * len(BETTING_ODDS_HEADER):
                headers_with_underlines += 1
        
        if line == ENVIRONMENT_HEADER and i+1 < len(formatted_lines):
            underline = formatted_lines[i+1].strip()
            print(f"\nFound Environment Header at line {i}")
            print(f"Next line is: '{underline}'")
            print(f"Expected: '{'-' * len(ENVIRONMENT_HEADER)}'")
            print(f"Match: {underline == '-' * len(ENVIRONMENT_HEADER)}")
            if underline == '-' * len(ENVIRONMENT_HEADER):
                headers_with_underlines += 1
    
    # Final result
    print("\n=== VALIDATION RESULT ===")
    if headers_with_underlines == 3:
        print("✅ SUCCESS: All section headers have proper underlines!")
    else:
        print(f"❌ FAILED: Only {headers_with_underlines}/3 section headers have proper underlines!")

if __name__ == "__main__":
    main()
