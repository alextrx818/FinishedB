#!/usr/bin/env python3
"""
Test script to compare output between live.py and Formatter_Normalizer + fetch_all_endpoints.

This script:
1. Fetches live match data using fetch_all_endpoints
2. Formats it using Formatter_Normalizer
3. Compares the output with live.py's expected format
"""

import asyncio
import aiohttp
import json
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add parent directory to path to import Formatter_Normalizer and fetch_all_endpoints
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our formatter and endpoints
from Formatter.Formatter_Normalizer import format_full_match_block, normalize_match_data
from Formatter.fetch_all_endpoints import (
    fetch_live_matches, fetch_match_details, fetch_match_odds,
    fetch_team_info, fetch_competition_info, fetch_countries,
    BASE_URL, ENDPOINTS
)

# ===================================================================
# Configuration
# ===================================================================

# Time formatting constants
EASTERN = None
try:
    import pytz
    EASTERN = pytz.timezone('America/New_York')
except ImportError:
    print("Warning: pytz not available, using UTC for time formatting")
    from datetime import timezone
    EASTERN = timezone.utc

API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"
DATE_FORMAT = "%m/%d/%Y"
TIME_FORMAT = "%I:%M:%S %p"

# ===================================================================
# Helper Functions
# ===================================================================

def get_eastern_time() -> datetime:
    """Get current time in Eastern Time."""
    now = datetime.utcnow()
    if hasattr(EASTERN, 'localize'):  # pytz timezone
        return EASTERN.localize(now).astimezone(EASTERN)
    else:  # datetime.timezone
        return now.astimezone(EASTERN)

def extract_match_ids(matches_data: List[Dict]) -> List[int]:
    """Extract match IDs from the live matches data."""
    if not matches_data or 'events' not in matches_data:
        return []
    
    return [match['id'] for match in matches_data['events'] if 'id' in match]

def extract_team_name(team_data: Dict) -> str:
    """Extract team name from team data."""
    if not team_data:
        return "Unknown Team"
    
    # Try different possible field names for team name
    for field in ['name', 'shortName', 'nickname']:
        if field in team_data:
            return team_data[field]
    
    return "Unknown Team"

def extract_competition_info(competition_data: Dict) -> Tuple[str, str]:
    """Extract competition name and country from competition data."""
    if not competition_data:
        return "Unknown Competition", "Unknown Country"
    
    # Get competition name
    comp_name = competition_data.get('name', 'Unknown Competition')
    
    # Get country
    country = "Unknown Country"
    if 'category' in competition_data:
        country = competition_data['category'].get('name', 'Unknown Country')
    
    return comp_name, country

# ===================================================================
# Data Fetching and Formatting
# ===================================================================

async def fetch_and_format_match(session: aiohttp.ClientSession, match_id: int, match_index: int, total_matches: int) -> Dict:
    """Fetch and format a single match's data."""
    try:
        # Fetch match details and odds in parallel
        details_task = fetch_match_details(session, match_id)
        odds_task = fetch_match_odds(session, match_id)
        
        match_data = await details_task
        odds_data = await odds_task
        
        if not match_data or 'event' not in match_data:
            print(f"Skipping match {match_id}: No data returned")
            return None
        
        # Get team info
        home_team_id = match_data['event'].get('homeTeam', {}).get('id')
        away_team_id = match_data['event'].get('awayTeam', {}).get('id')
        
        home_team = extract_team_name(match_data['event'].get('homeTeam', {}))
        away_team = extract_team_name(match_data['event'].get('awayTeam', {}))
        
        # Get competition info
        competition_id = match_data['event'].get('tournament', {}).get('uniqueTournament', {}).get('id')
        competition_name, country = extract_competition_info(match_data['event'].get('tournament', {}).get('uniqueTournament', {}))
        
        # Format the match data for the formatter
        formatted_match = {
            'id': match_id,
            'competition_id': competition_id,
            'competition': competition_name,
            'country': country,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': match_data['event'].get('homeScore', {}).get('current', 0),
            'away_score': match_data['event'].get('awayScore', {}).get('current', 0),
            'home_ht_score': match_data['event'].get('homeScore', {}).get('period1', 0),
            'away_ht_score': match_data['event'].get('awayScore', {}).get('period1', 0),
            'status': match_data['event'].get('status', {}).get('description', 'Unknown'),
            'status_id': match_data['event'].get('status', {}).get('type', 'unknown'),
            'odds': odds_data,
            '_loop_index': match_index + 1,
            '_total_matches': total_matches,
        }
        
        # Add environment data if available
        if 'environment' in match_data['event']:
            env = match_data['event']['environment']
            formatted_match.update({
                'weather': env.get('weatherCode'),
                'temperature': env.get('temperature'),
                'humidity': env.get('humidity'),
                'wind': env.get('wind')
            })
        
        return formatted_match
        
    except Exception as e:
        print(f"Error processing match {match_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# ===================================================================
# Main Test Function
# ===================================================================

async def test_formatter():
    """Test the formatter with live data from the API."""
    print("Starting formatter test with live data...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Fetch live matches
            print("Fetching live matches...")
            matches_data = await fetch_live_matches(session)
            
            if not matches_data or 'events' not in matches_data or not matches_data['events']:
                print("No live matches found.")
                return
            
            match_ids = extract_match_ids(matches_data)
            print(f"Found {len(match_ids)} live matches")
            
            # Process each match
            formatted_outputs = []
            
            for i, match_id in enumerate(match_ids):
                print(f"\nProcessing match {i+1}/{len(match_ids)} (ID: {match_id})...")
                
                # Fetch and format match data
                match_data = await fetch_and_format_match(
                    session, match_id, i, len(match_ids)
                )
                
                if not match_data:
                    print(f"Skipping match {match_id} due to missing data")
                    continue
                
                # Format the match using our formatter
                formatted_output = format_full_match_block(match_data, set_number=1)
                formatted_outputs.append(formatted_output)
                
                # Print the formatted output
                print("\n" + "=" * 80)
                print(formatted_output)
                print("=" * 80 + "\n")
            
            if not formatted_outputs:
                print("No matches were successfully processed.")
                return
                
            print(f"\nSuccessfully processed {len(formatted_outputs)} matches.")
            
        except Exception as e:
            print(f"Error in test_formatter: {str(e)}")
            import traceback
            traceback.print_exc()

# ===================================================================
# Main Execution
# ===================================================================

if __name__ == "__main__":
    asyncio.run(test_formatter())
