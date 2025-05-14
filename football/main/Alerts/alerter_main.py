# alerter_main.py

import os
import json
import requests
import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo
from pure_json_fetch_cache import fetch_and_cache
from merge_logic import merge_all
from OU3 import OverUnderAlert

# Import specific formatting functions from combined_match_summary
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from combined_match_summary import (
    get_eastern_time, 
    format_odds_display, 
    summarize_environment,
    get_status_description,
    transform_odds,
    API_DATETIME_FORMAT
)

# Configure root logger for console output
root_logger = logging.getLogger()
if not root_logger.handlers:
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    root_logger.addHandler(console)
    root_logger.setLevel(logging.INFO)

# Telegram configuration with hardcoded credentials from telegram_config.py
TELEGRAM_TOKEN = "7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko"
CHAT_ID = "6128359776"
TELEGRAM_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"


def send_notification(message: str):
    """Send a Telegram notification."""
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(TELEGRAM_URL, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to send notification: {e}")


def format_match_summary(match):
    """Format match data exactly like combined_match_summary.py does.
    This is a direct duplicate of the formatting code from combined_match_summary.py
    to ensure consistent pretty-printing throughout the system.
    
    Args:
        match: The enriched match object from merge_logic
        
    Returns:
        List of formatted strings representing the match summary
    """
    lines = []
    
    # Headers and basic info
    lines.append("\n----- MATCH SUMMARY -----")
    lines.append("-------------------------")
    lines.append("")
    lines.append(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
    
    # Try both ID formats
    match_id = match.get('id') or match.get('match_id', 'Unknown')
    lines.append(f"Match ID: {match_id}")
    
    # Competition info - handle both string format and object format
    competition = match.get('competition', {})
    comp_id = None
    comp_name = None
    comp_country = None
    
    if isinstance(competition, str):
        # Direct string format
        comp_name = competition
        comp_id = match.get('competition_id', 'Unknown')
        comp_country = match.get('country', 'Unknown Country')
    elif isinstance(competition, dict):
        # Object format
        comp_id = competition.get('id')
        comp_name = competition.get('name')
        comp_country = competition.get('country')
    else:
        # Alternative key formats
        comp_id = match.get('competition_id')
        comp_name = match.get('competition_name')
        comp_country = match.get('country') or match.get('competition_country')
    
    # Apply defaults if still missing
    comp_id = comp_id or 'Unknown'
    comp_name = comp_name or 'Unknown'
    comp_country = comp_country or 'Unknown Country'
    
    lines.append(f"Competition ID: {comp_id}")
    lines.append(f"Competition: {comp_name} ({comp_country})")
    
    # Team names with fallbacks for different structures
    home_team = None
    away_team = None
    
    # String access
    home_team = match.get('home_team')
    away_team = match.get('away_team')
    
    # Object structure access
    if not isinstance(home_team, str) and match.get('home_team', {}).get('name'):
        home_team = match.get('home_team', {}).get('name')
    if not isinstance(away_team, str) and match.get('away_team', {}).get('name'):
        away_team = match.get('away_team', {}).get('name')
    
    # Alternate keys
    home_team = home_team or match.get('home', 'Unknown')
    away_team = away_team or match.get('away', 'Unknown')
    
    lines.append(f"Match: {home_team} vs {away_team}")
    
    # Score handling for both object and array structures
    home_live = 0
    home_ht = 0
    away_live = 0
    away_ht = 0
    
    # Object structure
    score = match.get('score', {})
    if isinstance(score, dict):
        home_live = score.get('home', 0) 
        away_live = score.get('away', 0)
        home_ht = score.get('home_ht', 0)
        away_ht = score.get('away_ht', 0)
    # Array structure (from original data source)
    elif isinstance(score, list) and len(score) > 3:
        hs, as_ = score[2], score[3]
        if isinstance(hs, list) and len(hs) > 1:
            home_live, home_ht = hs[0], hs[1]
        if isinstance(as_, list) and len(as_) > 1:
            away_live, away_ht = as_[0], as_[1]
    
    lines.append(f"Score: {home_live} - {away_live} (HT: {home_ht} - {away_ht})")
    
    # Status with rich description
    status_id = match.get('status_id')
    status = match.get('status', get_status_description(status_id))
    lines.append(f"Status: {status} (Status ID: {status_id})")
    
    # Betting Odds section
    lines.append("\n--- MATCH BETTING ODDS ---")
    lines.append("--------------------------")
    lines.append("")
    odds_data = match.get('odds', {})
    
    # Handle both market array and object structures
    ml_market = None
    spread_market = None
    ou_market = None
    minute = "4"
    
    # Extract markets by type
    markets = odds_data.get('markets', [])
    if markets:
        for market in markets:
            market_type = market.get('type')
            if market_type == 'MONEYLINE':
                ml_market = market
            elif market_type == 'SPREAD':
                spread_market = market
            elif market_type == 'OVER_UNDER':
                ou_market = market
                
        # Format exactly as in example
        odds_lines = []
        
        # Moneyline odds
        if ml_market:
            home = ml_market.get('home', 0)
            draw = ml_market.get('draw', 0)
            away = ml_market.get('away', 0)
            
            # Format to match +130 style
            home_str = f"{int(float(home) * 100):+d}" if home else "+0"
            draw_str = f"{int(float(draw) * 100):+d}" if draw else "+0"
            away_str = f"{int(float(away) * 100):+d}" if away else "+0"
            
            ml_line = f"│ Home  : {home_str} │ Draw  : {draw_str} │ Away  : {away_str} │ (@{minute}')"
            odds_lines.append(ml_line)
        
        # Spread odds
        if spread_market:
            home = spread_market.get('home', 0)
            handicap = spread_market.get('handicap', 0)
            away = spread_market.get('away', 0)
            
            # Format to match -133 style
            home_str = f"{int(float(home) * 100):+d}" if home else "+0"
            handicap_str = f"{float(handicap):.1f}" if handicap else "0.0"
            away_str = f"{int(float(away) * 100):+d}" if away else "+0"
            
            spread_line = f"│ Home  : {home_str} │ Hcap  : {handicap_str} │ Away  : {away_str} │ (@{minute}')"
            odds_lines.append(spread_line)
        
        # Over/Under odds
        if ou_market:
            over = ou_market.get('over', 0)
            line = ou_market.get('line', 0)
            under = ou_market.get('under', 0)
            
            # Format to match -111 style
            over_str = f"{int(float(over) * 100):+d}" if over else "+0"
            line_str = f"{float(line):.1f}" if line else "0.0"
            under_str = f"{int(float(under) * 100):+d}" if under else "+0"
            
            ou_line = f"│ Over  : {over_str} │ Line  : {line_str} │ Under : {under_str} │ (@{minute}')"
            odds_lines.append(ou_line)
            
        # Add all odds lines
        if odds_lines:
            lines.extend(odds_lines)
        else:
            lines.append("No betting odds available")
    else:
        # Try format_odds_display as fallback for any other odds format
        formatted_odds = {
            "ML": transform_odds(odds_data.get("eu", []), "eu"),
            "SPREAD": transform_odds(odds_data.get("asia", []), "asia"),
            "Over/Under": transform_odds(odds_data.get("bs", []), "bs")
        }
        odds_display = format_odds_display(formatted_odds)
        lines.append(odds_display)
    
    # Environment data
    lines.append("\n--- MATCH ENVIRONMENT ---")
    lines.append("-------------------------")
    lines.append("")
    env_data = match.get('environment', {})
    
    # Format environment exactly as in the example
    if isinstance(env_data, dict):
        weather = env_data.get('weather', {})
        if isinstance(weather, dict):
            # Temperature
            if 'temperature' in weather:
                try:
                    temp_c = float(weather['temperature'])
                    temp_f = temp_c * 9/5 + 32
                    lines.append(f"Temperature: {temp_f:.1f}°F")
                except (ValueError, TypeError):
                    pass
            
            # Humidity
            if 'humidity' in weather:
                try:
                    humidity = int(weather['humidity'])
                    lines.append(f"Humidity: {humidity}%")
                except (ValueError, TypeError):
                    pass
            
            # Wind
            if 'wind_speed' in weather:
                try:
                    wind = float(weather['wind_speed'])
                    lines.append(f"Wind: {wind:.1f} mph")
                except (ValueError, TypeError):
                    pass
        else:
            # Fallback to summarize_environment if needed
            env_lines = summarize_environment(env_data)
            lines.extend(env_lines)
    
    return lines


class FutureAlert:
    """Placeholder for future alert logic."""
    def check(self, match: dict) -> str | None:
        # TODO: implement when needed
        return None


class AlerterMain:
    """Orchestrates satellite alerts, manages per-alert state, logging, and dispatches notifications without duplicates."""
    def __init__(self, alerts=None):
        self.alerts = alerts or []
        self.seen_ids = {}
        # Create Alerts directory path for logs and state files
        self.alerts_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Store file_base mappings for alerts
        self.alert_file_bases = {}
        
        # Initialize per-alert logger and seen-ID storage
        for alert in self.alerts:
            # Determine appropriate alert name for logging and state files
            # Import path may contain slashes, get just the filename
            module_name = alert.__class__.__name__
            # Find the actual .py file that contains this class
            py_file = None
            for file in os.listdir(self.alerts_dir):
                if file.endswith('.py') and not file.startswith('__'):
                    # Check if the class is in this file
                    file_path = os.path.join(self.alerts_dir, file)
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if f'class {module_name}' in content:
                            py_file = file
                            break
            
            # Use the Python filename for logs (without .py extension)
            if py_file:
                file_base = os.path.splitext(py_file)[0]
            else:
                # Fallback to class name if file not found
                file_base = module_name
                
            # Store the file_base mapping for this alert
            self.alert_file_bases[id(alert)] = file_base
                
            # Setup logger using actual file name
            logger = logging.getLogger(file_base)
            if not logger.handlers:
                logger.setLevel(logging.INFO)
                # Save log files inside the Alerts folder with file name
                log_path = os.path.join(self.alerts_dir, f"{file_base}.logger")
                handler = logging.FileHandler(log_path)
                handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
                logger.addHandler(handler)
            # Use same file_base for seen IDs storage
            # Load seen IDs from disk - stored in Alerts directory with file base name
            seen_file = os.path.join(self.alerts_dir, f"{file_base}.seen.json")
            if os.path.exists(seen_file):
                try:
                    with open(seen_file, 'r') as f:
                        ids = json.load(f)
                    self.seen_ids[file_base] = set(ids)
                except Exception:
                    self.seen_ids[file_base] = set()
            else:
                self.seen_ids[file_base] = set()

    def _save_seen(self, file_base: str):
        """Persist seen IDs for an alert to disk."""
        # Store seen files in the Alerts directory with file base name
        seen_file = os.path.join(self.alerts_dir, f"{file_base}.seen.json")
        try:
            with open(seen_file, 'w') as f:
                json.dump(list(self.seen_ids[file_base]), f)
        except Exception as e:
            print(f"Failed to save seen IDs for {file_base}: {e}")

    def run(self):
        # 1. Fetch raw JSON data
        raw_data = fetch_and_cache()
        # 2. Merge into enriched match objects
        merged_matches = merge_all(raw_data)

        # 3. Check alerts, avoid duplicates, notify, and log
        for match in merged_matches:
            match_id = match.get("match_id")
            for alert in self.alerts:
                # Use module name for consistency
                module_name = alert.__class__.__module__.split('.')[-1]
                notice = alert.check(match)
                # Only proceed if alert triggers and not already seen
                if notice and match_id and match_id not in self.seen_ids[self.alert_file_bases[id(alert)]]:
                    # Send alert to Telegram
                    send_notification(notice)
                    # Generate pretty match summary for console display
                    print("\n" + "=" * 80)
                    print(f"ALERT TRIGGERED: {self.alert_file_bases[id(alert)]}")
                    print("=" * 80)
                    
                    # Format match data using the exact formatting from combined_match_summary.py
                    summary_lines = format_match_summary(match)
                    for line in summary_lines:
                        print(line)
                        
                    # Save home_team, away_team, and status for logger entry
                    home_team = match.get('home_team', {}).get('name', match.get('home', 'Unknown'))
                    away_team = match.get('away_team', {}).get('name', match.get('away', 'Unknown'))
                    score = match.get('score', {})
                    home_score = score.get('home', 0)
                    away_score = score.get('away', 0)
                    status_id = match.get('status_id')
                    status = match.get('status', get_status_description(status_id))
                    
                    # Import the format_alert_block function from formatting_utils for clean formatting
                    from formatting_utils import format_alert_block, get_alert_count
                    
                    # Get alert-specific information
                    file_base_id = self.alert_file_bases[id(alert)]
                    alert_logger = logging.getLogger(file_base_id)
                    
                    # Get alert count and timestamp
                    alert_num, total_alerts = get_alert_count(file_base_id)
                    timestamp = datetime.now().strftime("%I:%M:%S %p %m/%d/%Y")
                    
                    # Format the alert block using pure formatting function
                    formatted_lines = format_alert_block(
                        file_base_id, match_id, notice, summary_lines,
                        alert_num, total_alerts, timestamp
                    )
                    
                    # Get the log file path from the logger's file handler
                    log_file_path = None
                    for handler in alert_logger.handlers:
                        if isinstance(handler, logging.FileHandler):
                            log_file_path = handler.baseFilename
                            break
                    
                    if log_file_path and os.path.exists(log_file_path):
                        # Read existing content
                        try:
                            with open(log_file_path, 'r') as f:
                                existing_content = f.read()
                        except Exception as e:
                            print(f"Error reading existing log file: {e}")
                            existing_content = ""
                        
                        # Write new content followed by existing content (head-insertion)
                        try:
                            with open(log_file_path, 'w') as f:
                                f.write("\n".join(formatted_lines))
                                f.write("\n\n")
                                f.write(existing_content)
                            print(f"Successfully prepended alert to {log_file_path}")
                        except Exception as e:
                            print(f"Error writing to log file: {e}")
                            # Fallback to standard logging if file operations fail
                            for line in formatted_lines:
                                alert_logger.info(line)
                    else:
                        # Fallback to standard logging if we can't access the file
                        print(f"Warning: Cannot access log file, falling back to standard logging.")
                        for line in formatted_lines:
                            alert_logger.info(line)
                    # Mark as seen and persist
                    self.seen_ids[file_base_id].add(match_id)
                    self._save_seen(file_base_id)


if __name__ == "__main__":
    # Register satellite alerts here
    alerts = [
        OverUnderAlert(threshold=3.0),  # O/U ≥ 3.00
        FutureAlert(),                  # Future alert stub
    ]
    manager = AlerterMain(alerts=alerts)
    manager.run()