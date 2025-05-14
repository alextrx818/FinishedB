#!/usr/bin/env python3
"""
format_test.py

Test script to verify the formatting standards from alerter_main.py and formatting_utils.py
"""

import os
import sys

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the formatting utilities 
from formatting_utils import (
    log_alert_with_match_summary,
    setup_alert_logger,
    format_moneyline_odds,
    format_handicap_odds,
    format_overunder_odds,
    MATCH_SUMMARY_HEADER,
    MATCH_SUMMARY_UNDERLINE,
    BETTING_ODDS_HEADER,
    BETTING_ODDS_UNDERLINE,
    ENVIRONMENT_HEADER,
    ENVIRONMENT_UNDERLINE
)

# Import from alerter_main to test its formatting function
from Alerts.alerter_main import format_match_summary

def main():
    # Create a test match object
    test_match = {
        "id": "TEST-FORMAT-12345",
        "competition": {
            "id": "comp-test",
            "name": "Test Competition",
            "country": "Test Country"
        },
        "home_team": {
            "name": "Home Team Test"
        },
        "away_team": {
            "name": "Away Team Test"
        },
        "score": {
            "home": 2,
            "away": 1,
            "home_ht": 1,
            "away_ht": 0
        },
        "status": "In Progress",
        "status_id": 3,
        "odds": {
            "markets": [
                {
                    "type": "MONEYLINE",
                    "home": 1.40,
                    "draw": 2.90,
                    "away": 3.50
                },
                {
                    "type": "SPREAD",
                    "home": 1.25,
                    "handicap": -0.5,
                    "away": 1.80
                },
                {
                    "type": "OVER_UNDER",
                    "over": 1.60,
                    "line": 4.5,
                    "under": 2.40
                }
            ]
        },
        "environment": {
            "temperature": "19°C",
            "humidity": "65%",
            "wind": "10 mph" 
        }
    }
    
    # Get formatted match summary from alerter_main.py
    formatted_summary = format_match_summary(test_match)
    
    print("\n===== TEST: format_match_summary from alerter_main.py =====")
    for line in formatted_summary:
        print(line)
    
    # Check if the formatted summary includes the section headers with underlines
    has_match_summary_underline = False
    has_betting_odds_underline = False
    has_environment_underline = False
    
    for i, line in enumerate(formatted_summary):
        if line == MATCH_SUMMARY_HEADER and i+1 < len(formatted_summary):
            if formatted_summary[i+1] == MATCH_SUMMARY_UNDERLINE:
                has_match_summary_underline = True
                
        if line == BETTING_ODDS_HEADER and i+1 < len(formatted_summary):
            if formatted_summary[i+1] == BETTING_ODDS_UNDERLINE:
                has_betting_odds_underline = True
                
        if line == ENVIRONMENT_HEADER and i+1 < len(formatted_summary):
            if formatted_summary[i+1] == ENVIRONMENT_UNDERLINE:
                has_environment_underline = True
    
    print("\n===== FORMAT VERIFICATION RESULTS =====")
    print(f"Match Summary Underline: {'✓' if has_match_summary_underline else '✗'}")
    print(f"Betting Odds Underline: {'✓' if has_betting_odds_underline else '✗'}")
    print(f"Environment Underline: {'✓' if has_environment_underline else '✗'}")
    
    if has_match_summary_underline and has_betting_odds_underline and has_environment_underline:
        print("\nSUCCESS: All section headers are properly underlined!")
    else:
        print("\nFAILED: Some section headers are missing underlines!")

if __name__ == "__main__":
    main()
