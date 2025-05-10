#!/usr/bin/env python3
"""
Half-Time Alert

This module implements a standalone alert that triggers when a match reaches half-time.
Each alert in the live_alerts system is an independent module that handles its own logic.
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, Set

# Add project root to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

# Import utilities from the consolidated alert_system module
from football.live_alerts.alert_system import should_deduplicate_alert

# Try to import the Telegram alert functionality
try:
    from football.telegram import send_match_alert
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: Telegram module not available, alerts will be printed only")

# Cache to prevent duplicate alerts
alerted_match_ids = set()

# Constants
ALERT_TYPE = "halftime"
HALF_TIME_STATUS_ID = "3"  # Status ID that indicates half-time

def check_halftime_condition(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Check if a match has just reached half-time.
    
    Args:
        match_data: Current match data
        previous_data: Previous match data to check if this is a new half-time status
        
    Returns:
        True if this is a new half-time status, False otherwise
    """
    # Check if current status is half-time
    current_status_id = str(match_data.get("status_id", ""))
    is_halftime_now = current_status_id == HALF_TIME_STATUS_ID
    
    if not is_halftime_now:
        return False
    
    # If we have previous data, check if this is a new half-time
    if previous_data:
        previous_status_id = str(previous_data.get("status_id", ""))
        # If previously already at half-time, don't trigger again
        if previous_status_id == HALF_TIME_STATUS_ID:
            return False
    
    # This is a new half-time status
    return True

def get_match_identifier(match_data: Dict[str, Any]) -> str:
    """
    Get a unique identifier for a match.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        Unique match identifier string
    """
    match_id = match_data.get("id", "unknown")
    return f"{match_id}"

def format_halftime_message(match_data: Dict[str, Any]) -> str:
    """
    Format a half-time alert message.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        Formatted alert message
    """
    match_id = match_data.get("id", "Unknown")
    home_team = match_data.get("home_team", "Home Team")
    away_team = match_data.get("away_team", "Away Team")
    competition = match_data.get("competition", "Unknown Competition")
    
    # Get the current score
    home_score = match_data.get("home_score", "0")
    away_score = match_data.get("away_score", "0")
    
    message = f"⚽️ HALF-TIME ALERT\n\n"
    message += f"Match: {home_team} vs {away_team}\n"
    message += f"Competition: {competition}\n"
    message += f"Score: {home_score} - {away_score}\n"
    message += f"Half-Time Break\n\n"
    message += f"Match ID: {match_id}\n"
    message += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return message

def process_match_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Process match data and trigger an alert if half-time is reached.
    
    Args:
        match_data: Current match data
        previous_data: Previous match data for comparison
        
    Returns:
        True if an alert was triggered, False otherwise
    """
    # Check if match data has the necessary fields
    required_fields = ["id", "status_id", "home_team", "away_team"]
    if not all(field in match_data for field in required_fields):
        return False
    
    # Check if the match has reached half-time
    if not check_halftime_condition(match_data, previous_data):
        return False
    
    # Get a unique identifier for this match
    match_id = get_match_identifier(match_data)
    
    # Check for duplicate alerts
    if match_id in alerted_match_ids:
        return False
    
    # Generate alert message
    message = format_halftime_message(match_data)
    
    # Send the alert
    if TELEGRAM_AVAILABLE:
        send_match_alert(
            message=message,
            match_id=match_data.get("id"),
            teams=f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
            competition=match_data.get("competition"),
            alert_type=ALERT_TYPE
        )
    else:
        # Print to console if Telegram is not available
        print("\n" + "=" * 60)
        print("HALF-TIME ALERT (Telegram not available)")
        print("=" * 60)
        print(message)
        print("=" * 60 + "\n")
    
    # Add to alerted set to prevent duplicates
    alerted_match_ids.add(match_id)
    
    return True

def reset_alert_cache():
    """Reset the alert cache to clear any stored match IDs"""
    alerted_match_ids.clear()

# Example usage if run directly
if __name__ == "__main__":
    # Test the alert with a sample match
    test_match = {
        "id": "12345",
        "home_team": "Manchester United",
        "away_team": "Liverpool",
        "competition": "Premier League",
        "status_id": "3",  # Half-time status
        "home_score": "1",
        "away_score": "0"
    }
    
    # Previous state (not at half-time)
    prev_match = {
        "id": "12345",
        "status_id": "2"  # First half
    }
    
    # This should detect half-time and generate an alert
    alert_triggered = process_match_data(test_match, prev_match)
    print(f"Alert triggered: {alert_triggered}")
    
    # Test duplicate prevention (should not trigger again)
    alert_triggered = process_match_data(test_match, prev_match)
    print(f"Second alert triggered: {alert_triggered}")
