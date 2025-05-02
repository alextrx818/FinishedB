import logger.main_logger
import logger.log_filters.pnts3_start.pnts3_start

import requests
import json
import time
from functools import lru_cache
import sys
import traceback
import argparse
import datetime
import pytz
import signal
import threading
import os
import fcntl

# Record when the script started
START_TIME = datetime.datetime.now()

# Create a single session for all API calls
session = requests.Session()

# API credentials
USER = "thenecpt"
SECRET = "0c55322e8e196d6ef9066fa4252cf386"

# Define standard datetime formats as constants
DATE_FORMAT = "%m/%d/%Y"
TIME_FORMAT = "%I:%M:%S %p ET"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
CONSOLE_TIME_FORMAT = "%I:%M:%S %p ET"  # For console output only
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"  # For APIs and data

def fetch_live_matches():
    """
    Fetch all live football matches from the API
    """
    url = "https://api.thesports.com/v1/football/match/detail_live"
    params = {
        "user": USER,
        "secret": SECRET
    }
    
    try:
        print("Fetching live matches...")
        response = session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching live matches: {e}")
        return None

def fetch_match_details(match_id):
    """
    Fetch detailed information for a specific match ID
    """
    url = "https://api.thesports.com/v1/football/match/recent/list"
    params = {
        "user": USER,
        "secret": SECRET,
        "uuid": match_id
    }
    
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching details for match {match_id}: {e}")
        return None

@lru_cache(maxsize=None)
def fetch_team_info(team_id):
    """
    Fetch team information using the team ID (cached)
    """
    url = "https://api.thesports.com/v1/football/team/additional/list"
    params = {
        "user": USER,
        "secret": SECRET,
        "uuid": team_id
    }
    
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching team info for {team_id}: {e}")
        return None

@lru_cache(maxsize=None)
def fetch_competition_info(competition_id):
    """
    Fetch competition information using the competition ID (cached)
    """
    url = "https://api.thesports.com/v1/football/competition/additional/list"
    params = {
        "user": USER,
        "secret": SECRET,
        "uuid": competition_id
    }
    
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching competition info for {competition_id}: {e}")
        return None

def fetch_country_data():
    """
    Fetch all country data
    """
    url = "https://api.thesports.com/v1/football/country/list"
    params = {
        "user": USER,
        "secret": SECRET
    }
    
    try:
        print("Fetching country data...")
        response = session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching country data: {e}")
        return None

def extract_match_ids(matches_data):
    """
    Extract all match IDs from the live matches data
    """
    match_ids = []
    
    if not matches_data or "results" not in matches_data:
        return match_ids
    
    for match in matches_data["results"]:
        if "id" in match:
            match_ids.append(match["id"])
    
    return match_ids

def extract_team_name(team_data):
    """
    Extract team name from team data
    """
    if not team_data or "code" not in team_data or team_data["code"] != 0:
        return "Unknown Team"
    
    if "results" not in team_data or not team_data["results"]:
        return "Unknown Team"
    
    team_results = team_data["results"]
    team = team_results[0] if isinstance(team_results, list) and team_results else team_results
    
    return team.get("name", "Unknown Team")

def extract_competition_info(competition_data):
    """
    Extract competition name and country ID from competition data
    """
    competition_name = "Unknown Competition"
    country_id = ""
    
    if not competition_data or "code" not in competition_data or competition_data["code"] != 0:
        return competition_name, country_id
    
    if "results" not in competition_data or not competition_data["results"]:
        return competition_name, country_id
    
    comp_results = competition_data["results"]
    comp = comp_results[0] if isinstance(comp_results, list) and comp_results else comp_results
    
    competition_name = comp.get("name", "Unknown Competition")
    
    # Extract country ID if available
    # Check different possible locations for country ID
    if "country_id" in comp:
        country_id = comp.get("country_id", "")
    elif "country" in comp and comp["country"]:
        if isinstance(comp["country"], dict):
            country_id = comp["country"].get("id", "")
        else:
            country_id = comp["country"]
    
    return competition_name, country_id

def create_country_id_to_name_map(country_data):
    """
    Create a dictionary mapping country IDs to country names
    """
    country_map = {}
    
    if not country_data or "code" not in country_data or country_data["code"] != 0:
        return country_map
    
    if "results" not in country_data or not country_data["results"]:
        return country_map
    
    for country in country_data["results"]:
        if "id" in country and "name" in country:
            country_map[country["id"]] = country["name"]
    
    return country_map

def get_weather_description(weather_code):
    """
    Convert numeric weather code to a human-readable description
    """
    weather_codes = {
        "1": "Partially cloudy",
        "2": "Cloudy",
        "3": "Foggy",
        "4": "Rainy",
        "5": "Sunny",
        "6": "Snowy",
        "7": "Windy"
    }
    
    # Handle both string and integer codes
    if isinstance(weather_code, str) and weather_code.isdigit():
        code = weather_code
    elif isinstance(weather_code, int):
        code = str(weather_code)
    else:
        code = str(weather_code)
    
    return weather_codes.get(code, f"Unknown ({code})")

