#!/usr/bin/env python3
"""
final_alignment_test.py

Final test to verify the global formatting standards with correct underlines and alignment.
"""

import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from the core system
from Alerts.alerter_main import format_match_summary
from formatting_utils import setup_alert_logger, log_alert_with_match_summary

def main():
    # Get the absolute path for the logger file
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    logger_file = os.path.join(alerts_dir, "OU3.logger")
    
    # Create a test match with OU3-specific data
    test_match = {
        "id": "TEST-FINAL-123",
        "competition": {"name": "LaLiga", "country": "Spain", "id": "comp-laliga"},
        "home_team": {"name": "Barcelona"},
        "away_team": {"name": "Real Madrid"},
        "score": {"home": 1, "away": 1, "home_ht": 0, "away_ht": 0},
        "status": "Second Half",
        "status_id": 4,
        "odds": {
            "markets": [
                {"type": "MONEYLINE", "home": 1.40, "draw": 2.90, "away": 3.50},
                {"type": "SPREAD", "home": 1.25, "handicap": -0.5, "away": 1.80},
                {"type": "OVER_UNDER", "over": 1.60, "line": 4.5, "under": 2.40}
            ]
        },
        "environment": {
            "temperature": "74.0°F",
            "humidity": "55%",
            "wind": "6.2 mph"
        }
    }
    
    # Format the match summary
    formatted_summary = format_match_summary(test_match)
    
    # Print the formatted summary to check alignment
    print("\n===== FINAL ALERT FORMAT =====")
    print("=" * 80)
    print(f"#X of Y ALERT TRIGGERED: OU3 @ {datetime.now().strftime('%I:%M:%S %p %m/%d/%Y')}")
    print("=" * 80)
    print()
    
    for line in formatted_summary:
        print(line)
    
    # Print specific verification for the odds section
    betting_odds = []
    in_odds_section = False
    for line in formatted_summary:
        if "BETTING ODDS" in line:
            in_odds_section = True
            continue
        if in_odds_section and line.strip() and "ENVIRONMENT" not in line:
            if line.startswith("│"):
                betting_odds.append(line)
    
    if betting_odds:
        print("\n===== BETTING ODDS ALIGNMENT CHECK =====")
        for i, line in enumerate(betting_odds):
            print(f"Line {i+1}: {line}")
        
        # Count characters to verify alignment
        if len(betting_odds) >= 3:
            ou_line = betting_odds[2]
            parts = ou_line.split(BOX_VERTICAL)
            if len(parts) >= 4:
                line_part = parts[2].strip()
                under_part = parts[3].strip()
                print(f"\nLine column value: '{line_part}'")
                print(f"Under column value: '{under_part}'")
                print(f"Character alignment correct: {'Yes' if 'Under' in under_part else 'No'}")

if __name__ == "__main__":
    # Import the box vertical character
    from formatting_utils import BOX_VERTICAL
    main()
