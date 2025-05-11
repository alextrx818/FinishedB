#!/usr/bin/env python3
"""
Test the new standardized alert formatting system with a real match ID.

This script demonstrates how all alert modules can now benefit from the
centralized formatting logic in alert_system.py, ensuring consistent
alert presentation without each module needing to implement formatting.
"""
import sys
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('test_standardized_alerts')

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the alert system
from football.live_alerts.alert_system import format_alert_message, standardize_match_data

# Real match ID to test with
MATCH_ID = "23xmvkh6v38yqg8"

def main():
    """Test the standardized alert formatting with a real match."""
    print("\n=== TESTING STANDARDIZED ALERT FORMATTING ===\n")
    
    # Create sample match data for the specified ID
    match_data = {
        "id": MATCH_ID,
        "home_team": "Hapoel Ramat Gan",
        "away_team": "Maccabi Herzliya",
        "competition": "Israel Leumit League",
        "country": "Israel",
        "status_id": 8,  # Finished
        "status_name": "Finished",
        "home_score": 2,
        "away_score": 0,
        "ht_home_score": 2,
        "ht_away_score": 0,
        "competition_id": "v2y8m4zhv6ql074",
        # Betting odds data
        "ou_handicap": 2.75,
        "ou_over_american": "-125",
        "ou_under_american": "+100",
        "odds_time_minutes": 4,
        "ml_home_american": "-105",
        "ml_draw_american": "+300",
        "ml_away_american": "+210",
        "ah_handicap": 0.25,
        "ah_home_american": "-130",
        "ah_away_american": "+102",
        # Environment data
        "weather": "Clear",
        "temperature": "22°C",
        "humidity": "65%",
        "wind": "5 km/h"
    }
    
    # Create a sample alert from a module (what modules would return)
    alert_data = {
        "match_id": MATCH_ID,
        "home_team": "Hapoel Ramat Gan",
        "away_team": "Maccabi Herzliya",
        "competition": "Israel Leumit League",
        "status": "Finished",
        "status_id": 8,
        "current_score": "2 - 0",
        "ou_line": 2.75,
        "ou_over": "-125",
        "ou_under": "+100",
        "odds_time": 4,
        "alert_type": "3plus_overunder",
        "priority": 85,
        "dedup_key": f"3o_u_{MATCH_ID}"
    }
    
    # Test the new centralized formatting system
    print("\n--- TEST 1: FORMATTING WITH ORIGINAL MATCH DATA ---")
    message = format_alert_message(alert_data, original_match_data=match_data)
    print(message)
    
    print("\n--- TEST 2: SIMPLE FORMATTING (ALERT DATA ONLY) ---")
    simple_message = format_alert_message(alert_data)
    print(simple_message)
    
    # For comparison, show what an alert module would need to do if implementing its own formatting
    print("\n--- FOR COMPARISON: OLD WAY VS NEW WAY ---")
    print("OLD WAY (each module implements formatting):")
    print("  1. Import format_full_match_block")
    print("  2. Create enhanced_match_data with complete odds structure")
    print("  3. Format and include 'full_block' in alert data")
    print("  4. 30-50 lines of code in EACH alert module")
    
    print("\nNEW WAY (centralized in alert_system.py):")
    print("  1. Just return your alert data with core fields")
    print("  2. Zero formatting code needed in modules")
    print("  3. Consistent presentation across all alerts")
    print("  4. Much easier to create new alert modules")

if __name__ == "__main__":
    main()
