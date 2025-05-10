#!/usr/bin/env python3
"""
High Over/Under Alert

This module monitors match data for over/under lines of 3.0 or higher
and sends alerts when such matches are found.
"""

import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional, Set, List, Tuple

# Add project root to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

# Try to import the Telegram alert functionality
try:
    from football.telegram import send_match_alert
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: Telegram module not available, alerts will be printed only")

# Import utilities from the consolidated alert_system module
try:
    from football.live_alerts.alert_system import should_deduplicate_alert, generate_alert_message, get_weather_description, MINIMUM_OVERUNDER_THRESHOLD as HIGH_OVERUNDER_THRESHOLD
except ImportError:
    print("Warning: parse_alert_logic module not available, defaulting to internal logic")

# Cache to prevent duplicate alerts
alerted_match_lines = set()

# Constants
ALERT_TYPE = "odds"
MINIMUM_OVERUNDER_THRESHOLD = 3.0
# Only matches in-play or not started should be analyzed
VALID_STATUS_IDS = ["1", "2", "4"]  # 1=Not started, 2=In-play, 4=Second half

def extract_overunder_data(match_data: Dict[str, Any]) -> List[Tuple[float, str]]:
    """
    Extract over/under line values from match data.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        List of tuples containing (line_value, time_of_match)
    """
    result = []
    
    # Check if odds data exists
    odds_data = match_data.get("odds", {})
    if not odds_data:
        return result
    
    # Look for Over/Under odds
    ou_odds = odds_data.get("Over/Under", [])
    if not ou_odds:
        return result
    
    # Extract line values from each time point
    for time_point in ou_odds:
        # Get the time of match (minute)
        time_of_match = time_point.get("time_of_match", "0")
        
        # Look for the line value (total)
        line_value = time_point.get("line")
        if line_value is not None:
            try:
                # Convert line value to float
                line_float = float(line_value)
                result.append((line_float, time_of_match))
            except (ValueError, TypeError):
                # Skip invalid line values
                continue
    
    return result

