#!/usr/bin/env python3
"""
Missing Odds Alert

This module implements a standalone alert that triggers when a match is missing odds data.
Each alert in the live_alerts system is an independent module that handles its own logic.
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, Set, List

# Add project root to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

# Try to import the Telegram alert functionality
try:
    from football.telegram import send_match_alert
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: Telegram module not available, alerts will be printed only")

# Cache to prevent duplicate alerts
alerted_match_conditions = set()

# Constants
ALERT_TYPE = "odds"
EXPECTED_ODDS_TYPES = ["ML", "SPREAD", "Over/Under"]
MINIMUM_MATCH_MINUTE = 3  # Only check matches that have been running for at least 3 minutes

def check_missing_odds_condition(match_data: Dict[str, Any]) -> List[str]:
    """
    Check if a match is missing any expected odds data.
    
    Args:
        match_data: Current match data
        
    Returns:
        List of missing odds types, empty if none missing
    """
    missing_odds = []
    
    # Skip matches that haven't started or are too early
    status_id = str(match_data.get("status_id", ""))
    minute = match_data.get("minute", "0")
    
    # Try to convert minute to integer
    try:
        minute_int = int(minute)
    except (ValueError, TypeError):
        minute_int = 0
    
    # Only check matches that are in-play (status_id 2 or 4) and past minimum minute
    if status_id not in ["2", "4"] or minute_int < MINIMUM_MATCH_MINUTE:
        return []
    
    # Check if odds data exists
    odds_data = match_data.get("odds", {})
    if not odds_data:
        return EXPECTED_ODDS_TYPES  # All odds types are missing
    
    # Check each expected odds type
    for odds_type in EXPECTED_ODDS_TYPES:
        if odds_type not in odds_data or not odds_data[odds_type]:
            missing_odds.append(odds_type)
    
    return missing_odds

def get_alert_condition_key(match_id: str, missing_types: List[str]) -> str:
    """
    Create a unique key for this alert condition to prevent duplicates.
    
    Args:
        match_id: Match identifier
        missing_types: List of missing odds types
        
    Returns:
        Unique condition key string
    """
    return f"{match_id}_{','.join(sorted(missing_types))}"

def format_missing_odds_message(match_data: Dict[str, Any], missing_types: List[str]) -> str:
    """
    Format a missing odds alert message.
    
    Args:
        match_data: Match data dictionary
        missing_types: List of missing odds types
        
    Returns:
        Formatted alert message
    """
    match_id = match_data.get("id", "Unknown")
    home_team = match_data.get("home_team", "Home Team")
    away_team = match_data.get("away_team", "Away Team")
    competition = match_data.get("competition", "Unknown Competition")
    minute = match_data.get("minute", "Unknown")
    
    message = f"⚠️ MISSING ODDS ALERT\n\n"
    message += f"Match: {home_team} vs {away_team}\n"
    message += f"Competition: {competition}\n"
    message += f"Current Minute: {minute}\n\n"
    message += f"Missing odds types:\n"
    
    for odds_type in missing_types:
        message += f"• {odds_type}\n"
    
    message += f"\nMatch ID: {match_id}\n"
    message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return message

def process_match_data(match_data: Dict[str, Any]) -> bool:
    """
    Process match data and trigger an alert if odds data is missing.
    
    Args:
        match_data: Current match data
        
    Returns:
        True if an alert was triggered, False otherwise
    """
    # Check if match data has the necessary fields
    required_fields = ["id", "status_id", "home_team", "away_team", "minute"]
    if not all(field in match_data for field in required_fields):
        return False
    
    # Check if the match is missing odds data
    missing_odds_types = check_missing_odds_condition(match_data)
    if not missing_odds_types:
        return False
    
    # Get match ID and create a unique condition key
    match_id = match_data.get("id", "unknown")
    condition_key = get_alert_condition_key(match_id, missing_odds_types)
    
    # Check for duplicate alerts
    if condition_key in alerted_match_conditions:
        return False
    
    # Generate alert message
    message = format_missing_odds_message(match_data, missing_odds_types)
    
    # Send the alert
    if TELEGRAM_AVAILABLE:
        send_match_alert(
            message=message,
            match_id=match_id,
            teams=f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
            competition=match_data.get("competition"),
            alert_type=ALERT_TYPE
        )
    else:
        # Print to console if Telegram is not available
        print("\n" + "=" * 60)
        print("MISSING ODDS ALERT (Telegram not available)")
        print("=" * 60)
        print(message)
        print("=" * 60 + "\n")
    
    # Add to alerted set to prevent duplicates
    alerted_match_conditions.add(condition_key)
    
    return True

def reset_alert_cache():
    """Reset the alert cache to clear any stored conditions"""
    alerted_match_conditions.clear()

# Example usage if run directly
if __name__ == "__main__":
    # Test the alert with a sample match
    test_match = {
        "id": "12345",
        "home_team": "Manchester United",
        "away_team": "Liverpool",
        "competition": "Premier League",
        "status_id": "2",  # In-play
        "minute": "5",
        "odds": {
            "ML": [{
                "time_of_match": "4",
                "home_win": 150,
                "draw": 280,
                "away_win": 130
            }],
            # Missing SPREAD and Over/Under data
        }
    }
    
    # This should detect missing odds and generate an alert
    alert_triggered = process_match_data(test_match)
    print(f"Alert triggered: {alert_triggered}")
    
    # Test duplicate prevention (should not trigger again)
    alert_triggered = process_match_data(test_match)
    print(f"Second alert triggered: {alert_triggered}")