def celsius_to_fahrenheit(celsius_str):
    """
    Convert celsius temperature string to fahrenheit
    """
    try:
        # Extract numeric part from temperature string (e.g., "20°C" -> "20")
        celsius_value = float(celsius_str.replace('°C', '').strip())
        # Convert to Fahrenheit: F = (C * 9/5) + 32
        fahrenheit_value = (celsius_value * 9/5) + 32
        return f"{fahrenheit_value:.1f}°F"
    except (ValueError, AttributeError):
        return celsius_str  # Return original if conversion fails

def meters_per_second_to_mph(mps_str):
    """
    Convert wind speed from m/s to mph
    """
    try:
        # Extract numeric part from wind string (e.g., "2.0m/s" -> "2.0")
        mps_value = float(mps_str.replace('m/s', '').strip())
        # Convert to mph: 1 m/s = 2.237 mph
        mph_value = mps_value * 2.237
        return f"{mph_value:.1f} mph"
    except (ValueError, AttributeError):
        return mps_str  # Return original if conversion fails

def fetch_match_odds(match_id):
    """
    Fetch odds history for a specific match ID
    """
    url = "https://api.thesports.com/v1/football/odds/history"
    params = {
        "user": USER,
        "secret": SECRET,
        "uuid": match_id
    }
    
    try:
        response = session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching odds for match {match_id}: {e}")
        return None

def decimal_to_american(decimal_odds):
    """
    Convert decimal odds to American odds (int value)
    For odds > 2.0: (decimal - 1) * 100
    For odds < 2.0: -100 / (decimal - 1)
    """
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds == 0:
            return 0
        
        if decimal_odds >= 2.0:
            return int(round((decimal_odds - 1) * 100))
        else:
            return int(round(-100 / (decimal_odds - 1)))
    except (ValueError, ZeroDivisionError):
        return 0

def decimal_to_american_str(decimal_odds):
    """
    Convert decimal odds to American odds with + or - prefix
    """
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds == 0:
            return "0"
            
        if decimal_odds >= 2.0:
            return f"+{int(round((decimal_odds - 1) * 100))}"
        else:
            return f"{int(round(-100 / (decimal_odds - 1)))}"
    except (ValueError, ZeroDivisionError):
        return "0"

def hk_to_american(hk_odds):
    """
    Convert Hong Kong odds to American odds (int value)
    """
    try:
        hk_odds = float(hk_odds)
        if hk_odds >= 1:
            return int(round(hk_odds * 100))
        else:
            return int(round(-100 / hk_odds))
    except (ValueError, ZeroDivisionError):
        return 0

def hk_to_american_str(hk_odds):
    """
    Convert Hong Kong odds to American odds with + or - prefix
    """
    try:
        hk_odds = float(hk_odds)
        if hk_odds >= 1:
            return f"+{int(round(hk_odds * 100))}"
        else:
            return f"{int(round(-100 / hk_odds))}"
    except (ValueError, ZeroDivisionError):
        return "0"