def check_high_overunder_condition(match_data: Dict[str, Any]) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Check if a match has over/under odds of 3.0 or higher.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        Tuple of (has_high_overunder, line_value, time_of_match)
    """
    # Check if match is in a valid status
    status_id = str(match_data.get("status_id", ""))
    if status_id not in VALID_STATUS_IDS:
        return False, None, None
    
    # Extract over/under data
    ou_values = extract_overunder_data(match_data)
    if not ou_values:
        return False, None, None
    
    # Find highest line value
    highest_line = None
    time_of_highest = None
    
    for line_value, time_of_match in ou_values:
        if highest_line is None or line_value > highest_line:
            highest_line = line_value
            time_of_highest = time_of_match
    
    # Check if highest line meets threshold
    if highest_line is not None and highest_line >= MINIMUM_OVERUNDER_THRESHOLD:
        return True, highest_line, time_of_highest
    
    return False, None, None

def get_match_line_key(match_id: str, line_value: float) -> str:
    """
    Create a unique key for tracking already alerted lines.
    
    Args:
        match_id: Match identifier
        line_value: Over/under line value
        
    Returns:
        String key for deduplication
    """
    # Round to 1 decimal place to avoid minor fluctuations triggering multiple alerts
    rounded_line = round(line_value, 1)
    return f"{match_id}_{rounded_line}"

def get_weather_description(code: str) -> str:
    """
    Convert weather code to human-readable description.
    
    Args:
        code: Weather code from the API
        
    Returns:
        Human-readable weather description
    """
    weather_codes = {
        "1": "Partly cloudy",
        "2": "Cloudy",
        "3": "Overcast",
        "4": "Fog",
        "5": "Drizzle",
        "6": "Rain",
        "7": "Snow",
        "8": "Shower",
        "9": "Thunderstorm",
        "10": "Light rain",
        "11": "Heavy rain",
        "12": "Light snow",
        "13": "Heavy snow",
        "14": "Sleet",
        "15": "Clear",
        "16": "Sunny"
    }
    
    return weather_codes.get(code, f"Unknown ({code})")

def format_high_overunder_message(match_data: Dict[str, Any], line_value: float, time_of_match: str) -> str:
    """
    Format an alert message for high over/under with comprehensive match details.
    
    Args:
        match_data: Match data dictionary
        line_value: The over/under line value
        time_of_match: When the odds were recorded (match minute)
        
    Returns:
        Formatted alert message with all match details
    """
    # Basic match information
    match_id = match_data.get("id", "Unknown")
    home_team = match_data.get("home_team", "Home Team")
    away_team = match_data.get("away_team", "Away Team")
    competition = match_data.get("competition", "Unknown Competition")
    status_id = str(match_data.get("status_id", "Unknown"))
    current_minute = match_data.get("minute", "Unknown")
    
    # Get status text
    status_map = {
        "0": "Not Started", 
        "1": "Not Started",
        "2": "First Half",
        "3": "Half-Time",
        "4": "Second Half", 
        "5": "Full Time",
        "6": "Extra Time",
        "7": "Penalties",
        "8": "Finished",
        "9": "Postponed",
        "10": "Cancelled",
        "11": "To Be Announced",
        "12": "Interrupted",
        "13": "Abandoned"
    }
    status_text = status_map.get(status_id, "Unknown Status")
    
    # Get score information
    home_score = match_data.get("home_score", "0")
    away_score = match_data.get("away_score", "0")
    score_display = f"{home_score} - {away_score}"
    
    # Get venue information
    venue = match_data.get("venue", "Unknown Venue")
    
    # Get environment data if available
    environment = match_data.get("environment", {})
    weather_code = environment.get("weather", {}).get("code", "")
    weather_desc = get_weather_description(weather_code) if weather_code else "N/A"
    temp_c = environment.get("temperature", {}).get("temp", "N/A")
    temp_f = "N/A"
    if temp_c != "N/A" and isinstance(temp_c, (int, float, str)):
        try:
            temp_f = round((float(temp_c) * 9/5) + 32, 1)
        except (ValueError, TypeError):
            temp_f = "N/A"
    
    humidity = environment.get("humidity", "N/A")
    wind_speed = environment.get("wind", {}).get("speed", "N/A")
    
    # Get odds information
    odds_data = match_data.get("odds", {})
    ml_odds = odds_data.get("ML", [{}])[0] if "ML" in odds_data and odds_data["ML"] else {}
    spread_odds = odds_data.get("SPREAD", [{}])[0] if "SPREAD" in odds_data and odds_data["SPREAD"] else {}
    
    # Format home/away money line if available
    home_ml = ml_odds.get("home_win", "N/A")
    away_ml = ml_odds.get("away_win", "N/A")
    draw_ml = ml_odds.get("draw", "N/A")
    
    # Format spread if available
    handicap = spread_odds.get("handicap", "N/A")
    home_spread = spread_odds.get("home", "N/A")
    away_spread = spread_odds.get("away", "N/A")
    
    # Start building the message
    message = f"📊 HIGH OVER/UNDER ALERT\n\n"
    message += f"⚽ MATCH SUMMARY ⚽\n"
    message += f"───────────────────\n"
    message += f"{home_team} vs {away_team}\n"
    
    # Score and status section
    message += f"Score: {score_display}\n"
    message += f"Status: {status_text}"
    if current_minute and current_minute != "Unknown":
        message += f" (minute {current_minute})"
    message += "\n"
    message += f"Competition: {competition}\n"
    message += f"Venue: {venue}\n\n"
    
    # Environment section
    message += f"🌤 ENVIRONMENT\n"
    message += f"───────────────────\n"
    if weather_desc != "N/A":
        message += f"Weather: {weather_desc}\n"
    if temp_c != "N/A":
        message += f"Temperature: {temp_c}°C / {temp_f}°F\n"
    if humidity != "N/A":
        message += f"Humidity: {humidity}%\n"
    if wind_speed != "N/A":
        message += f"Wind Speed: {wind_speed} mph\n\n"
    
    # Odds section
    message += f"📈 ODDS INFORMATION\n"
    message += f"───────────────────\n"
    message += f"ALERT! Over/Under: {line_value}\n"
    message += f"Recorded at match minute: {time_of_match}\n\n"
    
    # Money line
    if home_ml != "N/A" or away_ml != "N/A":
        message += f"Money Line:\n"
        message += f"  {home_team}: {home_ml}\n"
        message += f"  {away_team}: {away_ml}\n"
        if draw_ml != "N/A":
            message += f"  Draw: {draw_ml}\n"
        message += "\n"
    
    # Spread
    if handicap != "N/A":
        message += f"Spread (Handicap: {handicap}):\n"
        message += f"  {home_team}: {home_spread}\n"
        message += f"  {away_team}: {away_spread}\n\n"
    
    # Meta information
    message += f"Match ID: {match_id}\n"
    message += f"Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return message

def process_match_data(match_data: Dict[str, Any]) -> bool:
    """
    Process match data and trigger an alert if high over/under is found.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        True if an alert was triggered, False otherwise
    """
    # Check if match data has the necessary fields
    required_fields = ["id", "status_id", "home_team", "away_team", "odds"]
    if not all(field in match_data for field in required_fields):
        return False
    
    # Check if the match has high over/under odds
    has_high_ou, line_value, time_of_match = check_high_overunder_condition(match_data)
    if not has_high_ou or line_value is None:
        return False
    
    # Get match ID and create a unique line key
    match_id = match_data.get("id", "unknown")
    line_key = get_match_line_key(match_id, line_value)
    
    # Check for duplicate alerts
    if line_key in alerted_match_lines:
        return False
    
    # Create alert data dictionary with comprehensive match info
    alert_data = {
        # Core match info
        "match_id": match_id,
        "home_team": match_data.get("home_team", "Home Team"),
        "away_team": match_data.get("away_team", "Away Team"),
        "competition": match_data.get("competition", "Unknown Competition"),
        "competition_id": match_data.get("competition_id", "Unknown"),
        "venue": match_data.get("venue", "Unknown Venue"),
        
        # Score and status
        "home_score": match_data.get("home_score", "0"),
        "away_score": match_data.get("away_score", "0"),
        "ht_home_score": match_data.get("ht_home_score", "0"),
        "ht_away_score": match_data.get("ht_away_score", "0"),
        "status_id": match_data.get("status_id", "Unknown"),
        "minute": match_data.get("minute", "Unknown"),
        
        # Environment data
        "environment": match_data.get("environment", {}),
        
        # Odds data (include all available odds)
        "odds": match_data.get("odds", {}),
        
        # Timestamp
        "timestamp": datetime.now().strftime("%m/%d/%Y %I:%M:%S %p ET"),
        
        # Alert-specific information
        "alert_reasons": [
            f"High over/under line detected: {line_value}",
            f"Recorded at match minute: {time_of_match}"
        ]
    }
    
    # Generate alert message using the common formatter
    message = generate_alert_message(alert_data, "odds")
    
    # Send the alert
    if TELEGRAM_AVAILABLE:
        send_match_alert(
            message=message,
            match_id=match_id,
            teams=f"{match_data.get('home_team')} vs {match_data.get('away_team')}",
            competition=match_data.get("competition"),
            alert_type=ALERT_TYPE
        )
    else:
        # Print to console if Telegram is not available
        print("\n" + "=" * 60)
        print("HIGH OVER/UNDER ALERT (Telegram not available)")
        print("=" * 60)
        print(message)
        print("=" * 60 + "\n")
    
    # Add to alerted set to prevent duplicates
    alerted_match_lines.add(line_key)
    
    return True

def reset_alert_cache():
    """Reset the alert cache to clear any stored match IDs"""
    alerted_match_lines.clear()

def test_with_sample_data():
    """Test the alert with sample data"""
    # Create a test match with high over/under and comprehensive odds data
    test_match = {
        "id": "8yomo4h3wkj8q0j",
        "home_team": "D. Concepcion",
        "away_team": "Santiago Morning",
        "competition": "Chilean Primera B (Chile)",
        "competition_id": "l965mkyhdgr1ge4",
        "status_id": "2",  # In-play (First Half)
        "minute": "15",
        "home_score": "1",
        "away_score": "0",
        "ht_home_score": "0",
        "ht_away_score": "0",
        "venue": "Estadio Municipal de Concepcion",
        "environment": {
            "weather": {
                "code": "16"  # Sunny
            },
            "temperature": {
                "temp": 22.5  # Celsius
            },
            "humidity": 39,
            "wind": {
                "speed": 1.2,  # m/s
                "direction": "NE"
            }
        },
        "odds": {
            # Money Line odds
            "ML": [
                {
                    "time_of_match": "4",
                    "home_win": "+137",
                    "draw": "+200",
                    "away_win": "+187"
                },
                {
                    "time_of_match": "0",
                    "home_win": "+145",
                    "draw": "+210",
                    "away_win": "+175"
                }
            ],
            # Spread/handicap odds
            "SPREAD": [
                {
                    "time_of_match": "4",
                    "home": "-101",
                    "handicap": "0.25",
                    "away": "-130"
                },
                {
                    "time_of_match": "0",
                    "home": "-105",
                    "handicap": "0.0",
                    "away": "-120"
                }
            ],
            # Over/Under odds with high line value to trigger alert
            "Over/Under": [
                {
                    "time_of_match": "4",
                    "over": "+105",
                    "line": "3.5",
                    "under": "-133"
                },
                {
                    "time_of_match": "0",
                    "over": "+100",
                    "line": "3.0",
                    "under": "-125"
                }
            ]
        },
        "timestamp": "05/09/2025 08:58:22 PM ET"
    }
    
    # Process the test match with complete odds data
    print("Testing with comprehensive match data...")
    alert_triggered = process_match_data(test_match)
    print(f"Alert triggered: {alert_triggered}")
    
    # Test that same match doesn't trigger again
    print("Testing duplicate prevention...")
    alert_triggered = process_match_data(test_match)
    print(f"Second alert triggered: {alert_triggered}")
    
    # Test with below threshold
    test_match["odds"]["Over/Under"] = [
        {
            "time_of_match": "4",
            "over": "+105",
            "line": "2.25",
            "under": "-133"
        }
    ]
    reset_alert_cache()  # Reset cache for testing
    
    print("Testing with below threshold value...")
    alert_triggered = process_match_data(test_match)
    print(f"Below threshold alert triggered: {alert_triggered}")

# Example usage if run directly
if __name__ == "__main__":
    test_with_sample_data()
