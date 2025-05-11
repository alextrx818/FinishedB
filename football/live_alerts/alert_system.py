#!/usr/bin/env python3
"""
!!!!! IMPORTANT SYSTEM ARCHITECTURE NOTE !!!!!

This is the SPORTS ALERT SYSTEM which is COMPLETELY SEPARATE from the SYSTEM ALERT system.

1. DO NOT MODIFY System Alert Components:
   - /football/telegram/alerts.py  - Low-level Telegram API communication
   - /football/alerts.py - System monitoring and verification

2. ONLY ADD/MODIFY sports alerts in the live_alerts directory:
   - /football/live_alerts/alert_system.py
   - /football/live_alerts/*_alert.py modules

3. MAINTAIN STRICT SEPARATION between systems:
   - Sports alerts: For match conditions only
   - System alerts: For technical monitoring only
   - DO NOT try to mix these systems or have them call each other directly

!!!!! END OF IMPORTANT NOTE !!!!!

Alert System

This consolidated module contains the core alert system functionality:
1. Alert criteria and thresholds
2. JSON parsing and alert message generation
3. Utility functions for working with match data

All individual alert modules should import from this file.
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set, Union

# Add project root to path to allow imports from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

#==========================================
# ALERT CRITERIA AND THRESHOLDS
#==========================================

# Minimum odds entries required to consider data complete
MINIMUM_ODDS_COUNT = 3

# Thresholds for unusual odds values
UNUSUAL_HANDICAP_THRESHOLD = 3.0  # Alert if absolute handicap > 3
HIGH_OVERUNDER_THRESHOLD = 3.0    # Alert if over/under line > 3.0

# Temperature thresholds (Celsius)
TEMPERATURE_ALERT_THRESHOLD_C = 35  # Alert if temperature above 35°C
LOW_TEMPERATURE_THRESHOLD_C = 0    # Alert if temperature below 0°C

# Wind speed threshold (mph)
WIND_ALERT_THRESHOLD_MPH = 25       # Alert if wind above 25 mph

# Expected odds types that should be present
EXPECTED_ODDS_TYPES = ["SPREAD", "ML", "Over/Under"]

# Target minutes for odds collection
ML_TARGET_MINUTES = [4, 5, 6]      # Minutes 4-6 for Money Line
SPREAD_TARGET_MINUTES = [0, 1, 2, 3]  # Early minutes for spread
OVERUNDER_TARGET_MINUTES = [0, 1, 2, 3]  # Early minutes for over/under

# Alert priority definitions (higher number = higher priority)
ALERT_PRIORITIES = {
    "missing_odds": 70,            # Missing odds data
    "unusual_odds": 60,            # Unusual odds values
    "missing_environment": 40,     # Missing environment data
    "extreme_environment": 80,     # Extreme environment conditions
    "score_change": 90,            # Score change event
    "unusual_score": 85,           # Unusual score pattern
    "data_inconsistency": 75       # Data inconsistency detected
}

# PRIORITY ALERT CONFIGURATION
# These alert modules are loaded first and always run for every match
# You can add new alert modules to this list without changing any code
# Format: Either full filenames (e.g., "my_alert.py") or patterns (e.g., "odds_*.py")
PRIORITY_ALERT_PATTERNS = [
    "3o_u_alert.py",           # 3 Over/Under alert
    # Add any other priority alerts below
    # "second_alert.py",       # Another priority alert
    # "important_*.py",        # All alerts matching this pattern
]

# Extract just the module names (without .py) for processing
PRIORITY_ALERT_MODULES = [p[:-3] if p.endswith('.py') else p for p in PRIORITY_ALERT_PATTERNS]

# Time before allowing duplicate alerts for the same condition (seconds)
ALERT_DEDUPLICATION_TIMEOUT = 15 * 60  # 15 minutes

# Match status ID mapping
STATUS_MAP = {
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

#==========================================
# DATA STRUCTURE VERIFICATION
#==========================================

def verify_match_structure(match_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Verify if match data contains all expected fields and structure.
    Returns a dictionary with verification results for each major component.
    
    Args:
        match_data: The match data dictionary from the API or database
        
    Returns:
        Dictionary with verification results for each component
    """
    result = {
        "has_core_data": False,
        "has_teams": False,
        "has_odds": False,
        "has_environment": False,
        "has_score": False
    }
    
    # Check for core data fields
    core_fields = ["id", "status_id"]
    result["has_core_data"] = all(field in match_data for field in core_fields)
    
    # Check for team information
    team_fields = ["home_team", "away_team", "competition"]
    result["has_teams"] = all(field in match_data for field in team_fields)
    
    # Check for odds data
    result["has_odds"] = "odds" in match_data and isinstance(match_data["odds"], dict)
    
    # Check for environment data
    result["has_environment"] = "environment" in match_data and isinstance(match_data["environment"], dict)
    
    # Check for score data
    score_fields = ["home_score", "away_score"]
    result["has_score"] = all(field in match_data for field in score_fields)
    
    return result

