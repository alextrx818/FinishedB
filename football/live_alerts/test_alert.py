"""
Test alert module to verify alert system integration.
This alert will always trigger for testing purposes.
"""

from typing import Dict, Any, Optional

def process_match_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test alert that always returns True for testing the alert system integration.
    
    Args:
        match_data: Current match data
        previous_data: Previous match data (if available)
        
    Returns:
        True to indicate this alert was triggered (always triggers)
    """
    # Extract basic match info for logging
    match_id = match_data.get('id', 'unknown')
    
    # Extract team names safely
    home_team = match_data.get('home_team', 'Unknown Home')
    away_team = match_data.get('away_team', 'Unknown Away')
    
    # Log that this test alert was called
    print(f"[TEST_ALERT] Test alert processing match {match_id}: {home_team} vs {away_team}")
    
    # Always return True to verify alert system is working
    return True
