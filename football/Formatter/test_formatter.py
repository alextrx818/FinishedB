#!/usr/bin/env python3
"""
Test script to verify Formatter_Normalizer output matches live.py format.
This script:
1. Fetches live match data from the API
2. Formats it using Formatter_Normalizer
3. Prints the output for comparison with main.logger
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any, Optional

# Add parent directory to path to import Formatter_Normalizer
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Formatter.Formatter_Normalizer import format_full_match_block

# API endpoints (copied from live.py)
BASE_URL = "https://api.sofascore.com"
LIVE_MATCHES_URL = f"{BASE_URL}/api/v1/sport/football/scheduled-events/live"
MATCH_DETAILS_URL = "{}/api/v1/event/{}"  # .format(BASE_URL, match_id)
MATCH_ODDS_URL = "{}/api/v1/event/{}/odds/1/all"  # .format(BASE_URL, match_id)
TEAM_INFO_URL = "{}/api/v1/team/{{}}"  # .format(BASE_URL, team_id)
COMPETITION_INFO_URL = "{}/api/v1/unique-tournament/{{}}"  # .format(BASE_URL, competition_id)
COUNTRIES_URL = f"{BASE_URL}/api/v1/config/unique-tournaments"

# Global session for HTTP requests
session = None

# Cache for team and competition info
team_cache = {}
competition_cache = {}
country_map = {}

async def fetch_json(url: str, params: Optional[Dict] = None) -> Dict:
    """Helper function to fetch JSON data from an API endpoint"""
    if params is None:
        params = {}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        async with session.get(url, params=params, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return {}

async def fetch_live_matches() -> Dict:
    """Fetch all live football matches from the API"""
    return await fetch_json(LIVE_MATCHES_URL)

async def fetch_match_details(match_id: int) -> Dict:
    """Fetch detailed information for a specific match ID"""
    return await fetch_json(MATCH_DETAILS_URL.format(match_id))

async def fetch_match_odds(match_id: int) -> Dict:
    """Fetch odds history for a specific match ID"""
    return await fetch_json(MATCH_ODDS_URL.format(match_id))

async def fetch_team_info(team_id: int) -> Dict:
    """Fetch team information using the team ID (cached)"""
    if team_id in team_cache:
        return team_cache[team_id]
    
    team_data = await fetch_json(TEAM_INFO_URL.format(team_id))
    if team_data:
        team_cache[team_id] = team_data
    
    return team_data

async def fetch_competition_info(competition_id: int) -> Dict:
    """Fetch competition information using the competition ID (cached)"""
    if competition_id in competition_cache:
        return competition_cache[competition_id]
    
    comp_data = await fetch_json(COMPETITION_INFO_URL.format(competition_id))
    if comp_data:
        competition_cache[competition_id] = comp_data
    
    return comp_data

async def fetch_country_data() -> Dict:
    """Fetch all country data"""
    global country_map
    if not country_map:
        data = await fetch_json(COUNTRIES_URL)
        if data and 'groups' in data:
            for group in data['groups']:
                if 'uniqueTournaments' in group:
                    for tournament in group['uniqueTournaments']:
                        country_map[tournament['id']] = tournament.get('category', {}).get('name', 'Unknown')
    return country_map

def extract_team_name(team_data: Dict) -> str:
    """Extract team name from team data"""
    if not team_data or 'team' not in team_data:
        return "Unknown Team"
    return team_data['team'].get('name', 'Unknown Team')

def extract_competition_info(competition_data: Dict) -> tuple:
    """Extract competition name and country from competition data"""
    if not competition_data or 'uniqueTournament' not in competition_data:
        return "Unknown Competition", "Unknown Country"
    
    tournament = competition_data['uniqueTournament']
    comp_name = tournament.get('name', 'Unknown Competition')
    country = tournament.get('category', {}).get('name', 'Unknown Country')
    
    return comp_name, country

async def format_match_data(match_data: Dict) -> Dict:
    """Format match data into the structure expected by Formatter_Normalizer"""
    match_id = match_data.get('id')
    if not match_id:
        return {}
    
    # Fetch additional details
    details = await fetch_match_details(match_id)
    odds_data = await fetch_match_odds(match_id)
    
    # Extract basic match info
    home_team = extract_team_name(details.get('homeTeam', {}))
    away_team = extract_team_name(details.get('awayTeam', {}))
    
    # Get competition info
    competition_name, country = extract_competition_info(details.get('tournament', {}))
    
    # Format the match data structure expected by Formatter_Normalizer
    formatted_match = {
        'id': match_id,
        'competition_id': details.get('tournament', {}).get('uniqueTournament', {}).get('id'),
        'competition': competition_name,
        'country': country,
        'home_team': home_team,
        'away_team': away_team,
        'home_score': details.get('homeScore', {}).get('current', 0),
        'away_score': details.get('awayScore', {}).get('current', 0),
        'home_ht_score': details.get('homeScore', {}).get('period1', ''),
        'away_ht_score': details.get('awayScore', {}).get('period1', ''),
        'status': details.get('status', {}).get('description', 'Unknown'),
        'status_id': details.get('status', {}).get('type', 'unknown'),
        'weather': details.get('venue', {}).get('stadium', {}).get('weather', {}).get('description', 'Unknown'),
        'temperature': details.get('venue', {}).get('stadium', {}).get('weather', {}).get('temperature', {}).get('current', ''),
        'humidity': details.get('venue', {}).get('stadium', {}).get('weather', {}).get('humidity', ''),
        'wind': details.get('venue', {}).get('stadium', {}).get('weather', {}).get('wind', {}).get('speed', ''),
        '_loop_index': 1,  # For testing
        '_total_matches': 1  # For testing
    }
    
    # Format odds data if available
    formatted_odds = {}
    if odds_data and 'all' in odds_data:
        # This is a simplified version - you'll need to implement the actual odds formatting
        # based on the format_match_odds function in live.py
        formatted_odds = {
            'ML': [{
                'time_of_match': '5',  # Example time
                'home_win': 150,      # Example odds
                'draw': 250,          # Example odds
                'away_win': -110      # Example odds
            }],
            'SPREAD': [{
                'time_of_match': '5',
                'home_win': -110,
                'handicap': '+1.5',
                'away_win': -110
            }],
            'Over/Under': [{
                'time_of_match': '5',
                'over': -110,
                'handicap': '2.5',
                'under': -110
            }]
        }
    
    return formatted_match, formatted_odds

def get_mock_match_data():
    """Return mock match data for testing"""
    return {
        'id': 1234567,
        'competition_id': 35,
        'competition': 'Premier League',
        'country': 'England',
        'home_team': 'Arsenal',
        'away_team': 'Chelsea',
        'home_score': 2,
        'away_score': 1,
        'home_ht_score': '1',
        'away_ht_score': '0',
        'status': '2nd Half',
        'status_id': 'inprogress',
        'weather': 'Clear',
        'temperature': '18',
        'humidity': '65',
        'wind': '12',
        '_loop_index': 1,
        '_total_matches': 5
    }

def get_mock_odds_data():
    """Return mock odds data for testing"""
    return {
        'ML': [{
            'time_of_match': '5',
            'home_win': -110,
            'draw': +250,
            'away_win': +300
        }],
        'SPREAD': [{
            'time_of_match': '5',
            'home_win': -110,
            'handicap': '-0.5',
            'away_win': -110
        }],
        'Over/Under': [{
            'time_of_match': '5',
            'over': -110,
            'handicap': '2.5',
            'under': -110
        }]
    }

async def test_formatter():
    """Test the formatter with mock data"""
    try:
        # Try to fetch live data first
        print("Attempting to fetch live matches...")
        async with aiohttp.ClientSession() as session:
            live_matches = await fetch_live_matches()
            
            if live_matches and 'events' in live_matches and live_matches['events']:
                # Use live data if available
                print("Using live match data...")
                match_data = live_matches['events'][0]
                formatted_match, formatted_odds = await format_match_data(match_data)
                if not formatted_match:
                    raise Exception("Failed to format live match data")
            else:
                # Fall back to mock data
                print("No live matches found, using mock data...")
                formatted_match = get_mock_match_data()
                formatted_odds = get_mock_odds_data()
    except Exception as e:
        print(f"Error fetching live data, using mock data: {e}")
        formatted_match = get_mock_match_data()
        formatted_odds = get_mock_odds_data()
    
    # Generate the formatted output
    print("\n" + "=" * 70)
    print("FORMATTED OUTPUT (for comparison with main.logger)".center(70))
    print("=" * 70)
    
    output = format_full_match_block(formatted_match, formatted_odds)
    print(output)
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE".center(70))
    print("=" * 70)
    print("Compare the above output with the format in main.logger".center(70))
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_formatter())
