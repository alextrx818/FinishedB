#!/usr/bin/env python3
"""
Test script to demonstrate the formatter and normalizer workflow.

This script shows how to use:
1. fetch_all_endpoints.py - For data fetching
2. Formatter_Normalizer.py - For data formatting and normalization
"""

import asyncio
import aiohttp
import json
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add parent directory to path to import Formatter_Normalizer and fetch_all_endpoints
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our formatter and endpoints
from Formatter.Formatter_Normalizer import format_full_match_block, normalize_match_data
from Formatter.fetch_all_endpoints import (
    decimal_to_american, hk_to_american, normalize_match_data as fetch_normalize,
    format_odds_display, generate_match_summary_text
)

# ===================================================================
# Sample Data for Testing
# ===================================================================

# Sample match data that would come from the API
SAMPLE_MATCH = {
    'id': 1234567,
    'startTimestamp': int(datetime.now().timestamp()),
    'homeTeam': {'name': 'Home Team FC', 'id': 123},
    'awayTeam': {'name': 'Away United', 'id': 456},
    'home_team': 'Home Team FC',  # Add direct field access
    'away_team': 'Away United',   # Add direct field access
    'home_score': 2,              # Add direct field access
    'away_score': 1,              # Add direct field access
    'home_ht_score': 1,           # Add direct field access
    'away_ht_score': 0,           # Add direct field access
    'competition': 'Premier League',  # Add direct field access
    'country': 'England',          # Add direct field access
    'competition_id': 8,           # Add direct field access
    'tournament': {
        'name': 'Premier League',
        'category': {'name': 'England'},
        'uniqueTournament': {'id': 8}
    },
    'homeScore': {'current': 2, 'period1': 1},
    'awayScore': {'current': 1, 'period1': 0},
    'status': {'type': 'inprogress', 'description': '2nd Half'},
    'status_description': '2nd Half',  # Add this line to match the expected format
    'status_type': 'inprogress',       # Add direct field access
    'environment': {
        'weatherCode': 2,  # 1=Clear, 2=PartlyCloudy, 3=Cloudy, 4=Rainy, etc.
        'temperature': 22,
        'humidity': 65,
        'wind': 3.2,
        'wind_speed': 3.2,
        'weather_condition': 'Partly Cloudy',
        'pitch_condition': 'Good',
        'home_missing_players': [],
        'away_missing_players': []
    },
    'environment_summary': 'Partly Cloudy, 22°C, Wind: 3.2 m/s',
    'odds': {
        'ML': [
            {'time_of_match': '4', 'home_win': 2.1, 'draw': 3.4, 'away_win': 3.5},
            {'time_of_match': '1', 'home_win': 2.0, 'draw': 3.2, 'away_win': 3.7}
        ],
        'SPREAD': [
            {'time_of_match': '4', 'home_win': 1.9, 'handicap': '-0.5', 'away_win': 2.0},
            {'time_of_match': '1', 'home_win': 1.8, 'handicap': '-0.5', 'away_win': 2.1}
        ],
        'Over/Under': [
            {'time_of_match': '4', 'over': 1.95, 'handicap': '2.5', 'under': 1.95},
            {'time_of_match': '1', 'over': 1.9, 'handicap': '2.5', 'under': 1.9}
        ]
    }
}

# ===================================================================
# Test Functions
# ===================================================================

def test_normalization():
    """Test the normalization of match data."""
    print("\n=== Testing Data Normalization ===")
    
    # Normalize the sample match data
    normalized = normalize_match_data(SAMPLE_MATCH.copy())
    
    print("Original data keys:", list(SAMPLE_MATCH.keys()))
    print("Normalized data keys:", list(normalized.keys()))
    
    # Print some key normalized fields
    print("\nNormalized fields:")
    print(f"Match ID: {normalized.get('id')}")
    print(f"Home: {normalized.get('home_team')} {normalized.get('home_score')}")
    print(f"Away: {normalized.get('away_team')} {normalized.get('away_score')}")
    print(f"Status: {normalized.get('status')}")
    
    # Show odds conversion
    if 'ml_home_american' in normalized:
        print("\nConverted Odds:")
        print(f"Home ML: {normalized.get('ml_home_american'):+d}")
        print(f"Draw ML: {normalized.get('ml_draw_american'):+d}")
        print(f"Away ML: {normalized.get('ml_away_american'):+d}")
        print(f"Spread: {normalized.get('spread_handicap')} ({normalized.get('spread_home_american'):+d}/{normalized.get('spread_away_american'):+d})")
        print(f"Total: {normalized.get('ou_handicap')} (O:{normalized.get('ou_over_american'):+d}/U:{normalized.get('ou_under_american'):+d})")

