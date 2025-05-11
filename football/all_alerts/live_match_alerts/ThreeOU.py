#!/usr/bin/env python3
"""
Three Over/Under Alert Module

This module detects matches with an over/under line of 3.0 or higher.
It reports these matches to the alert system for notification via Telegram.
"""

import logging
from typing import Dict, Any, Optional

# This logger will be replaced by main_match_alerts.py with a specialized logger
logger = logging.getLogger("sports_alerts.ThreeOU")

# Module configuration
CONFIG = {
    "enabled": True,
    "min_ou_line": 3.0,  # Minimum over/under line to trigger an alert
}

# Keep track of processed matches to avoid duplicate alerts
processed_matches = set()

def process_match_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Check if a match has an over/under line of 3.0 or higher.
    
    Args:
        match_data: Current match data from live.py
        previous_data: Previous match data (optional, not used in this module)
        
    Returns:
        Alert data dict or None if no alert should be sent
    """
    # Print at the module level to help diagnose what's happening
    print(f"ThreeOU examining match: {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}")
    
    # Skip if module is disabled
    if not CONFIG["enabled"]:
        return None
        
    # Extract match identifier
    match_id = match_data.get("id", match_data.get("match_id", "unknown"))
    
    # Try different field names for over/under lines
    ou_line = None
    if "ou_handicap" in match_data and match_data["ou_handicap"] is not None:
        ou_line = match_data["ou_handicap"]
    elif "ou_line" in match_data and match_data["ou_line"] is not None:
        ou_line = match_data["ou_line"]
    elif "over_under" in match_data and match_data["over_under"] is not None:
        ou_line = match_data["over_under"]
    
    # Skip if no line available
    if ou_line is None:
        return None
    
    # Convert to float if it is a string
    try:
        if isinstance(ou_line, str):
            ou_line = float(ou_line)
    except (ValueError, TypeError):
        return None
    
    # Create a deduplication key
    dedup_key = f"three_ou_{match_id}_{ou_line}"
    
    # Skip if we have already processed this exact line for this match
    if dedup_key in processed_matches:
        return None
    
    # Track this match as processed
    processed_matches.add(dedup_key)
    
    # Check if line is at or above our threshold
    min_ou_line = CONFIG["min_ou_line"]
    if ou_line >= min_ou_line:
        # Format team names
        home_team = match_data.get("home_team", "Unknown")
        away_team = match_data.get("away_team", "Unknown")
        teams = f"{home_team} vs {away_team}"
        
        # Get competition name
        competition = match_data.get("competition", "Unknown Competition")
        
        # Return alert data
        return {
            "alert_type": "three_ou",
            "match_id": match_id,
            "title": f"{ou_line} Over/Under Alert",
            "message": f"Match has an over/under line of {ou_line}",
            "teams": teams,
            "competition": competition,
            "ou_line": ou_line,
            "home_team": home_team,
            "away_team": away_team,
            "dedup_key": dedup_key
        }
    
    return None

def reset() -> None:
    """
    Reset the module state by clearing the processed matches cache.
    
    This can be called by the main alert system to reset state between sessions.
    """
    processed_matches.clear()
