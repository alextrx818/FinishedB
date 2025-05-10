#!/usr/bin/env python3
"""
Parse Alert Logic

Core logic module for parsing and analyzing match data to determine alert conditions.
This module provides standardized functions for interpreting raw API data from 
thesports.com and identifying various alert criteria such as missing odds data,
score changes, or abnormal weather conditions.
"""

import os
import sys
import re
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Union

# Add project root to path to allow imports from other modules
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

# Constants for alert thresholds
MINIMUM_ODDS_COUNT = 3  # Minimum number of odds entries expected
TEMPERATURE_ALERT_THRESHOLD_C = 35  # Alert if temperature above 35°C
WIND_ALERT_THRESHOLD_MPH = 25  # Alert if wind above 25 mph
EXPECTED_ODDS_TYPES = ["SPREAD", "ML", "Over/Under"]

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
        Dictionary with boolean verification results for each component
    """
    verification = {
        "core_fields": False,
        "team_info": False,
        "score_data": False,
        "odds_data": False,
        "environment_data": False
    }
    
    # Verify core fields
    required_core = ["id", "status_id", "minute", "timestamp"]
    verification["core_fields"] = all(field in match_data for field in required_core)
    
    # Verify team information
    required_team = ["home_team", "away_team", "competition", "country"]
    verification["team_info"] = all(field in match_data for field in required_team)
    
    # Verify score data
    required_score = ["home_score", "away_score"]
    verification["score_data"] = all(field in match_data for field in required_score)
    
    # Verify odds data (any odds types present)
    verification["odds_data"] = "odds" in match_data and isinstance(match_data["odds"], dict)
    
    # Verify environment data (any environment fields present)
    env_fields = ["weather", "temperature", "humidity", "wind"]
    verification["environment_data"] = any(field in match_data for field in env_fields)
    
    return verification

def identify_missing_components(match_data: Dict[str, Any]) -> List[str]:
    """
    Identify which components are missing or incomplete in the match data.
    
    Args:
        match_data: The match data dictionary
        
    Returns:
        List of component names that are missing or incomplete
    """
    verification = verify_match_structure(match_data)
    return [component for component, status in verification.items() if not status]

#==========================================
# ODDS DATA PARSING
#==========================================

def parse_odds_data(odds_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and validate odds data, extracting key values.
    
    Args:
        odds_data: Raw odds data from the API or match_data["odds"]
        
    Returns:
        Dictionary with standardized odds values and validation flags
    """
    result = {
        "has_ml": False,
        "has_spread": False,
        "has_ou": False,
        "ml_values": {},
        "spread_values": {},
        "ou_values": {},
        "is_complete": False
    }
    
    if not odds_data:
        return result
    
    # Check for Money Line (ML) odds
    if "ML" in odds_data and odds_data["ML"]:
        ml_entries = odds_data["ML"]
        # Find entries from minutes 4-6 (critical period for ML odds)
        target_entries = [e for e in ml_entries if e.get("time_of_match") in ["4", "5", "6"]]
        
        # Use best available entry (target minutes or latest)
        ml_entry = target_entries[-1] if target_entries else ml_entries[-1] if ml_entries else None
        
        if ml_entry:
            result["has_ml"] = True
            result["ml_values"] = {
                "home_win": ml_entry.get("home_win"),
                "draw": ml_entry.get("draw"),
                "away_win": ml_entry.get("away_win"),
                "time": ml_entry.get("time_of_match")
            }
    
    # Check for Spread (Asian handicap) odds
    if "SPREAD" in odds_data and odds_data["SPREAD"]:
        spread_entries = odds_data["SPREAD"]
        # Find any valid spread entry
        spread_entry = spread_entries[-1] if spread_entries else None
        
        if spread_entry:
            result["has_spread"] = True
            result["spread_values"] = {
                "home_win": spread_entry.get("home_win"),
                "handicap": spread_entry.get("handicap"),
                "away_win": spread_entry.get("away_win"),
                "time": spread_entry.get("time_of_match")
            }
    
    # Check for Over/Under odds
    if "Over/Under" in odds_data and odds_data["Over/Under"]:
        ou_entries = odds_data["Over/Under"]
        # Find any valid over/under entry
        ou_entry = ou_entries[-1] if ou_entries else None
        
        if ou_entry:
            result["has_ou"] = True
            result["ou_values"] = {
                "over": ou_entry.get("over"),
                "handicap": ou_entry.get("handicap"),
                "under": ou_entry.get("under"),
                "time": ou_entry.get("time_of_match")
            }
    
    # Check if odds data is complete (all three types present)
    result["is_complete"] = all([result["has_ml"], result["has_spread"], result["has_ou"]])
    
    return result

