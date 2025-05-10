"""
Test alert module to verify the separation between sports alerts and system alerts.
This module checks that sports alerts don't interfere with system alerts.
"""

from typing import Dict, Any, Optional

def process_match_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Test alert for verifying separation between sports alerts and system alerts.
    
    This processes match data and only triggers when specific test conditions are met.
    Using a very specific condition ensures it won't trigger accidentally.
    
    Args:
        match_data: Current match data dictionary
        previous_data: Previous match data for comparison (optional)
        
    Returns:
        True if test conditions are met (specific match ID), False otherwise
    """
    # Get match ID - we'll only trigger for a specific test match ID
    match_id = match_data.get('id', '')
    
    # Only print debugging info, don't try to use system alert channels
    print(f"[TEST_SEPARATION] Processing match {match_id}")
    
    # Extract basic info for logging
    home_team = match_data.get('home_team', 'Unknown')
    away_team = match_data.get('away_team', 'Unknown')
    
    # Check for a test condition - only trigger for matches with IDs ending in "test"
    # This ensures it won't trigger accidentally during normal usage
    if match_id.endswith('test'):
        print(f"[TEST_SEPARATION] 🏆 TRIGGERED sports alert for {home_team} vs {away_team}")
        return True
    
    return False