def test_odds_formatting():
    """Test the odds formatting."""
    print("\n=== Testing Odds Formatting ===")
    
    # Get the odds data
    odds_data = SAMPLE_MATCH.get('odds', {})
    
    # Convert float odds to integers for display
    odds_data_fixed = {}
    for odds_type, odds_list in odds_data.items():
        fixed_list = []
        for entry in odds_list:
            fixed_entry = {}
            for k, v in entry.items():
                if k in ['home_win', 'draw', 'away_win', 'over', 'under'] and isinstance(v, float):
                    fixed_entry[k] = int(round(v * 100))  # Convert to American odds
                else:
                    fixed_entry[k] = v
            fixed_list.append(fixed_entry)
        odds_data_fixed[odds_type] = fixed_list
    
    # Format the odds display
    formatted_odds = format_odds_display(odds_data_fixed)
    
    print("\nFormatted Odds Display:")
    print(formatted_odds)

def test_summary_generation():
    """Test the match summary generation."""
    print("\n=== Testing Match Summary Generation ===")
    
    # Make a copy of the sample match
    match_data = SAMPLE_MATCH.copy()
    
    # Convert float odds to integers for display
    odds_data = match_data.get('odds', {})
    odds_data_fixed = {}
    for odds_type, odds_list in odds_data.items():
        fixed_list = []
        for entry in odds_list:
            fixed_entry = {}
            for k, v in entry.items():
                if k in ['home_win', 'draw', 'away_win', 'over', 'under'] and isinstance(v, float):
                    fixed_entry[k] = int(round(v * 100))  # Convert to American odds
                else:
                    fixed_entry[k] = v
            fixed_list.append(fixed_entry)
        odds_data_fixed[odds_type] = fixed_list
    
    # Update the match data with fixed odds
    match_data['odds'] = odds_data_fixed
    
    # Normalize the data
    normalized = normalize_match_data(match_data)
    
    # Add loop info for display
    normalized['_loop_index'] = 1
    normalized['_total_matches'] = 10
    
    # Generate the summary
    summary = generate_match_summary_text(normalized)
    
    print("\nGenerated Match Summary:")
    print(summary)

def test_full_match_block():
    """Test the full match block formatting."""
    print("\n=== Testing Full Match Block ===")
    
    # Make a copy of the sample match
    match_data = SAMPLE_MATCH.copy()
    
    # Add match numbering info
    match_data['_loop_index'] = 1
    match_data['_total_matches'] = 10
    
    # Convert float odds to integers for display
    odds_data = match_data.get('odds', {})
    odds_data_fixed = {}
    for odds_type, odds_list in odds_data.items():
        fixed_list = []
        for entry in odds_list:
            fixed_entry = {}
            for k, v in entry.items():
                if k in ['home_win', 'draw', 'away_win', 'over', 'under'] and isinstance(v, float):
                    fixed_entry[k] = int(round(v * 100))  # Convert to American odds
                else:
                    fixed_entry[k] = v
            fixed_list.append(fixed_entry)
        odds_data_fixed[odds_type] = fixed_list
    
    # Update the match data with fixed odds
    match_data['odds'] = odds_data_fixed
    
    # Create a full match block
    match_block = format_full_match_block(match_data, set_number=1)
    
    print("\nFull Match Block:")
    print(match_block)

# ===================================================================
# Main Test Function
# ===================================================================

async def test_formatter_flow():
    """Test the complete formatter workflow."""
    print("Starting formatter workflow test...")
    
    # Run all tests
    test_normalization()
    test_odds_formatting()
    test_summary_generation()
    test_full_match_block()
    
    print("\nAll tests completed!")

# ===================================================================
# Main Execution
# ===================================================================

if __name__ == "__main__":
    asyncio.run(test_formatter_flow())