def format_match_odds(odds_data):
    """
    Format the odds data according to the required structure:
    - SPREAD (Asia handicap)
    - ML (European odds)
    - Over/Under (Big Small)
    
    Filter all odds types to only include minutes 4-6
    """
    if not odds_data or "code" not in odds_data or odds_data["code"] != 0:
        return {}
    
    if "results" not in odds_data:
        return {}
    
    formatted_odds = {
        "SPREAD": [],
        "ML": [],
        "Over/Under": []
    }
    
    # Handle the case where results is a dictionary rather than a list
    results = odds_data["results"]
    
    # The structure is {"results": {"bookmaker_id": {"odds_type": [odds_entries]}}}
    for bookmaker_id, bookmaker_data in results.items():
        # Process Asia handicap (SPREAD)
        if "asia" in bookmaker_data:
            target_minutes_entries = []
            other_entries = []
            
            for asia_entry in bookmaker_data["asia"]:
                if len(asia_entry) >= 5:
                    time_of_match = asia_entry[1] if asia_entry[1] else "pre-match"
                    home_win_hk = asia_entry[2]
                    handicap = asia_entry[3]
                    away_win_hk = asia_entry[4]
                    
                    spread_entry = {
                        "time_of_match": time_of_match,
                        "home_win": hk_to_american(home_win_hk),
                        "handicap": handicap,
                        "away_win": hk_to_american(away_win_hk)
                    }
                    
                    # Check if time_of_match is numeric
                    try:
                        minute = int(time_of_match) if time_of_match.isdigit() else 0
                        # Only include minutes 4-6 as requested
                        if minute >= 4 and minute <= 6:
                            target_minutes_entries.append(spread_entry)
                        else:
                            other_entries.append(spread_entry)
                    except (ValueError, TypeError):
                        # Not a numeric minute, add to other entries
                        other_entries.append(spread_entry)
            
            # Add target minutes entries if they exist (prioritized)
            if target_minutes_entries:
                formatted_odds["SPREAD"].extend(target_minutes_entries)
            # Otherwise add the other entries
            elif other_entries:
                formatted_odds["SPREAD"].extend(other_entries)
        
        # Process European odds (ML) - ONLY FOR BOOKMAKER 2
        if bookmaker_id == "2" and "eu" in bookmaker_data:
            target_minutes_entries = []
            other_entries = []
            
            for euro_entry in bookmaker_data["eu"]:
                if len(euro_entry) >= 5:
                    time_of_match = euro_entry[1] if euro_entry[1] else "pre-match"
                    home_win_decimal = float(euro_entry[2])  # Home win odds (decimal)
                    draw_decimal = float(euro_entry[3])      # Draw odds (decimal)
                    away_win_decimal = float(euro_entry[4])  # Away win odds (decimal)
                    
                    # Skip conversion if any odds value is exactly 1.0
                    if home_win_decimal == 1.0 or draw_decimal == 1.0 or away_win_decimal == 1.0:
                        continue
                    
                    # Directly apply the conversion formula
                    if home_win_decimal >= 2.0:
                        home_win = int(round((home_win_decimal - 1) * 100))
                    else:
                        home_win = int(round(-100 / (home_win_decimal - 1)))
                        
                    if draw_decimal >= 2.0:
                        draw = int(round((draw_decimal - 1) * 100))
                    else:
                        draw = int(round(-100 / (draw_decimal - 1)))
                        
                    if away_win_decimal >= 2.0:
                        away_win = int(round((away_win_decimal - 1) * 100))
                    else:
                        away_win = int(round(-100 / (away_win_decimal - 1)))
                    
                    ml_entry = {
                        "time_of_match": time_of_match,
                        "home_win": home_win,
                        "draw": draw,
                        "away_win": away_win
                    }
                    
                    # Check if time_of_match is numeric
                    try:
                        minute = int(time_of_match) if time_of_match.isdigit() else 0
                        # Only include minutes 4-6 as requested
                        if minute >= 4 and minute <= 6:
                            target_minutes_entries.append(ml_entry)
                        else:
                            other_entries.append(ml_entry)
                    except (ValueError, TypeError):
                        # Not a numeric minute, add to other entries
                        other_entries.append(ml_entry)
                        
            # Add target minutes entries if they exist (prioritized)
            if target_minutes_entries:
                formatted_odds["ML"].extend(target_minutes_entries)
            # Otherwise add the other entries
            elif other_entries:
                formatted_odds["ML"].extend(other_entries)
        
        # Process Big Small (Over/Under)
        if "bs" in bookmaker_data:
            target_minutes_entries = []
            other_entries = []
            
            for bs_entry in bookmaker_data["bs"]:
                if len(bs_entry) >= 5:
                    time_of_match = bs_entry[1] if bs_entry[1] else "pre-match"
                    over_hk = bs_entry[2]
                    points_total = bs_entry[3]
                    under_hk = bs_entry[4]
                    
                    ou_entry = {
                        "time_of_match": time_of_match,
                        "over": hk_to_american(over_hk),
                        "handicap": points_total,
                        "under": hk_to_american(under_hk)
                    }
                    
                    # Check if time_of_match is numeric
                    try:
                        minute = int(time_of_match) if time_of_match.isdigit() else 0
                        # Only include minutes 4-6 as requested
                        if minute >= 4 and minute <= 6:
                            target_minutes_entries.append(ou_entry)
                        else:
                            other_entries.append(ou_entry)
                    except (ValueError, TypeError):
                        # Not a numeric minute, add to other entries
                        other_entries.append(ou_entry)
            
            # Add target minutes entries if they exist (prioritized)
            if target_minutes_entries:
                formatted_odds["Over/Under"].extend(target_minutes_entries)
            # Otherwise add the other entries
            elif other_entries:
                formatted_odds["Over/Under"].extend(other_entries)
    
    return formatted_odds

def get_latest_odds(odds_data, odds_type):
    """
    Get the latest odds entry for a specific odds type, prioritizing early game odds,
    with special handling for ML odds (minutes 4-6)
    """
    if not odds_data or odds_type not in odds_data or not odds_data[odds_type]:
        return None
    
    # For ML (Money Line), specifically prioritize minutes 4, 5, and 6
    if odds_type == "ML":
        # Find entries from minutes 4, 5, or 6 (specifically for ML odds)
        early_minutes = [entry for entry in odds_data[odds_type] 
                        if entry["time_of_match"] in ["4", "5", "6"]]
        
        # If we have early minute entries, return the latest one
        if early_minutes:
            return early_minutes[-1]
        
        # Otherwise return the latest entry
        return odds_data[odds_type][-1]
        
    # For SPREAD and Over/Under, filter entries to only include minutes 0-3 or minutes ≥ 7 (skip minutes 4-6)
    valid_entries = []
    for entry in odds_data[odds_type]:
        time_of_match = entry.get("time_of_match", "")
        try:
            # Try to convert to integer if it's a digit string
            if isinstance(time_of_match, str) and time_of_match.isdigit():
                minute = int(time_of_match)
                # Keep minutes 0-3 or minutes ≥ 7 (skip minutes 4-6)
                if minute <= 3 or minute >= 7:
                    valid_entries.append(entry)
            else:
                # Non-numeric time, add it
                valid_entries.append(entry)
        except (ValueError, TypeError):
            # Not convertible to integer, add it
            valid_entries.append(entry)
    
    # If no valid entries after filtering, return None
    if not valid_entries:
        return None
    
    # Separate early minutes (0-3) from other valid minutes
    early_minutes = [entry for entry in valid_entries 
                    if isinstance(entry.get("time_of_match", ""), str) 
                    and entry["time_of_match"].isdigit() 
                    and int(entry["time_of_match"]) <= 3]
    
    # If we have early minute entries, return the latest one
    if early_minutes:
        return early_minutes[-1]
    
    # Otherwise return the latest valid entry
    return valid_entries[-1]

