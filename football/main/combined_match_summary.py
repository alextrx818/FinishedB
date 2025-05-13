# combined_match_summary.py

import json
from datetime import datetime
from zoneinfo import ZoneInfo
import functools

# Implement conversion functions directly instead of importing from live.py
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

API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p %Z"

def get_eastern_time():
    return datetime.now(ZoneInfo("America/New_York"))

def format_american_odds(raw_value, market):
    """Format American odds with consistent sign display, using appropriate conversion."""
    try:
        if market in ("SPREAD", "Over/Under"):
            amd = hk_to_american(raw_value)
        else:
            amd = decimal_to_american(raw_value)
        return f"{amd:+d}"
    except Exception:
        return "+0"

@functools.lru_cache(maxsize=32)
def get_status_description(status_id):
    status_mapping = {
        "1": "Not started", "2": "First half", "3": "Half-time break",
        "4": "Second half", "5": "Extra time", "6": "Penalty shootout",
        "7": "Finished", "8": "Finished", "9": "Postponed",
        "10": "Canceled", "11": "To be announced", "12": "Interrupted",
        "13": "Abandoned", "14": "Suspended"
    }
    return status_mapping.get(str(status_id), f"Unknown (ID: {status_id})")

def pick_best_entry(entries):
    """Select the best entry from available odds, preferring minutes 4-6"""
    if not entries:
        return {}
        
    # Sort entries by time (numeric values first, then non-numeric)
    entries.sort(key=lambda e: int(e["time_of_match"]) if e.get("time_of_match","").isdigit() else 1000)
    
    # Target minutes are 4, 5, and 6
    target_minutes = ["4", "5", "6"]
    
    # First try to find an entry within target minutes
    best_entry = next((e for e in entries if e.get("time_of_match", "") in target_minutes), None)
    
    # If no entry found in target minutes, use the first available entry
    if not best_entry and entries:
        best_entry = entries[0]
        
    return best_entry or {}

def format_odds_display(formatted_odds):
    """Format the odds for display."""
    if not formatted_odds:
        return "No odds data available"
    
    output = []
    for market in ("ML", "SPREAD", "Over/Under"):
        entries = formatted_odds.get(market, [])
        if not entries: 
            continue

        # Pick the best entry (preferring minutes 4-6)
        entry = pick_best_entry(entries)
        if not entry:
            continue
            
        # Format based on market type
        if market == "ML":
            hw = format_american_odds(entry.get("home_win", 0), market)
            dr = format_american_odds(entry.get("draw", 0), market)
            aw = format_american_odds(entry.get("away_win", 0), market)
            output.append(f"ML → Home {hw}, Draw {dr}, Away {aw}")
        elif market == "SPREAD":
            h = format_american_odds(entry.get("home_win", 0), market)
            a = format_american_odds(entry.get("away_win", 0), market)
            output.append(f"SPREAD → Home {h}, Hcap {entry.get('handicap', 0)}, Away {a}")
        else:  # Over/Under
            o = format_american_odds(entry.get("over", 0), market)
            u = format_american_odds(entry.get("under", 0), market)
            output.append(f"OU → Over {o}, Line {entry.get('handicap', 0)}, Under {u}")
    
    return "\n".join(output) or "No odds data available"

def transform_odds(raw_odds):
    """
    Transform raw odds data from the merged format to the format expected by the formatter
    
    Raw format: List of arrays with numeric/timestamp values
    Expected: List of dictionaries with named keys
    """
    if not raw_odds or not isinstance(raw_odds, list):
        return []
        
    transformed = []
    for odds_entry in raw_odds:
        if not isinstance(odds_entry, list) or len(odds_entry) < 5:
            continue
            
        # Standard format for all odds types
        entry = {
            "time_of_match": str(odds_entry[1]) if len(odds_entry) > 1 else "0",
        }
        
        # Add type-specific fields based on which odds type this is
        if len(odds_entry) >= 7:  # asia/SPREAD
            entry["home_win"] = odds_entry[2] if len(odds_entry) > 2 else 0
            entry["handicap"] = odds_entry[3] if len(odds_entry) > 3 else 0
            entry["away_win"] = odds_entry[4] if len(odds_entry) > 4 else 0
        elif len(odds_entry) >= 5:  # eu/ML
            entry["home_win"] = odds_entry[2] if len(odds_entry) > 2 else 0
            entry["draw"] = odds_entry[3] if len(odds_entry) > 3 else 0
            entry["away_win"] = odds_entry[4] if len(odds_entry) > 4 else 0
        elif len(odds_entry) >= 5:  # bs/Over/Under
            entry["over"] = odds_entry[2] if len(odds_entry) > 2 else 0
            entry["handicap"] = odds_entry[3] if len(odds_entry) > 3 else 0
            entry["under"] = odds_entry[4] if len(odds_entry) > 4 else 0
            
        transformed.append(entry)
        
    return transformed

def summarize_environment(env):
    weather_map = {1: "Clear", 2: "Cloudy"}
    lines = []
    w = weather_map.get(env.get("weather"))
    if w: lines.append(f"Weather: {w}")
    temp = env.get("temperature")
    if temp and temp.endswith("°C"):
        c = int(temp.rstrip("°C"))
        lines.append(f"Temperature: {c * 9/5 + 32:.1f}°F")
    if env.get("humidity"):
        lines.append(f"Humidity: {env['humidity']}")
    wind = env.get("wind")
    if wind and wind.endswith("m/s"):
        ms = float(wind.rstrip("m/s"))
        lines.append(f"Wind: {ms * 2.237:.1f} mph")
    return lines or ["No environment data available"]

if __name__ == "__main__":
    # Get the path to the merged output file
    from pathlib import Path
    BASE_DIR = Path(__file__).parent
    MERGE_OUTPUT_FILE = BASE_DIR / "merge_logic.json"
    
    # Load merged match data
    with open(MERGE_OUTPUT_FILE) as f:
        matches = json.load(f)
    
    for match in matches:
        print("\n----- MATCH SUMMARY -----")
        print(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
        print(f"Match ID: {match.get('id')}")
        print(f"Competition ID: {match.get('competition_id')}")
        print(f"Competition: {match.get('competition')} ({match.get('country')})")
        print(f"Match: {match.get('home_team')} vs {match.get('away_team')}")
        
        # Score extraction
        home_live = home_ht = away_live = away_ht = 0
        sd = match.get("score", [])
        if isinstance(sd, list) and len(sd) > 3:
            hs, as_ = sd[2], sd[3]
            if isinstance(hs, list) and len(hs) > 1:
                home_live, home_ht = hs[0], hs[1]
            if isinstance(as_, list) and len(as_) > 1:
                away_live, away_ht = as_[0], as_[1]
        print(f"Score: {home_live} - {away_live} (HT: {home_ht} - {away_ht})")
        
        # Status
        sid = match.get("status_id")
        print(f"Status: {get_status_description(sid)} (Status ID: {sid})")
        
        # Betting Odds
        print("\n--- MATCH BETTING ODDS ---")
        
        # Transform the odds data structure to match our formatter's expectations
        odds_data = match.get("odds", {})
        formatted_odds = {
            "ML": transform_odds(odds_data.get("eu", [])),
            "SPREAD": transform_odds(odds_data.get("asia", [])),
            "Over/Under": transform_odds(odds_data.get("bs", []))
        }
        
        print(format_odds_display(formatted_odds))
        
        # Environment
        print("\n--- MATCH ENVIRONMENT ---")
        for line in summarize_environment(match.get("environment", {})):
            print(line)
