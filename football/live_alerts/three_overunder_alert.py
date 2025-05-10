#!/usr/bin/env python3
"""
Three Points Over/Under Alert

This sports alert module monitors matches with a total over/under line of at least 3.0 points.
It specifically targets higher-scoring game expectations, which may indicate better scoring opportunities.

This is a SPORTS ALERT module, part of the live_alerts system for analyzing match data,
and is completely separate from the system alert functionality.
"""

import os
from typing import Dict, Any, Optional
import logging

# Minimum over/under threshold to trigger this alert (3.0 or higher)
THREE_OVERUNDER_THRESHOLD = 3.0

# Configure logging
logger = logging.getLogger(__name__)

# Define at module scope so it's available in all functions
# Track matches we've already alerted on to avoid duplicate alerts
alerted_matches = {}

# Import utilities from the consolidated alert_system module
try:
    from football.live_alerts.alert_system import should_deduplicate_alert
except ImportError as e:
    print(f"Error importing alert_system utilities: {e}")
    
# Define a simple extract_match_odds function if import fails
def extract_match_odds(match_data):
    """Simplified match odds extraction fallback"""
    return match_data.get('odds', {})

def process_match_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Process a match to check if its over/under line is 3.0 or higher.
    
    Args:
        match_data: The current match data dictionary
        previous_data: Previous data for the same match (if available)
        
    Returns:
        True if an alert should be triggered, False otherwise
    """
    # Extract match ID and basic info for logging
    match_id = match_data.get('id', 'unknown')
    
    # Extract team names for logging
    home_team = match_data.get('home_team', 'Home Team')
    away_team = match_data.get('away_team', 'Away Team')
    
    # Get over/under line directly from match data (promoted to top level in live.py)
    ou_line = match_data.get('ou_line')
    
    # Skip if we don't have an over/under line
    if not ou_line:
        return False
    
    # Try to convert to float
    try:
        ou_value = float(ou_line)
    except (ValueError, TypeError):
        return False
    
    # Check if the over/under line meets or exceeds our threshold
    if ou_value >= THREE_OVERUNDER_THRESHOLD:
        # Check if we've already alerted on this match
        if should_deduplicate_alert(match_id, 'three_overunder', [f"OU line: {ou_value}"], alerted_matches):
            return False
        
        # Extract related odds for context
        odds = extract_match_odds(match_data)
        
        # Return True to indicate this alert was triggered
        return True
    else:
        # Line is below threshold
        return False

def reset_alert_cache():
    """Reset the alert cache to prevent memory leaks in long-running processes"""
    global alerted_matches
    alerted_matches = {}
    return True