# Now implementing parallelization with ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor, as_completed

def format_american_odds(odds_value):
    """Format American odds with consistent sign display."""
    return f"{odds_value:+d}"

def format_odds_display(formatted_odds):
    """
    Format the odds for display
    """
    if not formatted_odds:
        return "No odds data available"
    
    output_lines = []
    
    # Format ML (Money Line) - European odds
    if "ML" in formatted_odds and formatted_odds["ML"]:
        ml_entries = formatted_odds["ML"]
        
        # Sort by time to find the closest entries to minutes 4-6
        # Convert time_of_match to int where possible for better sorting
        def get_time_value(entry):
            time_str = entry.get("time_of_match", "")
            try:
                if time_str.isdigit():
                    return int(time_str)
                return 1000  # Large number for non-numeric times
            except (ValueError, AttributeError):
                return 1000
                
        # Sort the entries by time
        ml_entries.sort(key=get_time_value)
        
        # Try to find an entry from minutes 4-6
        target_minutes = ["4", "5", "6"]
        ml_entry = None
        
        # First pass: check for exact match in minutes 4-6
        for entry in ml_entries:
            time_of_match = entry.get("time_of_match", "")
            if time_of_match in target_minutes:
                ml_entry = entry
                break
        
        # If no entry from minutes 4-6, find the closest minute
        if not ml_entry and ml_entries:
            # Create entries with numeric times and non-numeric times
            numeric_entries = []
            non_numeric_entries = []
            
            for entry in ml_entries:
                time_str = entry.get("time_of_match", "")
                if time_str.isdigit():
                    numeric_entries.append((int(time_str), entry))
                else:
                    non_numeric_entries.append(entry)
            
            # Find the closest numeric time to the target range (4-6)
            if numeric_entries:
                # Sort by distance to the target range (middle is 5)
                numeric_entries.sort(key=lambda x: min(abs(x[0] - 4), abs(x[0] - 5), abs(x[0] - 6)))
                ml_entry = numeric_entries[0][1]
            else:
                # If no numeric entries, use the first non-numeric entry
                ml_entry = non_numeric_entries[0] if non_numeric_entries else None
        
        if ml_entry:
            ml_time = ml_entry.get("time_of_match", "Unknown")
            ml_home_win = ml_entry.get("home_win", 0)
            ml_draw = ml_entry.get("draw", 0)
            ml_away_win = ml_entry.get("away_win", 0)
            
            # Add a note if this is not from the target minutes 4-6
            minutes_note = ""
            if ml_time not in target_minutes:
                minutes_note = f" (Closest time to minutes 4-6 available: {ml_time})"
            
            output_lines.append("ML (Money Line):")
            output_lines.append(f"Time: {ml_time} min | Home: {format_american_odds(ml_home_win)} | Draw: {format_american_odds(ml_draw)} | Away: {format_american_odds(ml_away_win)}{minutes_note}")
    
    # Display SPREAD (Asia handicap)
    if "SPREAD" in formatted_odds and formatted_odds["SPREAD"]:
        spread_entries = formatted_odds["SPREAD"]
        
        # Sort entries by time for finding closest match
        def get_time_value(entry):
            time_str = entry.get("time_of_match", "")
            try:
                if time_str.isdigit():
                    return int(time_str)
                return 1000  # Large number for non-numeric times
            except (ValueError, AttributeError):
                return 1000
                
        # Sort the entries by time
        spread_entries.sort(key=get_time_value)
        
        # Try to find an entry from minutes 4-6
        target_minutes = ["4", "5", "6"]
        spread_entry = None
        
        # First pass: check for exact match in minutes 4-6
        for entry in spread_entries:
            time_of_match = entry.get("time_of_match", "")
            if time_of_match in target_minutes:
                spread_entry = entry
                break
        
        # If no entry from minutes 4-6, find the closest minute
        if not spread_entry and spread_entries:
            # Create entries with numeric times and non-numeric times
            numeric_entries = []
            non_numeric_entries = []
            
            for entry in spread_entries:
                time_str = entry.get("time_of_match", "")
                if time_str.isdigit():
                    numeric_entries.append((int(time_str), entry))
                else:
                    non_numeric_entries.append(entry)
            
            # Find the closest numeric time to the target range (4-6)
            if numeric_entries:
                # Sort by distance to the target range (middle is 5)
                numeric_entries.sort(key=lambda x: min(abs(x[0] - 4), abs(x[0] - 5), abs(x[0] - 6)))
                spread_entry = numeric_entries[0][1]
            else:
                # If no numeric entries, use the first non-numeric entry
                spread_entry = non_numeric_entries[0] if non_numeric_entries else None
                
        if spread_entry:
            spread_time = spread_entry.get("time_of_match", "Unknown")
            home_odds = format_american_odds(spread_entry.get("home_win", 0))
            handicap = spread_entry.get("handicap", 0)
            away_odds = format_american_odds(spread_entry.get("away_win", 0))
            
            # Add a note if this is not from the target minutes 4-6
            minutes_note = ""
            if spread_time not in target_minutes:
                minutes_note = f" (Closest time to minutes 4-6 available: {spread_time})"
                
            output_lines.append("\nSPREAD (Asia Handicap):")
            output_lines.append(f"Time: {spread_time} min | Home: {home_odds} | Handicap: {handicap} | Away: {away_odds}{minutes_note}")
    
    # Display Over/Under
    if "Over/Under" in formatted_odds and formatted_odds["Over/Under"]:
        ou_entries = formatted_odds["Over/Under"]
        
        # Sort entries by time for finding closest match
        def get_time_value(entry):
            time_str = entry.get("time_of_match", "")
            try:
                if time_str.isdigit():
                    return int(time_str)
                return 1000  # Large number for non-numeric times
            except (ValueError, AttributeError):
                return 1000
                
        # Sort the entries by time
        ou_entries.sort(key=get_time_value)
        
        # Try to find an entry from minutes 4-6
        target_minutes = ["4", "5", "6"]
        ou_entry = None
        
        # First pass: check for exact match in minutes 4-6
        for entry in ou_entries:
            time_of_match = entry.get("time_of_match", "")
            if time_of_match in target_minutes:
                ou_entry = entry
                break
        
        # If no entry from minutes 4-6, find the closest minute
        if not ou_entry and ou_entries:
            # Create entries with numeric times and non-numeric times
            numeric_entries = []
            non_numeric_entries = []
            
            for entry in ou_entries:
                time_str = entry.get("time_of_match", "")
                if time_str.isdigit():
                    numeric_entries.append((int(time_str), entry))
                else:
                    non_numeric_entries.append(entry)
            
            # Find the closest numeric time to the target range (4-6)
            if numeric_entries:
                # Sort by distance to the target range (middle is 5)
                numeric_entries.sort(key=lambda x: min(abs(x[0] - 4), abs(x[0] - 5), abs(x[0] - 6)))
                ou_entry = numeric_entries[0][1]
            else:
                # If no numeric entries, use the first non-numeric entry
                ou_entry = non_numeric_entries[0] if non_numeric_entries else None
        
        if ou_entry:
            ou_time = ou_entry.get("time_of_match", "Unknown")
            over_odds = format_american_odds(ou_entry.get("over", 0))
            handicap = ou_entry.get("handicap", 0)
            under_odds = format_american_odds(ou_entry.get("under", 0))
            
            # Add a note if this is not from the target minutes 4-6
            minutes_note = ""
            if ou_time not in target_minutes:
                minutes_note = f" (Closest time to minutes 4-6 available: {ou_time})"
                
            output_lines.append("\nOver/Under:")
            output_lines.append(f"Time: {ou_time} min | Over: {over_odds} | Line: {handicap} | Under: {under_odds}{minutes_note}")
    
    return "\n".join(output_lines)

