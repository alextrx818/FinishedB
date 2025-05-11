#!/usr/bin/env python3
"""
Test script to fetch and format live match data using functions from live.py

This script demonstrates how to use the core data fetching and formatting
functions from live.py to get match data in the same format as the main bot.
"""

import asyncio
import aiohttp
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Add the current directory to path to import live.py
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import functions from live.py
from live import (
    fetch_live_matches, fetch_match_details, fetch_match_odds,
    fetch_team_info, fetch_competition_info, fetch_country_data,
    extract_match_ids, extract_team_name, extract_competition_info,
    format_match_odds, format_odds_display, get_status_description,
    get_weather_description, get_eastern_time, AIOHTTP_AVAILABLE
)

# ===================================================================
# Configuration
# ===================================================================

# Time formatting constants
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"
DATE_FORMAT = "%m/%d/%Y"
TIME_FORMAT = "%I:%M:%S %p"

# ===================================================================
# Helper Functions
# ===================================================================

def generate_match_summary(match_data: Dict[str, Any], formatted_odds: Dict[str, Any]) -> str:
    """Generate a formatted match summary string."""
    parts = []
    
    # Match header
    parts.append("\n" + "=" * 50)
    
    # Match info
    parts.append(f"Match ID: {match_data.get('id', 'N/A')}")
    parts.append(f"Status: {get_status_description(match_data.get('status', {}).get('type', 'unknown'))}")
    
    # Teams and score
    home_team = match_data.get('homeTeam', {}).get('name', 'Home Team')
    away_team = match_data.get('awayTeam', {}).get('name', 'Away Team')
    home_score = match_data.get('homeScore', {}).get('current', 0)
    away_score = match_data.get('awayScore', {}).get('current', 0)
    
    parts.append(f"\n{home_team} {home_score} - {away_score} {away_team}")
    
    # Competition info
    competition = match_data.get('tournament', {}).get('name', 'Unknown Competition')
    country = match_data.get('tournament', {}).get('category', {}).get('name', 'Unknown Country')
    parts.append(f"\n{competition} ({country})")
    
    # Match time
    start_time = match_data.get('startTimestamp')
    if start_time:
        try:
            dt = datetime.fromtimestamp(start_time)
            parts.append(f"Kickoff: {dt.strftime('%Y-%m-%d %H:%M')}")
        except (TypeError, ValueError):
            pass
    
    # Weather
    weather = match_data.get('environment', {})
    if weather:
        temp = weather.get('temperature')
        wind = weather.get('wind')
        humidity = weather.get('humidity')
        weather_code = weather.get('weatherCode')
        
        weather_parts = []
        if temp is not None:
            weather_parts.append(f"{temp}°C")
        if wind is not None:
            weather_parts.append(f"Wind: {wind} m/s")
        if humidity is not None:
            weather_parts.append(f"Humidity: {humidity}%")
        if weather_code is not None:
            weather_parts.append(f"Conditions: {get_weather_description(weather_code)}")
            
        if weather_parts:
            parts.append("\nWeather: " + ", ".join(weather_parts))
    
    # Odds
    if formatted_odds:
        parts.append("\n" + format_odds_display(formatted_odds))
    
    parts.append("=" * 50 + "\n")
    
    return "\n".join(parts)

# ===================================================================
# Main Test Function
# ===================================================================

async def fetch_upcoming_matches(session):
    """Fetch upcoming football matches from the API"""
    try:
        url = "https://api.sofascore.com/api/v1/sport/football/scheduled-events"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            return None
    except Exception as e:
        print(f"Error fetching upcoming matches: {e}")
        return None

async def test_live_formatting():
    """Test the live match data fetching and formatting."""
    if not AIOHTTP_AVAILABLE:
        print("Error: aiohttp is required but not available")
        return
    
    print("Starting match data test...")
    
    async with aiohttp.ClientSession() as session:
        try:
            # 1. First try to fetch live matches
            print("Fetching live matches...")
            matches_data = await fetch_live_matches(session)
            
            if not matches_data or 'events' not in matches_data or not matches_data['events']:
                print("No live matches found. Checking for upcoming matches...")
                # Try to fetch upcoming matches if no live matches
                matches_data = await fetch_upcoming_matches(session)
                
                if not matches_data or 'events' not in matches_data or not matches_data['events']:
                    print("No upcoming matches found either.")
                    return
                
                print("Found upcoming matches:")
            else:
                print(f"Found {len(matches_data['events'])} live matches:")
            
            match_ids = extract_match_ids(matches_data)
            
            # 2. Process each match
            for i, match_id in enumerate(match_ids, 1):
                print(f"\nProcessing match {i}/{len(match_ids)} (ID: {match_id})...")
                
                # Fetch match details and odds in parallel
                details_task = fetch_match_details(session, match_id)
                odds_task = fetch_match_odds(session, match_id)
                
                match_data = await details_task
                odds_data = await odds_task
                
                if not match_data or 'event' not in match_data:
                    print(f"  No data for match {match_id}")
                    continue
                
                # Format the odds
                formatted_odds = format_match_odds(odds_data) if odds_data else {}
                
                # Generate and print the match summary
                summary = generate_match_summary(match_data['event'], formatted_odds)
                print(summary)
                
                # Add a small delay between matches to be nice to the API
                await asyncio.sleep(1)
            
            print("\nTest completed successfully!")
            
        except Exception as e:
            print(f"Error in test_live_formatting: {str(e)}")
            import traceback
            traceback.print_exc()

# ===================================================================
# Main Execution
# ===================================================================

if __name__ == "__main__":
    asyncio.run(test_live_formatting())
