#!/usr/bin/env python3
"""
3 OVER/UNDER ALERT MODULE

This module detects live football matches with an over/under line of 3.0 or higher.
It integrates with the alert_system.py to scan all incoming match data.

How it works:
1. Receives normalized match data from alert_system.py
2. Extracts the over/under line value
3. Alerts when the line is >= 3.0
4. Avoids duplicate alerts for the same match

This is a sports alert module for match conditions (over/under betting lines)
and is completely separate from the system alert functionality.
"""

import os
from typing import Dict, Any, Optional
import logging

# Track matches we've already alerted on to avoid duplicates
_alerted_matches = set()

# Threshold for alerting - minimum over/under line
MIN_OVERUNDER_THRESHOLD = 3.0

# No upper limit (None means no maximum threshold)
MAX_OVERUNDER_THRESHOLD = None

# Import utilities from the alert_system module
try:
    from football.live_alerts.alert_system import should_deduplicate_alert
except Exception as e:
    print(f"Error importing alert_system utilities: {e}")

def extract_match_odds(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and normalize odds data from match data.
    
    Args:
        match_data: The normalized match data
        
    Returns:
        Dictionary with extracted odds information
    """
    result = {
        'ou_line': None,
        'ou_over': None,
        'ou_under': None,
    }
    
    # Try to get the over/under line from normalized data
    # The alert_system already converts this to American format
    ou_line = match_data.get('ou_handicap')
    if ou_line is not None:
        result['ou_line'] = float(ou_line)
    
    # Get over/under American odds if available
    result['ou_over'] = match_data.get('ou_over_american')
    result['ou_under'] = match_data.get('ou_under_american')
    
    return result

def process_match_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Process match data to check for over/under alerts.
    
    This function is called by the alert system for each match.
    
    Args:
        match_data: Current match data (normalized)
        previous_data: Previous match data for comparison (optional)
        
    Returns:
        True if alert triggered, False otherwise
    """
    # Get match identifiers
    match_id = match_data.get('id')
    if not match_id:
        return False
    
    # Get match meta information for the alert
    home_team = match_data.get('home_team', 'Unknown Home')
    away_team = match_data.get('away_team', 'Unknown Away')
    competition = match_data.get('competition', 'Unknown Competition')
    
    # Extract the over/under line
    odds_data = extract_match_odds(match_data)
    ou_line = odds_data.get('ou_line')
    
    # Skip if no over/under line available
    if ou_line is None:
        print(f"[3O_U_ALERT] No over/under line for {home_team} vs {away_team}")
        return False
    
    # Debug line to show what was found
    print(f"[3O_U_ALERT] saw Over/Under line: {ou_line}")
    
    # Check if the line meets our criteria
    if ou_line < MIN_OVERUNDER_THRESHOLD:
        print(f"[3O_U_ALERT] Ignoring match with line {ou_line} (below threshold)")
        return False
    
    # Check upper threshold if defined
    if MAX_OVERUNDER_THRESHOLD is not None and ou_line > MAX_OVERUNDER_THRESHOLD:
        print(f"[3O_U_ALERT] Ignoring match with line {ou_line} (above maximum threshold)")
        return False
    
    # Check if we've already alerted on this match
    if match_id in _alerted_matches:
        print(f"[3O_U_ALERT] Already alerted on {home_team} vs {away_team}")
        return False
    
    # Record that we've alerted on this match
    _alerted_matches.add(match_id)
    
    # Trigger the alert
    print(f"[3O_U_ALERT] Processing match #{match_id} with line {ou_line}")
    print(f"[3O_U_ALERT] ALERT! {home_team} vs {away_team} has Over/Under line {ou_line}")
    
    return True

def reset_alert_cache():
    """Reset the alert cache to clear memory."""
    global _alerted_matches
    _alerted_matches.clear()
    print("[3O_U_ALERT] Alert cache reset")