def get_status_description(status_id):
    """
    Convert numeric status_id to a human-readable description
    """
    status_mapping = {
        "1": "Not started",
        "2": "First half",
        "3": "Half-time break",
        "4": "Second half",
        "5": "Extra time",
        "6": "Penalty shootout",
        "7": "Finished",
        "8": "Finished",
        "9": "Postponed",
        "10": "Canceled",
        "11": "To be announced",
        "12": "Interrupted",
        "13": "Abandoned",
        "14": "Suspended",
    }
    
    # Handle both string and integer status codes
    if isinstance(status_id, int):
        code = str(status_id)
    else:
        code = str(status_id)
    
    return status_mapping.get(code, f"Unknown (ID: {code})")

def get_eastern_time():
    """Get current time in Eastern timezone"""
    utc_now = datetime.datetime.now(pytz.utc)
    eastern = pytz.timezone('America/New_York')
    eastern_time = utc_now.astimezone(eastern)
    return eastern_time

def send_telegram_alert(message, token="7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko", chat_id="6128359776"):
    """Send an alert message via Telegram"""
    timestamp = get_eastern_time().strftime(API_DATETIME_FORMAT)
    telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
    formatted_message = f"{message}\n\nTimestamp: {timestamp}"
    
    try:
        response = requests.post(
            telegram_url,
            json={
                "chat_id": chat_id,
                "text": formatted_message,
                "parse_mode": "HTML"
            }
        )
        if response.status_code == 200:
            print(f"Successfully sent Telegram alert: {message}")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