def check_odds_alert_conditions(odds_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check if odds data triggers any alert conditions.
    
    Args:
        odds_data: Parsed odds data from parse_odds_data()
        
    Returns:
        Dictionary of alert conditions and whether they're triggered
    """
    alerts = {
        "missing_ml": not odds_data["has_ml"],
        "missing_spread": not odds_data["has_spread"],
        "missing_ou": not odds_data["has_ou"],
        "incomplete_odds": not odds_data["is_complete"],
        "unusual_handicap": False,
        "high_variance": False
    }
    
    # Check for unusual handicap values (absolute value > 3)
    if odds_data["has_spread"]:
        try:
            handicap = float(odds_data["spread_values"]["handicap"])
            alerts["unusual_handicap"] = abs(handicap) > 3
        except (ValueError, TypeError):
            pass
    
    # Check for high variance in over/under line
    if odds_data["has_ou"]:
        try:
            ou_line = float(odds_data["ou_values"]["handicap"])
            alerts["high_variance"] = ou_line > 4.5
        except (ValueError, TypeError):
            pass
    
    return alerts

#==========================================
# SCORE DATA PARSING
#==========================================

def parse_score_data(score_data: Union[List, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse and standardize score data from the API response.
    
    Args:
        score_data: Score data from the API (list format) or match_data
        
    Returns:
        Dictionary with standardized score values
    """
    result = {
        "home_live_score": 0,
        "away_live_score": 0,
        "home_ht_score": 0,
        "away_ht_score": 0,
        "is_complete": False
    }
    
    # Handle direct dictionary format (preprocessed)
    if isinstance(score_data, dict):
        if "home_score" in score_data and "away_score" in score_data:
            result["home_live_score"] = score_data.get("home_score", 0)
            result["away_live_score"] = score_data.get("away_score", 0)
            result["home_ht_score"] = score_data.get("home_ht_score", 0)
            result["away_ht_score"] = score_data.get("away_ht_score", 0)
            result["is_complete"] = True
        return result
    
    # Handle API list format
    if isinstance(score_data, list) and len(score_data) > 3:
        # Extract home scores
        home_scores = score_data[2]
        if isinstance(home_scores, list) and len(home_scores) > 1:
            # Extract live score (first element)
            if isinstance(home_scores[0], str) and " " in home_scores[0]:
                result["home_live_score"] = home_scores[0].split(" ")[0]
            else:
                result["home_live_score"] = home_scores[0]
            
            # Extract half-time score (second element)
            if isinstance(home_scores[1], str) and " " in home_scores[1]:
                result["home_ht_score"] = home_scores[1].split(" ")[0]
            else:
                result["home_ht_score"] = home_scores[1]
        
        # Extract away scores
        away_scores = score_data[3]
        if isinstance(away_scores, list) and len(away_scores) > 1:
            # Extract live score (first element)
            if isinstance(away_scores[0], str) and " " in away_scores[0]:
                result["away_live_score"] = away_scores[0].split(" ")[0]
            else:
                result["away_live_score"] = away_scores[0]
            
            # Extract half-time score (second element)
            if isinstance(away_scores[1], str) and " " in away_scores[1]:
                result["away_ht_score"] = away_scores[1].split(" ")[0]
            else:
                result["away_ht_score"] = away_scores[1]
        
        result["is_complete"] = True
    
    return result

def check_score_change(previous_scores: Dict[str, Any], current_scores: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check if there has been a score change between two score snapshots.
    
    Args:
        previous_scores: Previously parsed score data
        current_scores: Current parsed score data
        
    Returns:
        Dictionary indicating which team scored and what changed
    """
    changes = {
        "home_scored": False,
        "away_scored": False,
        "score_changed": False
    }
    
    # Convert all values to integers for comparison
    try:
        prev_home = int(previous_scores["home_live_score"])
        prev_away = int(previous_scores["away_live_score"])
        curr_home = int(current_scores["home_live_score"])
        curr_away = int(current_scores["away_live_score"])
        
        changes["home_scored"] = curr_home > prev_home
        changes["away_scored"] = curr_away > prev_away
        changes["score_changed"] = changes["home_scored"] or changes["away_scored"]
    except (ValueError, TypeError):
        # If conversion fails, we can't reliably detect changes
        pass
    
    return changes

#==========================================
# ENVIRONMENT DATA PARSING
#==========================================

def parse_environment_data(match_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and standardize environment data from match data.
    
    Args:
        match_data: Match data dictionary
        
    Returns:
        Dictionary with standardized environment values
    """
    result = {
        "has_weather": False,
        "has_temperature": False,
        "has_humidity": False,
        "has_wind": False,
        "weather_description": "",
        "temperature_c": None,
        "temperature_f": None,
        "humidity_pct": None,
        "wind_mph": None,
        "is_complete": False
    }
    
    # Extract weather and convert code to description
    weather = match_data.get("weather")
    if weather:
        result["has_weather"] = True
        result["weather_description"] = get_weather_description(weather)
    
    # Extract and convert temperature
    temperature = match_data.get("temperature")
    if temperature:
        result["has_temperature"] = True
        try:
            temp_c = float(temperature)
            result["temperature_c"] = temp_c
            result["temperature_f"] = (temp_c * 9/5) + 32
        except (ValueError, TypeError):
            pass
    
    # Extract humidity
    humidity = match_data.get("humidity")
    if humidity:
        result["has_humidity"] = True
        try:
            # Extract numeric part if it ends with %
            if isinstance(humidity, str) and "%" in humidity:
                humidity = humidity.replace("%", "").strip()
            result["humidity_pct"] = float(humidity)
        except (ValueError, TypeError):
            pass
    
    # Extract and convert wind
    wind = match_data.get("wind")
    if wind:
        result["has_wind"] = True
        try:
            # Extract numeric part and convert m/s to mph
            if isinstance(wind, str):
                wind_value = wind.replace("m/s", "").strip()
                wind_ms = float(wind_value)
                result["wind_mph"] = wind_ms * 2.237  # Convert m/s to mph
        except (ValueError, TypeError):
            pass
    
    # Check if environment data is reasonably complete
    env_fields = [result["has_weather"], result["has_temperature"], 
                 result["has_humidity"], result["has_wind"]]
    result["is_complete"] = sum(env_fields) >= 2  # At least 2 environment fields
    
    return result

def check_environment_alert_conditions(env_data: Dict[str, Any]) -> Dict[str, bool]:
    """
    Check if environment data triggers any alert conditions.
    
    Args:
        env_data: Parsed environment data from parse_environment_data()
        
    Returns:
        Dictionary of alert conditions and whether they're triggered
    """
    alerts = {
        "missing_weather": not env_data["has_weather"],
        "missing_temperature": not env_data["has_temperature"],
        "missing_humidity": not env_data["has_humidity"],
        "missing_wind": not env_data["has_wind"],
        "extreme_temperature": False,
        "high_wind": False
    }
    
    # Check for extreme temperature
    if env_data["temperature_c"] is not None:
        alerts["extreme_temperature"] = env_data["temperature_c"] > TEMPERATURE_ALERT_THRESHOLD_C
    
    # Check for high wind
    if env_data["wind_mph"] is not None:
        alerts["high_wind"] = env_data["wind_mph"] > WIND_ALERT_THRESHOLD_MPH
    
    return alerts

#==========================================
# HELPER FUNCTIONS
#==========================================

def get_weather_description(weather_code: str) -> str:
    """
    Convert numeric weather code to a human-readable description.
    
    Args:
        weather_code: Weather code from API
        
    Returns:
        Human-readable weather description
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

def format_american_odds(odds_value: int) -> str:
    """
    Format American odds with consistent sign display.
    
    Args:
        odds_value: Integer odds value
        
    Returns:
        Formatted odds string with sign
    """
    return f"{odds_value:+d}"

def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert decimal (European) odds to American format.
    
    Args:
        decimal_odds: Decimal odds value
        
    Returns:
        American odds as integer
    """
    if decimal_odds >= 2.0:
        return int(round((decimal_odds - 1) * 100))
    else:
        return int(round(-100 / (decimal_odds - 1)))

def hk_to_american(hk_odds: float) -> int:
    """
    Convert Hong Kong odds to American format.
    
    Args:
        hk_odds: Hong Kong odds value
        
    Returns:
        American odds as integer
    """
    # Convert HK to decimal first, then to American
    decimal_odds = hk_odds + 1.0
    return decimal_to_american(decimal_odds)

#==========================================
# MAIN ALERT LOGIC
#==========================================

def analyze_match_for_alerts(match_data: Dict[str, Any], 
                            previous_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Analyze a match for all possible alert conditions.
    
    Args:
        match_data: Current match data
        previous_data: Previous match data for comparison (optional)
        
    Returns:
        Dictionary with all detected alert conditions
    """
    # Initialize result
    result = {
        "match_id": match_data.get("id"),
        "teams": f"{match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}",
        "competition": match_data.get("competition", "Unknown"),
        "missing_components": [],
        "odds_alerts": {},
        "score_alerts": {},
        "environment_alerts": {},
        "should_alert": False,
        "alert_reasons": []
    }
    
    # Check for missing components
    result["missing_components"] = identify_missing_components(match_data)
    
    # Parse and check odds data
    odds_data = parse_odds_data(match_data.get("odds", {}))
    result["odds_alerts"] = check_odds_alert_conditions(odds_data)
    
    # Parse and check environment data
    env_data = parse_environment_data(match_data)
    result["environment_alerts"] = check_environment_alert_conditions(env_data)
    
    # Parse and check score data
    score_data = parse_score_data(match_data)
    
    # Check for score changes if previous data is available
    if previous_data:
        prev_score_data = parse_score_data(previous_data)
        result["score_alerts"] = check_score_change(prev_score_data, score_data)
    
    # Determine if we should send an alert based on all conditions
    # Add any triggered conditions to alert_reasons
    
    # Check for missing odds
    for odds_type in ["missing_ml", "missing_spread", "missing_ou"]:
        if result["odds_alerts"].get(odds_type, False):
            result["should_alert"] = True
            result["alert_reasons"].append(f"Missing {odds_type.replace('missing_', '').upper()} odds")
    
    # Check for missing environment data
    if result["environment_alerts"].get("missing_weather", False) and \
       result["environment_alerts"].get("missing_temperature", False):
        result["should_alert"] = True
        result["alert_reasons"].append("Missing weather and temperature data")
    
    # Check for extreme conditions
    if result["environment_alerts"].get("extreme_temperature", False):
        result["should_alert"] = True
        result["alert_reasons"].append("Extreme temperature detected")
    
    if result["environment_alerts"].get("high_wind", False):
        result["should_alert"] = True
        result["alert_reasons"].append("High wind speed detected")
    
    # Check for unusual odds
    if result["odds_alerts"].get("unusual_handicap", False):
        result["should_alert"] = True
        result["alert_reasons"].append("Unusual handicap value detected")
    
    return result

def generate_alert_message(alert_data: Dict[str, Any]) -> str:
    """
    Generate a formatted alert message based on alert analysis.
    
    Args:
        alert_data: Alert analysis data from analyze_match_for_alerts()
        
    Returns:
        Formatted alert message string
    """
    match_id = alert_data.get("match_id", "Unknown")
    teams = alert_data.get("teams", "Unknown Teams")
    competition = alert_data.get("competition", "Unknown Competition")
    reasons = alert_data.get("alert_reasons", [])
    
    message = f"⚠️ ALERT: Match {match_id}\n"
    message += f"{teams}\n"
    message += f"Competition: {competition}\n\n"
    message += "Issues detected:\n"
    
    for i, reason in enumerate(reasons, 1):
        message += f"{i}. {reason}\n"
    
    message += f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return message

def should_deduplicate_alert(match_id: str, alert_reasons: List[str], 
                            previous_alerts: Dict[str, List[str]]) -> bool:
    """
    Determine if an alert should be deduplicated based on previous alerts.
    
    Args:
        match_id: Match identifier
        alert_reasons: Current alert reasons
        previous_alerts: Dictionary of match_id -> previous alert reasons
        
    Returns:
        True if alert should be skipped (deduplicated), False if it should be sent
    """
    if match_id not in previous_alerts:
        return False
    
    # Check if all current reasons were already alerted
    for reason in alert_reasons:
        if reason not in previous_alerts[match_id]:
            return False
    
    # All reasons were already alerted for this match
    return True

#==========================================
# USAGE EXAMPLE
#==========================================

def example_usage():
    """Example of how to use this module in an alert system"""
    # Sample match data
    match_data = {
        "id": "12345",
        "home_team": "Team A",
        "away_team": "Team B",
        "competition": "League X",
        "country": "Country Y",
        "status_id": "2",
        "minute": "15",
        "timestamp": "2025-05-10 01:45:00",
        "home_score": "1",
        "away_score": "0",
        "home_ht_score": "0",
        "away_ht_score": "0",
        "odds": {
            "ML": [{"time_of_match": "5", "home_win": 150, "draw": 280, "away_win": 130}],
            "SPREAD": [],  # Missing spread odds - potential alert
            "Over/Under": [{"time_of_match": "5", "over": 110, "handicap": "2.5", "under": -130}]
        },
        "weather": "5",  # Sunny
        "temperature": "28",  # 28°C
        "humidity": "45%",
        "wind": "5.2m/s"
    }
    
    # Previous alerts for deduplication
    previous_alerts = {
        "12345": ["Missing SPREAD odds"]
    }
    
    # Analyze match for alerts
    alert_analysis = analyze_match_for_alerts(match_data)
    
    # Check if we should alert (considering deduplication)
    if alert_analysis["should_alert"] and not should_deduplicate_alert(
            match_data["id"], alert_analysis["alert_reasons"], previous_alerts):
        
        # Generate alert message
        alert_message = generate_alert_message(alert_analysis)
        
        # Here you would send the alert
        print("WOULD SEND ALERT:")
        print(alert_message)
        
        # Update previous alerts for deduplication
        if match_data["id"] not in previous_alerts:
            previous_alerts[match_data["id"]] = []
        previous_alerts[match_data["id"]].extend(alert_analysis["alert_reasons"])

if __name__ == "__main__":
    example_usage()
