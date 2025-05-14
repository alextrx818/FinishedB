#!/usr/bin/env python3
"""
Simplified test that demonstrates the pretty formatting without dependencies
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from zoneinfo import ZoneInfo

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('pretty_test')

# Import OU3 directly
from OU3 import OverUnderAlert

# Sample test match with all the necessary data for pretty formatting
test_match = {
    "match_id": "ednm9whwke2zryo",
    "status_id": 2,  # First half
    "status": "First half",
    "home_team": {"name": "Al-Gharafa"},
    "away_team": {"name": "Al-Sadd"},
    "competition": {
        "id": "kjw2r09hlx4rz84",
        "name": "Qatar Prince Cup",
        "country": "Qatar"
    },
    "score": {
        "home": 0,
        "away": 0,
        "home_ht": 0,
        "away_ht": 0
    },
    "odds": {
        "markets": [
            {
                "type": "MONEYLINE",
                "home": 4.0,    # +300 in American odds
                "draw": 4.0,    # +300 in American odds
                "away": 1.66,   # -152 in American odds
                "minute": 4
            },
            {
                "type": "SPREAD",
                "home": 1.92,  # -109 in American odds
                "line": -0.75,
                "away": 1.87,  # -115 in American odds
                "minute": 4
            },
            {
                "type": "OVER_UNDER",
                "over": 1.92,  # -109 in American odds
                "line": 3.25,
                "under": 1.87, # -115 in American odds
                "minute": 4
            }
        ]
    },
    "environment": {
        "weather": 5,           # 5 = Foggy
        "temperature": "100.4°F",
        "humidity": "27%",
        "wind": "8.9mph",
        "pressure": "762mmHg"
    }
}

# Simplified implementation of needed functions from combined_match_summary.py
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p %Z"

def get_eastern_time():
    return datetime.now(ZoneInfo("America/New_York"))

def get_status_description(status_id):
    status_mapping = {
        "1": "Not started", "2": "First half", "3": "Half-time break",
        "4": "Second half", "5": "Extra time", "6": "Penalty shootout",
        "7": "Finished", "8": "Finished", "9": "Postponed",
        "10": "Canceled", "11": "To be announced", "12": "Interrupted",
        "13": "Abandoned", "14": "Suspended"
    }
    return status_mapping.get(str(status_id), f"Unknown (ID: {status_id})")

def hk_to_american(hk_odds):
    """Convert Hong Kong odds to American odds (int value)"""
    try:
        hk_odds = float(hk_odds)
        if hk_odds >= 1:
            return int(round(hk_odds * 100))
        else:
            return int(round(-100 / hk_odds))
    except (ValueError, ZeroDivisionError):
        return 0

def decimal_to_american(decimal_odds):
    """Convert decimal odds to American odds (int value)"""
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

def format_american_odds(raw_value, market):
    """Format American odds with consistent sign display."""
    try:
        # Ensure valid input
        if raw_value is None or raw_value == "" or raw_value == 0:
            return "+0"
            
        if market in ("SPREAD", "Over/Under"):
            amd = hk_to_american(raw_value)
        else:
            amd = decimal_to_american(raw_value)
            
        # Check for valid conversion result
        if amd == 0:
            return "+0"
            
        return f"{amd:+d}"
    except Exception as e:
        return "+0"

def transform_odds(markets, odds_type=None):
    """Simplified transform function that works directly with our test data"""
    if not markets:
        return []
    
    transformed = []
    for market in markets:
        entry = {}
        
        if odds_type == "eu" and market.get("type") == "MONEYLINE":
            entry = {
                "time_of_match": str(market.get("minute", 0)),
                "home_win": market.get("home"),
                "draw": market.get("draw"),
                "away_win": market.get("away")
            }
            transformed.append(entry)
        elif odds_type == "asia" and market.get("type") == "SPREAD":
            entry = {
                "time_of_match": str(market.get("minute", 0)),
                "home_win": market.get("home"),
                "handicap": market.get("line"),
                "away_win": market.get("away")
            }
            transformed.append(entry)
        elif odds_type == "bs" and market.get("type") == "OVER_UNDER":
            entry = {
                "time_of_match": str(market.get("minute", 0)),
                "over": market.get("over"),
                "size": market.get("line"),
                "under": market.get("under")
            }
            transformed.append(entry)
            
    return transformed

def format_odds_display(formatted_odds):
    """Simplified version of format_odds_display"""
    if not any(formatted_odds.values()):
        return "No betting odds available"
    
    lines = []
    
    # ML odds
    ml_entries = formatted_odds.get("ML", [])
    if ml_entries:
        entry = ml_entries[0]  # Just use the first entry
        time = entry.get("time_of_match", "0")
        home = format_american_odds(entry.get("home_win"), "ML")
        draw = format_american_odds(entry.get("draw"), "ML")
        away = format_american_odds(entry.get("away_win"), "ML")
        lines.append(f"│ ML:     │ Home: {home} │ Draw: {draw} │ Away: {away} │ (@{time}')")
    
    # Spread odds
    spread_entries = formatted_odds.get("SPREAD", [])
    if spread_entries:
        entry = spread_entries[0]  # Just use the first entry
        time = entry.get("time_of_match", "0")
        home = format_american_odds(entry.get("home_win"), "SPREAD")
        hcap = entry.get("handicap", 0)
        away = format_american_odds(entry.get("away_win"), "SPREAD")
        lines.append(f"│ Spread: │ Home: {home} │ Hcap: {hcap} │ Away: {away} │ (@{time}')")
    
    # Over/Under odds
    ou_entries = formatted_odds.get("Over/Under", [])
    if ou_entries:
        entry = ou_entries[0]  # Just use the first entry
        time = entry.get("time_of_match", "0")
        over = format_american_odds(entry.get("over"), "Over/Under")
        line = entry.get("size", 0)
        under = format_american_odds(entry.get("under"), "Over/Under")
        lines.append(f"│ O/U:    │ Over: {over} │ Line: {line} │ Under: {under} │ (@{time}')")
    
    return "\n".join(lines)

def summarize_environment(env):
    """Simplified environment formatter"""
    if not env:
        return ["No environment data available"]
    
    weather_codes = {
        1: "Sunny",
        2: "Partly Cloudy",
        3: "Cloudy",
        4: "Overcast",
        5: "Foggy",
        6: "Light Rain",
        7: "Rain",
        8: "Heavy Rain",
        9: "Snow",
        10: "Thunder"
    }
    
    lines = []
    
    # Weather condition
    weather_code = env.get("weather")
    if weather_code is not None:
        weather_text = weather_codes.get(weather_code, f"Unknown ({weather_code})")
        lines.append(f"Weather: {weather_text}")
    
    # Temperature
    temp = env.get("temperature")
    if temp:
        lines.append(f"Temperature: {temp}")
    
    # Humidity
    humidity = env.get("humidity")
    if humidity:
        lines.append(f"Humidity: {humidity}")
    
    # Wind
    wind = env.get("wind")
    if wind:
        # Extract numeric part and unit
        wind_match = re.match(r'(\d+\.?\d*)(\w+)', wind)
        if wind_match:
            speed = float(wind_match.group(1))
            unit = wind_match.group(2)
            
            # Determine Beaufort wind force description
            if unit.lower() == "mph":
                if speed < 1:
                    desc = "Calm"
                elif speed < 4:
                    desc = "Light Air"
                elif speed < 8:
                    desc = "Light Breeze"
                elif speed < 13:
                    desc = "Gentle Breeze"
                elif speed < 19:
                    desc = "Moderate Breeze"
                else:
                    desc = "Fresh Breeze"
                lines.append(f"Wind: {desc}, {speed} {unit}")
            else:
                lines.append(f"Wind: {wind}")
        else:
            lines.append(f"Wind: {wind}")
    
    return lines

def print_match_summary(match):
    """Print a nicely formatted match summary like in combined_match_summary.py"""
    print("\n----- MATCH SUMMARY -----")
    print(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
    print(f"Match ID: {match.get('match_id')}")
    competition = match.get('competition', {})
    print(f"Competition ID: {competition.get('id', 'Unknown')}")
    print(f"Competition: {competition.get('name', 'Unknown')} ({competition.get('country', 'Unknown Country')})")
    
    # Team names
    home_team = match.get('home_team', {}).get('name', match.get('home', 'Unknown'))
    away_team = match.get('away_team', {}).get('name', match.get('away', 'Unknown'))
    print(f"Match: {home_team} vs {away_team}")
    
    # Score
    score = match.get('score', {})
    home_score = score.get('home', 0)
    away_score = score.get('away', 0)
    home_ht = score.get('home_ht', 0)
    away_ht = score.get('away_ht', 0)
    print(f"Score: {home_score} - {away_score} (HT: {home_ht} - {away_ht})")
    
    # Status
    status_id = match.get('status_id')
    status = match.get('status', get_status_description(status_id))
    print(f"Status: {status} (Status ID: {status_id})")
    
    # Betting Odds
    print("\n--- MATCH BETTING ODDS ---")
    odds_data = match.get('odds', {})
    markets = odds_data.get('markets', [])
    
    # Extract and format odds data
    ml_odds = []
    spread_odds = []
    ou_odds = []
    
    for market in markets:
        market_type = market.get('type')
        if market_type == 'MONEYLINE':
            ml_odds.append(market)
        elif market_type == 'SPREAD':
            spread_odds.append(market)
        elif market_type == 'OVER_UNDER':
            ou_odds.append(market)
    
    formatted_odds = {
        "ML": transform_odds(ml_odds, "eu"),
        "SPREAD": transform_odds(spread_odds, "asia"),
        "Over/Under": transform_odds(ou_odds, "bs")
    }
    
    odds_display = format_odds_display(formatted_odds)
    print(odds_display)
    
    # Environment
    print("\n--- MATCH ENVIRONMENT ---")
    env_data = match.get('environment', {})
    for line in summarize_environment(env_data):
        print(line)

def run_simulator():
    # Check if the alert would trigger
    alert = OverUnderAlert(threshold=3.0)
    notice = alert.check(test_match)
    
    if notice:
        print("\n" + "=" * 80)
        print("ALERT TRIGGERED: OU3")
        print("=" * 80)
        
        # Mock telegram message
        print(f"\nTELEGRAM MESSAGE SENT:\n{notice}")
        
        # Print the pretty formatted match summary
        print_match_summary(test_match)
    else:
        print("Alert did not trigger")

if __name__ == "__main__":
    run_simulator()