#==========================================
# ODDS DATA PARSING AND FORMATTING
#==========================================

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

def format_american_odds(value: Union[int, float, str]) -> str:
    """
    Format odds value to American format with sign.
    
    Args:
        value: Raw odds value
        
    Returns:
        Formatted odds string with sign
    """
    if isinstance(value, str):
        # Check if already formatted
        if value.startswith("+") or value.startswith("-"):
            return value
        try:
            value = float(value)
        except ValueError:
            return value

    if isinstance(value, (int, float)):
        # Ensure it's displayed with a sign
        return f"+{int(value)}" if value >= 0 else f"{int(value)}"
    
    return str(value)

def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal odds to American format.
    
    Args:
        decimal_odds: Odds in decimal format (e.g., 2.5)
        
    Returns:
        Odds in American format (e.g., +150, -200)
    """
    if decimal_odds == 0:
        return 0
    
    if decimal_odds >= 2.0:
        # Underdog: Decimal odds minus 1, times 100
        return int(round((decimal_odds - 1.0) * 100))
    else:
        # Favorite: -100 divided by (decimal odds minus 1)
        return int(round(-100 / (decimal_odds - 1.0)))

def hk_to_american(hk_odds: float) -> int:
    """
    Convert Hong Kong odds to American format.
    
    Args:
        hk_odds: Odds in Hong Kong format
        
    Returns:
        Odds in American format
    """
    if hk_odds == 0:
        return 0
    
    if hk_odds >= 1.0:
        # Underdog: HK odds times 100
        return int(round(hk_odds * 100))
    else:
        # Favorite: -100 divided by HK odds
        return int(round(-100 / hk_odds))

def parse_odds_data(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format odds data from match data.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        Dictionary with parsed odds data
    """
    result = {
        "has_ml": False,
        "has_spread": False,
        "has_ou": False,
        "ml_values": {},
        "spread_values": {},
        "ou_values": {}
    }
    
    # Check if match has odds data
    odds_data = match_data.get("odds", {})
    if not odds_data:
        return result
    
    # Check for money line odds
    ml_odds = odds_data.get("ML", [])
    if ml_odds and len(ml_odds) > 0:
        result["has_ml"] = True
        for time_point in ml_odds:
            minute = time_point.get("time_of_match", "0")
            result["ml_values"][minute] = {
                "home": format_american_odds(time_point.get("home_win", "")),
                "draw": format_american_odds(time_point.get("draw", "")),
                "away": format_american_odds(time_point.get("away_win", ""))
            }
    
    # Check for spread/handicap odds
    spread_odds = odds_data.get("SPREAD", [])
    if spread_odds and len(spread_odds) > 0:
        result["has_spread"] = True
        for time_point in spread_odds:
            minute = time_point.get("time_of_match", "0")
            result["spread_values"][minute] = {
                "home": format_american_odds(time_point.get("home", "")),
                "handicap": time_point.get("handicap", "0"),
                "away": format_american_odds(time_point.get("away", ""))
            }
    
    # Check for over/under odds
    ou_odds = odds_data.get("Over/Under", [])
    if ou_odds and len(ou_odds) > 0:
        result["has_ou"] = True
        for time_point in ou_odds:
            minute = time_point.get("time_of_match", "0")
            result["ou_values"][minute] = {
                "over": format_american_odds(time_point.get("over", "")),
                "line": time_point.get("line", "0"),
                "under": format_american_odds(time_point.get("under", ""))
            }
    
    return result