def get_uptime_status():
    """Generate a formatted status message about the application's uptime"""
    now = datetime.datetime.now()
    uptime = now - START_TIME
    
    # Calculate hours, minutes, seconds
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format the uptime string
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    # Convert START_TIME to Eastern Time
    eastern = pytz.timezone('America/New_York')
    utc_start = pytz.utc.localize(START_TIME.replace(tzinfo=None))
    start_time_et = utc_start.astimezone(eastern)
    
    # Format the message with HTML formatting for Telegram
    message = f"📊 <b>LIVE.PY STATUS REPORT</b>\n\n"
    message += f"• <b>Started at:</b> {start_time_et.strftime(API_DATETIME_FORMAT)}\n"
    message += f"• <b>Current uptime:</b> {uptime_str}\n"
    message += f"• <b>Running process ID:</b> {os.getpid()}\n"
    
    return message

def handle_sigusr1(signum, frame):
    """Signal handler for SIGUSR1 to report uptime status via Telegram"""
    status_message = get_uptime_status()
    send_telegram_alert(status_message)

def telegram_listener(token="7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko", chat_id="6128359776"):
    """
    Background thread that listens for status requests from Telegram
    Processes /status commands sent to the bot
    """
    telegram_url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = None
    
    print(f"[Telegram Listener] Started with token: {token[:8]}... and chat_id: {chat_id}")
    
    while True:
        try:
            params = {
                "timeout": 30,
                "allowed_updates": ["message"]
            }
            
            if offset:
                params["offset"] = offset
            
            print(f"[Telegram Listener] Polling for updates with params: {params}")
            response = requests.get(telegram_url, params=params)
            
            if response.status_code == 200:
                updates = response.json()
                print(f"[Telegram Listener] Response: {json.dumps(updates)[:300]}...")
                
                if "result" in updates and updates["result"]:
                    print(f"[Telegram Listener] Received {len(updates['result'])} updates")
                    for update in updates["result"]:
                        # Update offset to acknowledge this update
                        offset = update["update_id"] + 1
                        print(f"[Telegram Listener] Processing update {update['update_id']}: {json.dumps(update)[:150]}...")
                        
                        # Check if this is a message with text
                        if "message" in update and "text" in update["message"]:
                            message_text = update["message"]["text"]
                            message_chat_id = str(update["message"]["chat"]["id"])
                            print(f"[Telegram Listener] Message: '{message_text}' from chat_id: {message_chat_id}, expected chat_id: {chat_id}")
                            
                            # Check if this is a status command from the configured chat
                            if message_text.lower() == "/status" and message_chat_id == chat_id:
                                print(f"[Telegram Listener] Status command received from authorized chat")
                                status_message = get_uptime_status()
                                print(f"[Telegram Listener] Sending status message: {status_message[:100]}...")
                                send_telegram_alert(status_message)
                            else:
                                print(f"[Telegram Listener] Not a status command or unauthorized chat: '{message_text}' != '/status' or '{message_chat_id}' != '{chat_id}'")
                else:
                    print(f"[Telegram Listener] No updates in response")
            else:
                print(f"[Telegram Listener] Error: {response.status_code} - {response.text}")
            
            # Sleep to avoid hammering the API
            time.sleep(5)
            
        except Exception as e:
            print(f"[Telegram Listener] Error in Telegram listener: {e}")
            traceback.print_exc()
            # Sleep and continue on error
            time.sleep(10)

def main():
    """
    Main function to fetch live matches and print match details with team names and competition country using parallelization
    """
    try:
        # Load countries first so we have them available for competition lookup
        country_data = fetch_country_data()
        country_map = create_country_id_to_name_map(country_data)
        
        # Always run in continuous mode by default
        continuous_mode = True
        interval = 30  # Default interval in seconds
        
        # Check for command line arguments
        parser = argparse.ArgumentParser(description='Live Football Match Monitor')
        parser.add_argument('-s', '--single', action='store_true', help='Run once and exit (default: run continuously)')
        parser.add_argument('-i', '--interval', type=int, help='Update interval in seconds (default: 30)')
        args = parser.parse_args()
        
        if args.single:
            continuous_mode = False
        if args.interval:
            interval = args.interval
        
        # Run the fetch process in a loop if continuous mode is enabled
        while True:
            process_live_matches(country_map)
            
            if not continuous_mode:
                break
                
            # Convert current time to Eastern Time (ET)
            eastern = pytz.timezone('America/New_York')
            et_time = datetime.datetime.now(eastern)
            et_time_str = et_time.strftime(CONSOLE_TIME_FORMAT)
            
            print(f"\nWaiting {interval} seconds before next update at {et_time_str}...")
            print(f"{'=' * 50}")
            time.sleep(interval)
            print(f"\n{'=' * 50}")
            print(f"REFRESHING DATA AT: {et_time.strftime(CONSOLE_TIME_FORMAT)}")
            print(f"{'=' * 50}\n")
    
    except KeyboardInterrupt:
        print("\nLive match monitoring stopped by user.")
    except Exception as e:
        print(f"Error in main function: {e}")
        traceback.print_exc()

def process_live_matches(country_map):
    """
    Process live matches and display their details
    """
    # Fetch live matches
    live_matches_data = fetch_live_matches()
    if not live_matches_data or "results" not in live_matches_data:
        print("No live matches found.")
        # Add telegram alert for no matches found
        message = "⚠️ <b>ALERT: NO LIVE MATCHES FOUND</b>\n\nThe API returned no live matches, which is unusual and may indicate a problem with the API or the system. Please check the connection and API status."
        send_telegram_alert(message)
        return
    
    # Extract match IDs
    match_ids = extract_match_ids(live_matches_data)
    
    # Print a header with total matches found
    print(f"\n===== FOUND {len(match_ids)} LIVE FOOTBALL MATCHES =====\n")
    eastern_now = get_eastern_time()
    print(f"Last updated: {eastern_now.strftime(DATE_FORMAT)} {eastern_now.strftime(CONSOLE_TIME_FORMAT)}")
    
    # Process each match ID
    for i, match_id in enumerate(match_ids, 1):
        try:
            # Get match data from the live endpoint
            live_match_data = None
            for match in live_matches_data["results"]:
                if match["id"] == match_id:
                    live_match_data = match
                    break
            
            if not live_match_data:
                continue
            
            # Fetch additional match details from the recent/list endpoint
            match_details_data = fetch_match_details(match_id)
            
            # Get match details from the response
            match_details = None
            if match_details_data and "results" in match_details_data and match_details_data["results"]:
                # Match details from recent/list endpoint may be in various formats
                if isinstance(match_details_data["results"], list):
                    match_details = match_details_data["results"][0]
                else:
                    match_details = match_details_data["results"]
            
            # Combine data from both endpoints
            match_data = live_match_data.copy()  # Start with live data
            
            # Add or override with details data if available
            if match_details:
                match_data.update({k: v for k, v in match_details.items() if k not in match_data or not match_data[k]})
            
            # Fetch team and competition info
            home_team_id = match_data.get("home_team_id", "")
            away_team_id = match_data.get("away_team_id", "")
            competition_id = match_data.get("competition_id", "")
            
            home_team_info = fetch_team_info(home_team_id) if home_team_id else None
            away_team_info = fetch_team_info(away_team_id) if away_team_id else None
            competition_info = fetch_competition_info(competition_id) if competition_id else None
            
            home_team_name = extract_team_name(home_team_info) if home_team_info else "Unknown Home Team"
            away_team_name = extract_team_name(away_team_info) if away_team_info else "Unknown Away Team"
            
            competition_name = extract_competition_info(competition_info)[0] if competition_info else "Unknown Competition"
            competition_country_id = extract_competition_info(competition_info)[1] if competition_info else None
            competition_country = country_map.get(competition_country_id, "Unknown Country")
            
            # Fetch odds data
            odds_data = fetch_match_odds(match_id)
            
            # Format the match odds
            formatted_odds = format_match_odds(odds_data)
            
            # Get environment data
            environment = match_data.get("environment", {})
            weather = environment.get("weather", "")
            temperature = environment.get("temperature", "")
            wind = environment.get("wind", "")
            humidity = environment.get("humidity", "")
            
            # Convert temperature from Celsius to Fahrenheit if available
            temperature_fahrenheit = ""
            if temperature:
                try:
                    temp_c = float(temperature)
                    temp_f = (temp_c * 9/5) + 32
                    temperature_fahrenheit = f"{temp_f:.1f}°F"
                except (ValueError, TypeError):
                    temperature_fahrenheit = ""
            
            # Process weather code to text description
            weather_text = get_weather_description(weather) if weather else ""
            
            # Convert wind speed from m/s to mph if available
            wind_mph = ""
            if wind:
                try:
                    # Extract numeric part from the wind string (remove "m/s" if present)
                    wind_value = wind.replace("m/s", "").strip()
                    wind_ms = float(wind_value)
                    wind_mph = f"{wind} ({wind_ms * 2.237:.1f} mph)"
                except (ValueError, TypeError):
                    wind_mph = wind
            
            # Format humidity with single %
            humidity_text = ""
            if humidity:
                # Remove any existing % sign and add a single one
                humidity_clean = str(humidity).replace("%", "").strip()
                humidity_text = f"{humidity_clean}%"
            
            # Print match header with number
            print(f"{'=' * 50}")
            print(f"MATCH #{i} OF {len(match_ids)}")
            print(f"{'=' * 50}")
            
            # Print match summary
            print("\n----- MATCH SUMMARY -----")
            print(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
            print(f"Match ID: {match_id}")
            print(f"Competition ID: {competition_id}")
            print(f"Competition: {competition_name} ({competition_country})")
            print(f"Match: {home_team_name} vs {away_team_name}")
            
            # Extract scores from detail_live API format
            home_live_score = 0
            home_ht_score = 0
            away_live_score = 0
            away_ht_score = 0
            
            if "score" in match_data:
                score_data = match_data.get("score", [])
                if isinstance(score_data, list) and len(score_data) > 3:
                    # Home scores (index 2)
                    home_scores = score_data[2]
                    if isinstance(home_scores, list) and len(home_scores) > 1:
                        # Home live score (index 0)
                        if isinstance(home_scores[0], str) and " " in home_scores[0]:
                            home_live_score = home_scores[0].split(" ")[0]
                        else:
                            home_live_score = home_scores[0]
                        # Home half-time score (index 1)
                        if isinstance(home_scores[1], str) and " " in home_scores[1]:
                            home_ht_score = home_scores[1].split(" ")[0]
                        else:
                            home_ht_score = home_scores[1]
                    
                    # Away scores (index 3)
                    away_scores = score_data[3]
                    if isinstance(away_scores, list) and len(away_scores) > 1:
                        # Away live score (index 0)
                        if isinstance(away_scores[0], str) and " " in away_scores[0]:
                            away_live_score = away_scores[0].split(" ")[0]
                        else:
                            away_live_score = away_scores[0]
                        # Away half-time score (index 1)
                        if isinstance(away_scores[1], str) and " " in away_scores[1]:
                            away_ht_score = away_scores[1].split(" ")[0]
                        else:
                            away_ht_score = away_scores[1]
            
            # Print the updated score format
            print(f"Score: {home_live_score} - {away_live_score} (HT: {home_ht_score} - {away_ht_score})")
            
            # Print match status with status_id
            status_name = get_status_description(match_data.get('status_id', 'Unknown'))
            status_id = match_data.get('status_id', 'Unknown')
            print(f"Status: {status_name} (Status ID: {status_id})")
            
            # Print odds information first
            if formatted_odds:
                print("\n--- MATCH BETTING ODDS ---")
                print(format_odds_display(formatted_odds))
            
            # Print environment info after the odds
            if weather_text or temperature_fahrenheit or wind_mph or humidity_text:
                print("\n--- MATCH ENVIRONMENT ---")
                if weather_text:
                    print(f"Weather: {weather_text}")
                if temperature_fahrenheit:
                    print(f"Temperature: {temperature_fahrenheit}")
                if humidity_text:
                    print(f"Humidity: {humidity_text}")
                if wind_mph:
                    print(f"Wind: {wind_mph}")
            else:
                print("\n--- MATCH ENVIRONMENT ---")
                print("No environment data available for this match")
            
            # Log match data to file in JSON format for easier parsing by other tools
            match_data = {
                "timestamp": get_eastern_time().strftime(API_DATETIME_FORMAT),
                "competition_id": competition_id,
                "competition": competition_name,
                "country": competition_country,
                "home_team": home_team_name,
                "away_team": away_team_name,
                "score": f"{home_live_score} - {away_live_score}",
                "status": status_name,
                "status_id": status_id,
                "odds": formatted_odds,
                "weather": weather_text,
                "humidity": humidity_text,
                "wind": wind_mph
            }
            
            print("\n")
        except Exception as e:
            print(f"Error processing match {match_id}: {str(e)}")
            traceback.print_exc()
            continue
    
    # Print a footer
    print(f"{'=' * 50}")
    print(f"END OF LIVE MATCH DATA - {len(match_ids)} MATCHES DISPLAYED")
    print(f"{'=' * 50}")
    print(f"Refreshing in 30 seconds... (Press Ctrl+C to exit)")

if __name__ == "__main__":
    # Create a lock file to ensure only one instance runs at a time
    lock_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live.lock")
    lock_file = open(lock_file_path, "w")
    
    try:
        # Attempt to acquire an exclusive lock (will fail if another instance has the lock)
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(f"Acquired process lock. This is the only running instance.")
        
        # Logger is already initialized on import
        print("Main logger is active...")
        
        # Register signal handler for SIGUSR1
        signal.signal(signal.SIGUSR1, handle_sigusr1)
        
        # Send startup notification to Telegram
        startup_message = f"🚀 <b>LIVE.PY STARTED</b>\n\nThe live data collection system has been started successfully."
        send_telegram_alert(startup_message)
        
        # Register a cleanup handler to notify on shutdown
        import atexit
        def exit_handler():
            exit_message = f"⛔ <b>LIVE.PY STOPPED</b>\n\nThe live data collection system has been stopped."
            try:
                send_telegram_alert(exit_message)
                # Release lock and close file
                fcntl.flock(lock_file, fcntl.LOCK_UN)
                lock_file.close()
                # Remove lock file on clean exit
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)
            except:
                pass  # Ensure no exceptions break the exit process
        atexit.register(exit_handler)
        
        # Start Telegram listener thread
        telegram_thread = threading.Thread(target=telegram_listener)
        telegram_thread.daemon = True  # Allow main thread to exit even if this thread is still running
        telegram_thread.start()
        
        main()
        
    except IOError:
        print(f"Failed to acquire process lock. Another instance is already running.")
        print(f"If you're sure no other instance is running, delete the lock file: {lock_file_path}")
        sys.exit(1)