def check_odds_alert_conditions(odds_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check odds data for alert conditions.
    
    Args:
        odds_data: Parsed odds data from parse_odds_data()
        
    Returns:
        Dictionary with alert conditions
    """
    alerts = {
        "missing_ml": False,
        "missing_spread": False,
        "missing_ou": False,
        "unusual_handicap": False,
        "high_ou_line": False
    }
    
    # Check for missing odds types
    alerts["missing_ml"] = not odds_data["has_ml"]
    alerts["missing_spread"] = not odds_data["has_spread"]
    alerts["missing_ou"] = not odds_data["has_ou"]
    
    # Check for unusual handicap values
    for minute, values in odds_data["spread_values"].items():
        handicap = values.get("handicap", "0")
        try:
            handicap_float = float(handicap)
            if abs(handicap_float) > UNUSUAL_HANDICAP_THRESHOLD:
                alerts["unusual_handicap"] = True
                break
        except (ValueError, TypeError):
            pass
    
    # Check for high over/under lines
    for minute, values in odds_data["ou_values"].items():
        line = values.get("line", "0")
        try:
            line_float = float(line)
            if line_float >= HIGH_OVERUNDER_THRESHOLD:
                alerts["high_ou_line"] = True
                break
        except (ValueError, TypeError):
            pass
    
    return alerts

#==========================================
# ENVIRONMENT DATA PARSING
#==========================================

def parse_environment_data(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and parse environment data from match data.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        Dictionary with parsed environment data
    """
    result = {
        "has_weather": False,
        "has_temperature": False,
        "has_humidity": False,
        "has_wind": False,
        "weather": None,
        "temperature_c": None,
        "temperature_f": None,
        "humidity": None,
        "wind_speed_ms": None,
        "wind_speed_mph": None
    }
    
    # Check if match has environment data
    environment = match_data.get("environment", {})
    if not environment:
        return result
    
    # Parse weather
    weather = environment.get("weather", {})
    if weather:
        weather_code = weather.get("code")
        if weather_code:
            result["has_weather"] = True
            result["weather"] = get_weather_description(str(weather_code))
    
    # Parse temperature
    temperature = environment.get("temperature", {})
    if temperature:
        temp_c = temperature.get("temp")
        if temp_c is not None:
            try:
                temp_c_float = float(temp_c)
                result["has_temperature"] = True
                result["temperature_c"] = temp_c_float
                result["temperature_f"] = round((temp_c_float * 9/5) + 32, 1)
            except (ValueError, TypeError):
                pass
    
    # Parse humidity
    humidity = environment.get("humidity")
    if humidity is not None:
        try:
            humidity_float = float(humidity)
            result["has_humidity"] = True
            result["humidity"] = humidity_float
        except (ValueError, TypeError):
            pass
    
    # Parse wind
    wind = environment.get("wind", {})
    if wind:
        wind_speed = wind.get("speed")
        if wind_speed is not None:
            try:
                wind_speed_float = float(wind_speed)
                result["has_wind"] = True
                result["wind_speed_ms"] = wind_speed_float
                result["wind_speed_mph"] = round(wind_speed_float * 2.237, 1)  # m/s to mph
            except (ValueError, TypeError):
                pass
    
    return result

def check_environment_alert_conditions(env_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check environment data for alert conditions.
    
    Args:
        env_data: Parsed environment data from parse_environment_data()
        
    Returns:
        Dictionary with alert conditions
    """
    alerts = {
        "missing_weather": False,
        "missing_temperature": False,
        "high_temperature": False,
        "low_temperature": False,
        "high_wind": False
    }
    
    # Check for missing data
    alerts["missing_weather"] = not env_data["has_weather"]
    alerts["missing_temperature"] = not env_data["has_temperature"]
    
    # Check for extreme temperatures
    if env_data["has_temperature"] and env_data["temperature_c"] is not None:
        alerts["high_temperature"] = env_data["temperature_c"] >= TEMPERATURE_ALERT_THRESHOLD_C
        alerts["low_temperature"] = env_data["temperature_c"] <= LOW_TEMPERATURE_THRESHOLD_C
    
    # Check for high wind
    if env_data["has_wind"] and env_data["wind_speed_mph"] is not None:
        alerts["high_wind"] = env_data["wind_speed_mph"] >= WIND_ALERT_THRESHOLD_MPH
    
    return alerts

#==========================================
# SCORE DATA PARSING
#==========================================

def parse_score_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extract and parse score data from match data.
    
    Args:
        match_data: Current match data dictionary
        previous_data: Previous match data for comparison (optional)
        
    Returns:
        Dictionary with parsed score data and changes
    """
    result = {
        "has_score": False,
        "home_score": None,
        "away_score": None,
        "score_changed": False,
        "home_score_changed": False,
        "away_score_changed": False,
        "previous_home_score": None,
        "previous_away_score": None
    }
    
    # Get current scores
    home_score = match_data.get("home_score")
    away_score = match_data.get("away_score")
    
    if home_score is not None and away_score is not None:
        result["has_score"] = True
        try:
            result["home_score"] = int(home_score)
            result["away_score"] = int(away_score)
        except (ValueError, TypeError):
            # Handle non-integer scores
            result["home_score"] = home_score
            result["away_score"] = away_score
    
    # Compare with previous data if available
    if previous_data and result["has_score"]:
        prev_home_score = previous_data.get("home_score")
        prev_away_score = previous_data.get("away_score")
        
        if prev_home_score is not None and prev_away_score is not None:
            try:
                result["previous_home_score"] = int(prev_home_score)
                result["previous_away_score"] = int(prev_away_score)
                
                # Check if scores have changed
                result["home_score_changed"] = result["home_score"] != result["previous_home_score"]
                result["away_score_changed"] = result["away_score"] != result["previous_away_score"]
                result["score_changed"] = result["home_score_changed"] or result["away_score_changed"]
            except (ValueError, TypeError):
                # Handle case where previous scores are not integers
                result["previous_home_score"] = prev_home_score
                result["previous_away_score"] = prev_away_score
                result["home_score_changed"] = str(result["home_score"]) != str(prev_home_score)
                result["away_score_changed"] = str(result["away_score"]) != str(prev_away_score)
                result["score_changed"] = result["home_score_changed"] or result["away_score_changed"]
    
    return result

def check_score_change(score_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check if score has changed.
    
    Args:
        score_data: Parsed score data from parse_score_data()
        
    Returns:
        Dictionary with score change information
    """
    return {
        "score_changed": score_data["score_changed"],
        "home_scored": score_data["home_score_changed"] and score_data["previous_home_score"] is not None and 
                       score_data["home_score"] > score_data["previous_home_score"],
        "away_scored": score_data["away_score_changed"] and score_data["previous_away_score"] is not None and 
                       score_data["away_score"] > score_data["previous_away_score"]
    }

#==========================================
# ALERT ANALYSIS AND GENERATION
#==========================================

def analyze_match_for_alerts(match_data: Dict[str, Any], 
                           previous_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze match data for potential alert conditions.
    
    Args:
        match_data: Current match data dictionary
        previous_data: Previous match data for comparison (optional)
        
    Returns:
        Dictionary with alert analysis results
    """
    result = {
        "match_id": match_data.get("id", "Unknown"),
        "home_team": match_data.get("home_team", "Home Team"),
        "away_team": match_data.get("away_team", "Away Team"),
        "competition": match_data.get("competition", "Unknown Competition"),
        "competition_id": match_data.get("competition_id", "Unknown"),
        "timestamp": datetime.now().strftime("%m/%d/%Y %I:%M:%S %p ET"),
        "should_alert": False,
        "alert_reasons": []
    }
    
    # Copy relevant match data to result
    for field in ["status_id", "minute", "venue", "home_score", "away_score", 
                 "ht_home_score", "ht_away_score", "odds", "environment"]:
        if field in match_data:
            result[field] = match_data[field]
    
    # Verify match structure
    structure = verify_match_structure(match_data)
    result["structure"] = structure
    
    # Check if basic data is missing
    if not structure["has_core_data"] or not structure["has_teams"]:
        result["should_alert"] = True
        result["alert_reasons"].append("Missing core match data")
    
    # Parse and check odds data
    odds_data = parse_odds_data(match_data)
    result["odds_data"] = odds_data
    odds_alerts = check_odds_alert_conditions(odds_data)
    result["odds_alerts"] = odds_alerts
    
    # Check for odds alerts
    if structure["has_odds"] and (odds_alerts["missing_ml"] or odds_alerts["missing_spread"] or odds_alerts["missing_ou"]):
        result["should_alert"] = True
        if odds_alerts["missing_ml"]:
            result["alert_reasons"].append("Missing money line odds")
        if odds_alerts["missing_spread"]:
            result["alert_reasons"].append("Missing spread/handicap odds")
        if odds_alerts["missing_ou"]:
            result["alert_reasons"].append("Missing over/under odds")
    
    # Check for unusual odds values
    if odds_alerts["unusual_handicap"]:
        result["should_alert"] = True
        result["alert_reasons"].append("Unusual handicap value detected")
    if odds_alerts["high_ou_line"]:
        result["should_alert"] = True
        result["alert_reasons"].append("High over/under line detected")
    
    # Parse and check environment data
    env_data = parse_environment_data(match_data)
    result["env_data"] = env_data
    env_alerts = check_environment_alert_conditions(env_data)
    result["env_alerts"] = env_alerts
    
    # Check for environment alerts
    if structure["has_environment"]:
        if env_alerts["high_temperature"]:
            result["should_alert"] = True
            result["alert_reasons"].append(f"High temperature: {env_data['temperature_c']}°C / {env_data['temperature_f']}°F")
        if env_alerts["low_temperature"]:
            result["should_alert"] = True
            result["alert_reasons"].append(f"Low temperature: {env_data['temperature_c']}°C / {env_data['temperature_f']}°F")
        if env_alerts["high_wind"]:
            result["should_alert"] = True
            result["alert_reasons"].append(f"High wind speed: {env_data['wind_speed_mph']} mph")
    
    # Parse and check score data if previous data is available
    if previous_data:
        score_data = parse_score_data(match_data, previous_data)
        result["score_data"] = score_data
        score_changes = check_score_change(score_data)
        result["score_changes"] = score_changes
        
        # Check for score change alerts
        if score_changes["score_changed"]:
            result["should_alert"] = True
            if score_changes["home_scored"]:
                result["alert_reasons"].append(f"Goal! {result['home_team']} scored")
            if score_changes["away_scored"]:
                result["alert_reasons"].append(f"Goal! {result['away_team']} scored")
    
    return result

def generate_alert_message(alert_data: Dict[str, Any], alert_type: str = "general") -> str:
    """
    Generate a formatted alert message with comprehensive match details.
    
    Args:
        alert_data: Dictionary with alert information from analyze_match_for_alerts()
        alert_type: Type of alert (odds, score, environment, general)
        
    Returns:
        Formatted alert message string with all match details
    """
    # Get basic match information
    match_id = alert_data.get("match_id", "Unknown")
    home_team = alert_data.get("home_team", "Home Team")
    away_team = alert_data.get("away_team", "Away Team")
    competition = alert_data.get("competition", "Unknown Competition")
    competition_id = alert_data.get("competition_id", "Unknown")
    
    # Get score and status information
    home_score = alert_data.get("home_score", "0")
    away_score = alert_data.get("away_score", "0")
    status_id = str(alert_data.get("status_id", "Unknown"))
    minute = alert_data.get("minute", "Unknown")
    
    # Get half-time score if available
    ht_home_score = alert_data.get("ht_home_score", "0")
    ht_away_score = alert_data.get("ht_away_score", "0")
    ht_score = f"(HT: {ht_home_score} - {ht_away_score})"
    
    # Map status ID to readable status
    status_text = STATUS_MAP.get(status_id, f"Unknown (Status ID: {status_id})")
    
    # Get venue information
    venue = alert_data.get("venue", "Unknown Venue")
    
    # Get timestamp
    timestamp = alert_data.get("timestamp", datetime.now().strftime("%m/%d/%Y %I:%M:%S %p ET"))
    
    # Start building the message
    emoji_map = {
        "odds": "📊",
        "score": "⚽",
        "environment": "🌤️",
        "general": "⚠️"
    }
    alert_emoji = emoji_map.get(alert_type.lower(), "⚠️")
    
    message = f"{alert_emoji} ALERT: {alert_type.upper()} {alert_emoji}\n\n"
    
    # Match summary section
    message += f"📋 MATCH SUMMARY\n"
    message += f"───────────────────\n"
    message += f"Timestamp: {timestamp}\n"
    message += f"Match ID: {match_id}\n"
    message += f"Competition ID: {competition_id}\n"
    message += f"Competition: {competition}\n"
    message += f"Match: {home_team} vs {away_team}\n"
    message += f"Score: {home_score} - {away_score} {ht_score}\n"
    message += f"Status: {status_text}"
    if minute and minute != "Unknown":
        message += f" (minute {minute})"
    message += "\n\n"
    
    # Add betting odds section if available
    odds_data = alert_data.get("odds", {})
    if odds_data:
        message += f"💰 MATCH BETTING ODDS\n"
        message += f"───────────────────\n"
        
        # ML odds
        ml_odds = odds_data.get("ML", [])
        if ml_odds:
            message += f"ML (Money Line):\n"
            for time_point in ml_odds:
                time_of_match = time_point.get("time_of_match", "N/A")
                home_win = time_point.get("home_win", "N/A")
                draw = time_point.get("draw", "N/A")
                away_win = time_point.get("away_win", "N/A")
                message += f"Time: {time_of_match} min | Home: {home_win} | Draw: {draw} | Away: {away_win}\n"
            message += "\n"
        
        # Spread odds
        spread_odds = odds_data.get("SPREAD", [])
        if spread_odds:
            message += f"SPREAD (Asia Handicap):\n"
            for time_point in spread_odds:
                time_of_match = time_point.get("time_of_match", "N/A")
                home = time_point.get("home", "N/A")
                handicap = time_point.get("handicap", "N/A")
                away = time_point.get("away", "N/A")
                message += f"Time: {time_of_match} min | Home: {home} | Handicap: {handicap} | Away: {away}\n"
            message += "\n"
        
        # Over/Under odds
        ou_odds = odds_data.get("Over/Under", [])
        if ou_odds:
            message += f"Over/Under:\n"
            for time_point in ou_odds:
                time_of_match = time_point.get("time_of_match", "N/A")
                over = time_point.get("over", "N/A")
                line = time_point.get("line", "N/A")
                under = time_point.get("under", "N/A")
                message += f"Time: {time_of_match} min | Over: {over} | Line: {line} | Under: {under}\n"
            message += "\n"
    
    # Add environment data if available
    environment = alert_data.get("environment", {})
    if environment:
        message += f"🌤️ MATCH ENVIRONMENT\n"
        message += f"───────────────────\n"
        
        # Weather
        weather = environment.get("weather", {})
        weather_code = weather.get("code", "")
        weather_desc = get_weather_description(str(weather_code)) if weather_code else "N/A"
        if weather_desc != "N/A":
            message += f"Weather: {weather_desc}\n"
        
        # Temperature
        temperature = environment.get("temperature", {})
        temp_c = temperature.get("temp", "N/A")
        if temp_c != "N/A":
            try:
                temp_f = round((float(temp_c) * 9/5) + 32, 1)
                message += f"Temperature: {temp_c}°C / {temp_f}°F\n"
            except (ValueError, TypeError):
                pass
        
        # Humidity
        humidity = environment.get("humidity", "N/A")
        if humidity != "N/A":
            message += f"Humidity: {humidity}%\n"
        
        # Wind
        wind = environment.get("wind", {})
        wind_speed_ms = wind.get("speed", "N/A")
        if wind_speed_ms != "N/A":
            try:
                wind_speed_mph = round(float(wind_speed_ms) * 2.237, 1)  # m/s to mph
                message += f"Wind: {wind_speed_ms}m/s ({wind_speed_mph} mph)\n"
            except (ValueError, TypeError):
                message += f"Wind: {wind_speed_ms}m/s\n"
    
    # Add alert reasons
    if "alert_reasons" in alert_data and alert_data["alert_reasons"]:
        message += "\n📢 ALERT REASONS\n"
        message += f"───────────────────\n"
        for reason in alert_data["alert_reasons"]:
            message += f"• {reason}\n"
    
    return message

def should_deduplicate_alert(match_id: str, alert_type: str, alert_reasons: List[str], 
                           previous_alerts: Dict[str, List[Dict[str, Any]]] = None,
                           threshold_seconds: int = ALERT_DEDUPLICATION_TIMEOUT) -> bool:
    """
    Determine if an alert should be deduplicated based on previous alerts.
    
    Args:
        match_id: Match identifier
        alert_type: Type of alert
        alert_reasons: Current alert reasons
        previous_alerts: Dictionary of match_id -> previous alerts
        threshold_seconds: Time threshold for deduplication (default: 15 minutes)
        
    Returns:
        True if alert should be deduplicated (not sent), False otherwise
    """
    # If no previous alerts, don't deduplicate
    if not previous_alerts or match_id not in previous_alerts:
        return False
    
    # Get current time
    current_time = time.time()
    
    # For each previous alert for this match
    for prev_alert in previous_alerts[match_id]:
        # Skip if different alert type
        if prev_alert.get("type") != alert_type:
            continue
            
        # Check if same reasons and within time threshold
        prev_reasons = set(prev_alert.get("reasons", []))
        current_reasons = set(alert_reasons)
        
        # If same reasons and within time threshold, deduplicate
        if prev_reasons == current_reasons and \
           current_time - prev_alert.get("timestamp", 0) < threshold_seconds:
            return True
    
    return False


#==========================================
# ALERT ORCHESTRATION SYSTEM
#==========================================

# Track loaded alert modules
loaded_alert_modules = {}

# Store alert history for deduplication
alert_history = {}

def discover_alert_modules() -> Dict[str, Any]:
    """
    Dynamically discover all alert modules in the live_alerts directory.
    
    Alert modules must:
    1. Have '_alert.py' in their filename
    2. Implement process_match_data() function
    
    Returns:
        Dictionary of module names to module objects
    """
    global loaded_alert_modules
    
    # Directory containing alert modules
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Clear existing modules
    loaded_alert_modules = {}
    
    # Get all Python files in the alerts directory that end with _alert.py
    alert_files = [f for f in os.listdir(alerts_dir) 
                   if f.endswith('_alert.py') and os.path.isfile(os.path.join(alerts_dir, f))]
    
    # First load all priority alert modules to ensure they're always available
    priority_files = []
    
    # Find all alert files that match any of the priority patterns
    for pattern in PRIORITY_ALERT_PATTERNS:
        for alert_file in alert_files:
            # Check if file matches the pattern (either exact match or glob pattern)
            if pattern.endswith('.py'):
                # Exact filename match
                if alert_file == pattern:
                    priority_files.append(alert_file)
            elif '*' in pattern:
                # Glob pattern match
                import fnmatch
                if fnmatch.fnmatch(alert_file, pattern):
                    priority_files.append(alert_file)
    
    # Remove duplicates while preserving order
    priority_files = list(dict.fromkeys(priority_files))
    
    # Load each priority module with extra care
    for priority_file in priority_files:
        module_name = priority_file[:-3]  # Remove .py extension
        try:
            # Import the module with extra error handling
            try:
                module = importlib.import_module(f"football.live_alerts.{module_name}")
            except ModuleNotFoundError:
                # Fall back to direct import if needed
                import sys
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    module_name, os.path.join(alerts_dir, priority_file))
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                sys.modules[f"football.live_alerts.{module_name}"] = module
            
            # Check if it has the required process_match_data function
            if hasattr(module, 'process_match_data') and callable(module.process_match_data):
                loaded_alert_modules[module_name] = module
                print(f"✓ Loaded PRIORITY alert module: {module_name}")
            else:
                print(f"✗ Failed to load PRIORITY module {module_name}: Missing process_match_data function")
        except Exception as e:
            print(f"✗ Error loading PRIORITY module {module_name}: {str(e)}")
            traceback.print_exc()
    
    # Import each regular alert module
    for alert_file in alert_files:
        # Skip priority modules that were already processed
        if alert_file in priority_files:
            continue
            
        module_name = alert_file[:-3]  # Remove .py extension
        try:
            # Import the module
            module = importlib.import_module(f"football.live_alerts.{module_name}")
            
            # Check if it has the required process_match_data function
            if hasattr(module, 'process_match_data') and callable(module.process_match_data):
                loaded_alert_modules[module_name] = module
                print(f"✓ Loaded alert module: {module_name}")
            else:
                print(f"✗ Skipped {module_name}: Missing process_match_data function")
        except Exception as e:
            print(f"✗ Error loading {module_name}: {str(e)}")
    
    print(f"Alert system discovered {len(loaded_alert_modules)} alert modules")
    return loaded_alert_modules

def send_sports_alert(module_name: str, match_data: Dict[str, Any]) -> bool:
    """
    Send a sports alert to Telegram based on an alert module trigger.
    
    Args:
        module_name: Name of the triggered alert module
        match_data: Current match data dictionary
        
    Returns:
        True if alert was sent successfully, False otherwise
    """
    try:
        # Extract needed fields from match_data
        match_id = match_data.get('id', 'unknown')
        home_team = match_data.get('home_team', 'Home Team')
        away_team = match_data.get('away_team', 'Away Team')
        competition = match_data.get('competition', 'Unknown Competition')
        country = match_data.get('country', '')
        home_score = match_data.get('home_score', '0')
        away_score = match_data.get('away_score', '0')
        
        # Get odds data for specialized alerts
        ou_line = match_data.get('ou_line')
        ou_over = match_data.get('ou_over')
        ou_under = match_data.get('ou_under')
        ml_home = match_data.get('ml_home')
        ml_draw = match_data.get('ml_draw')
        ml_away = match_data.get('ml_away')
        
        # Format alert message
        alert_message = f"⚽ SPORTS ALERT: {module_name}\n\n"
        alert_message += f"Match: {home_team} vs {away_team}\n"
        alert_message += f"Competition: {competition} {f'({country})' if country else ''}\n"
        alert_message += f"Current Score: {home_score} - {away_score}\n\n"
        
        # Add odds data based on the alert type
        if "overunder" in module_name.lower() and ou_line is not None:
            alert_message += f"Over/Under Line: {ou_line}\n"
            if ou_over is not None:
                alert_message += f"Over: {format_american_odds(ou_over)}\n"
            if ou_under is not None:
                alert_message += f"Under: {format_american_odds(ou_under)}\n"
        elif "odds" in module_name.lower():
            # Add money line odds
            if ml_home is not None and ml_away is not None:
                alert_message += f"ML Home: {format_american_odds(ml_home)}\n"
                alert_message += f"ML Away: {format_american_odds(ml_away)}\n"
                if ml_draw is not None:
                    alert_message += f"ML Draw: {format_american_odds(ml_draw)}\n"
        
        # Add match ID for reference
        alert_message += f"\nMatch ID: {match_id}"
        
        # Attempt to send via Telegram
        try:
            # First try direct import (if this module is imported directly)
            from football.telegram import send_match_alert as football_send_match_alert
            send_match_alert = football_send_match_alert
        except ImportError:
            # Fall back to global import (if imported through other means)
            try:
                from telegram import send_match_alert
            except ImportError:
                print(f"[SPORTS_ALERT] Could not import Telegram module, alert not sent: {module_name}")
                return False
        
        # Send to Telegram using match alert type
        send_match_alert(
            message=f"{module_name} detected",
            match_id=match_id,
            teams=f"{home_team} vs {away_team}",
            score=f"{home_score} - {away_score}",
            competition=competition,
            alert_type="odds" if "odds" in module_name.lower() else "match"
        )
        return True
    except Exception as e:
        print(f"[SPORTS_ALERT] Error sending alert for {module_name}: {str(e)}")
        return False


def process_match_with_alerts(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> Dict[str, bool]:
    """
    Process a match through all loaded alert modules.
    
    This is the main entry point called by live.py to process match data
    through all available alert modules.
    
    Args:
        match_data: Current match data
        previous_data: Previous match data for comparison (optional)
        
    Returns:
        Dictionary of alert module names and whether they triggered
    """
    global loaded_alert_modules
    
    # Ensure modules are loaded
    if not loaded_alert_modules:
        discover_alert_modules()
    
    # Track which modules triggered alerts
    results = {}
    
    # Check if Telegram is available - try both direct and indirect import paths
    telegram_available = False
    try:
        # First try direct import (if this module is imported directly)
        from football.telegram import send_match_alert as football_send_match_alert
        telegram_available = True
    except ImportError:
        # Fall back to global import (if imported through other means)
        try:
            from telegram import send_match_alert
            telegram_available = True
        except ImportError:
            telegram_available = False
    
    # Process priority modules first (based on configured patterns)
    priority_modules = [m for m in PRIORITY_ALERT_MODULES if m.endswith('.py') or '*' not in m]
    regular_modules = {}
    
    # Split modules into priority and regular
    for module_name, module in loaded_alert_modules.items():
        if module_name in priority_modules:
            # Process priority module immediately
            try:
                # Determine if the module accepts previous_data parameter
                params = inspect.signature(module.process_match_data).parameters
                
                # Call the module's process_match_data function with appropriate parameters
                if 'previous_data' in params and previous_data is not None:
                    # Module accepts previous_data
                    triggered = module.process_match_data(match_data, previous_data)
                else:
                    # Module doesn't use previous_data
                    triggered = module.process_match_data(match_data)
                
                results[module_name] = triggered
                
                # If alert was triggered, log and send notification
                if triggered:
                    match_id = match_data.get('id', 'unknown')
                    home_team = match_data.get('home_team', 'Home')
                    away_team = match_data.get('away_team', 'Away')
                    
                    # Log the alert trigger
                    print(f"[PRIORITY_ALERT] {module_name} triggered for {home_team} vs {away_team} (ID: {match_id})")
                    
                    # Send the alert to Telegram if available
                    if telegram_available:
                        send_sports_alert(module_name, match_data)
                
            except Exception as e:
                # Use more extensive error handling for priority modules
                print(f"Error in PRIORITY alert module {module_name}: {str(e)}")
                traceback.print_exc()  # Print full traceback for priority modules
                results[module_name] = False
        else:
            # Save regular modules for later processing
            regular_modules[module_name] = module
    
    # Process remaining regular modules
    for module_name, module in regular_modules.items():
        try:
            # Determine if the module accepts previous_data parameter
            params = inspect.signature(module.process_match_data).parameters
            
            # Call the module's process_match_data function with appropriate parameters
            if 'previous_data' in params and previous_data is not None:
                # Module accepts previous_data
                triggered = module.process_match_data(match_data, previous_data)
            else:
                # Module doesn't use previous_data
                triggered = module.process_match_data(match_data)
            
            results[module_name] = triggered
            
            # If alert was triggered, log and send notification
            if triggered:
                match_id = match_data.get('id', 'unknown')
                home_team = match_data.get('home_team', 'Home')
                away_team = match_data.get('away_team', 'Away')
                
                # Log the alert trigger
                print(f"[SPORTS_ALERT] {module_name} triggered for {home_team} vs {away_team} (ID: {match_id})")
                
                # Send the alert to Telegram if available
                if telegram_available:
                    send_sports_alert(module_name, match_data)
            
        except Exception as e:
            # Just log the error without using system alert channels
            print(f"Error in alert module {module_name}: {str(e)}")
            results[module_name] = False
    
    return results

def reset_alert_caches() -> None:
    """
    Reset caches in all loaded alert modules.
    
    This can be called periodically to clear any stored alert state
    and prevent memory leaks in long-running processes.
    """
    global loaded_alert_modules
    
    for module_name, module in loaded_alert_modules.items():
        # Check if the module has a reset_alert_cache function
        if hasattr(module, 'reset_alert_cache') and callable(module.reset_alert_cache):
            try:
                module.reset_alert_cache()
                print(f"Reset cache for {module_name}")
            except Exception as e:
                print(f"Error resetting cache for {module_name}: {str(e)}")

# Initialize alert modules when this module is imported
import importlib
import inspect
try:
    discover_alert_modules()
except Exception as e:
    print(f"Warning: Could not initialize alert modules: {str(e)}")

