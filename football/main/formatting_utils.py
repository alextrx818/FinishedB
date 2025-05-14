#!/usr/bin/env python3
"""
formatting_utils.py

Standardized formatting utilities for consistent display of match data across
the sports bot system. Implements the FORMATTING_STANDARDS.md rules.

This module ensures that all match summaries, betting odds displays, and
environment information follow the same visual format throughout the application.

**GLOBAL ALERT FORMATTING STANDARDS**:

1. ALERT PREPENDING RULE:
   - Each alert header must be prepended with alert count information in format: "#X of Y"
   - Count information must be followed by "ALERT TRIGGERED: [ALERT_NAME]" 
   - Timestamp must be included after alert name in format: "@ HH:MM:SS AM/PM MM/DD/YYYY"
   - Only applied AFTER an alert is triggered and confirmed by independent alerters
   - Managed by alerter_main.py in the alert processing flow

2. BETTING ODDS COLUMN ALIGNMENT [CRITICAL]:
   - NEVER modify the column spacing in the betting odds display - it has been perfected
   - Format must follow exactly this pattern with precise spacing:
     │ Home  : +140 │ Draw  : +290 │ Away  : +350 │ (@52')
     │ Home  : +125 │ Hcap  : -0.5 │ Away  : +180 │ (@52')
     │ Over  : +160 │ Line  : 4.5  │ Under : +240 │ (@52')
   - The Line column MUST have exactly two spaces after the value for proper alignment
   - All column labels must have the correct padding to align with "Under" (5 chars)

3. SECTION HEADERS FORMAT:
   - Use the standard section headers exactly as defined in this module
   - Match Summary: "----- MATCH SUMMARY -----"
   - Betting Odds: "--- MATCH BETTING ODDS ---"
   - Environment: "--- MATCH ENVIRONMENT ---"

These standards are GLOBAL for the entire project and must be maintained
across all alerts and displays for consistency and professionalism.
"""

import logging
from datetime import datetime
import time
import os
import json

# Constants
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p EDT"
BOX_VERTICAL = "│"

# Section headers with underlines
MATCH_SUMMARY_HEADER = "----- MATCH SUMMARY -----"
MATCH_SUMMARY_UNDERLINED = MATCH_SUMMARY_HEADER  # Same text for backward compatibility

BETTING_ODDS_HEADER = "--- MATCH BETTING ODDS ---"
BETTING_ODDS_UNDERLINED = BETTING_ODDS_HEADER  # Same text for backward compatibility

ENVIRONMENT_HEADER = "--- MATCH ENVIRONMENT ---"
ENVIRONMENT_UNDERLINED = ENVIRONMENT_HEADER  # Same text for backward compatibility

ALERT_HEADER_WIDTH = 80
ALERT_COUNTER_FILE = "alert_counters.json"

def get_eastern_time():
    """Return current datetime formatted for Eastern time.
    
    This is a simplified approach that doesn't require external timezone packages.
    For production, consider installing 'tzdata' package or using pytz.
    """
    # Using a simplified approach for timestamps
    return datetime.now()

def format_odds_display(odds_display_lines):
    """Format the odds display lines for consistent appearance."""
    if not odds_display_lines:
        return ""
    
    return "\n".join([BETTING_ODDS_HEADER, BETTING_ODDS_UNDERLINED, ""] + odds_display_lines + [""])

def format_moneyline_odds(home, draw, away, minute):
    """
    Format moneyline odds with standardized column alignment.
    
    Args:
        home (str): Home team odds value
        draw (str): Draw odds value
        away (str): Away team odds value
        minute (str): Match minute when odds were recorded
        
    Returns:
        Formatted string with properly aligned columns
    """
    # Convert odds values to standardized +/- format
    home_str = f"{int(float(home) * 100):+d}" if home else "+0"
    draw_str = f"{int(float(draw) * 100):+d}" if draw else "+0"
    away_str = f"{int(float(away) * 100):+d}" if away else "+0"
    
    # Note the extra space for padding 4-character labels to match "Under"
    return f"{BOX_VERTICAL} Home  : {home_str} {BOX_VERTICAL} Draw  : {draw_str} {BOX_VERTICAL} Away  : {away_str} {BOX_VERTICAL} (@{minute}')"

def format_handicap_odds(home, handicap, away, minute):
    """
    Format handicap/spread odds with standardized column alignment.
    
    Args:
        home (str): Home team odds value
        handicap (str): Handicap value
        away (str): Away team odds value
        minute (str): Match minute when odds were recorded
        
    Returns:
        Formatted string with properly aligned columns
    """
    # Convert odds values to standardized formats
    home_str = f"{int(float(home) * 100):+d}" if home else "+0"
    handicap_str = f"{float(handicap):.1f}" if handicap else "0.0"
    away_str = f"{int(float(away) * 100):+d}" if away else "+0"
    
    # Note the extra space for padding 4-character labels to match "Under"
    return f"{BOX_VERTICAL} Home  : {home_str} {BOX_VERTICAL} Hcap  : {handicap_str} {BOX_VERTICAL} Away  : {away_str} {BOX_VERTICAL} (@{minute}')"

def format_overunder_odds(over, line, under, minute):
    """
    Format over/under odds with standardized column alignment.
    
    Args:
        over (str): Over odds value
        line (str): Line value
        under (str): Under odds value
        minute (str): Match minute when odds were recorded
        
    Returns:
        Formatted string with properly aligned columns
    """
    # Convert odds values to standardized formats
    over_str = f"{int(float(over) * 100):+d}" if over else "+0"
    line_str = f"{float(line):.1f}" if line else "0.0"
    under_str = f"{int(float(under) * 100):+d}" if under else "+0"
    
    # Add exactly TWO spaces after line_str to ensure alignment with Under column
    # This is the critical spacing for perfect column alignment
    
    # Note the extra space for padding 4-character labels to match "Under"
    return f"{BOX_VERTICAL} Over  : {over_str} {BOX_VERTICAL} Line  : {line_str}  {BOX_VERTICAL} Under : {under_str} {BOX_VERTICAL} (@{minute}')"


def format_environment_data(env_data):
    """
    Format environment data with standardized display.
    
    Args:
        env_data (dict): Environment data dictionary
        
    Returns:
        List of formatted strings for environment display
    """
    if not env_data:
        return []
        
    lines = [ENVIRONMENT_HEADER, ENVIRONMENT_UNDERLINE, ""]
    
    # Format temperature (convert to Fahrenheit if needed)
    temp = env_data.get("temperature", "")
    if temp and "°C" in temp:
        # Convert Celsius to Fahrenheit
        try:
            celsius = float(temp.replace("°C", ""))
            fahrenheit = (celsius * 9/5) + 32
            temp = f"{fahrenheit:.1f}°F"
        except (ValueError, TypeError):
            temp = "N/A"
    lines.append(f"Temperature: {temp}")
    
    # Format humidity
    humidity = env_data.get("humidity", "")
    lines.append(f"Humidity: {humidity}")
    
    # Format wind
    wind = env_data.get("wind", "")
    if wind and "m/s" in wind:
        # Convert m/s to mph
        try:
            ms = float(wind.replace("m/s", ""))
            mph = ms * 2.237
            wind = f"{mph:.1f} mph"
        except (ValueError, TypeError):
            wind = "N/A"
    lines.append(f"Wind: {wind}")
    
    return lines

def setup_alert_logger(alert_name):
    """
    Set up a standardized logger for alerts.
    
    Args:
        alert_name (str): Base name of the alert file (without extension)
        
    Returns:
        Configured logger instance
    """
    # Configure logger with standardized format
    logger = logging.getLogger(alert_name)
    logger.setLevel(logging.INFO)
    
    # Check if handlers already exist
    if not logger.handlers:
        # Create logger file path
        import os
        alerts_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.basename(alerts_dir) == "Alerts":
            alerts_dir = os.path.join(alerts_dir, "Alerts")
        log_file = os.path.join(alerts_dir, f"{alert_name}.logger")
        
        # Create file handler with standard format
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(file_handler)
        
        print(f"Created alert logger: {log_file}")
    
    return logger

def get_alert_count(alert_name):
    """
    Get and update the alert count for the day.
    
    Args:
        alert_name (str): Name of the alert
        
    Returns:
        tuple: (current_alert_number, total_alerts_today)
    """
    # Get current date as string
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Initialize counters if they don't exist
    alerts_dir = os.path.dirname(os.path.abspath(__file__))
    if "Alerts" not in alerts_dir:
        alerts_dir = os.path.join(alerts_dir, "Alerts")
        
    counter_file = os.path.join(alerts_dir, ALERT_COUNTER_FILE)
    
    # Load existing counters or initialize
    counters = {}
    if os.path.exists(counter_file):
        try:
            with open(counter_file, 'r') as f:
                counters = json.load(f)
        except Exception:
            # If file is corrupted, start fresh
            counters = {}
    
    # Initialize for today if needed
    if today not in counters:
        counters[today] = {}
    
    # Initialize for this alert if needed
    if alert_name not in counters[today]:
        counters[today][alert_name] = 0
    
    # Get total alerts for today across all alert types
    total_today = sum(counters[today].values()) + 1  # Add 1 for current alert
    
    # Increment counter for this specific alert
    counters[today][alert_name] += 1
    current_alert = counters[today][alert_name]
    
    # Save updated counters
    try:
        with open(counter_file, 'w') as f:
            json.dump(counters, f)
    except Exception:
        # If we can't save, just continue without error
        pass
        
    return (current_alert, total_today)

def format_alert_block(alert_name, match_id, notice, match_summary_lines, alert_num, total_alerts, timestamp):
    """
    Format an alert block with properly formatted match summary.
    No I/O operations - pure formatting function.
    
    Args:
        alert_name (str): Name of the alert
        match_id (str): Match identifier
        notice (str): Alert notification message
        match_summary_lines (list): Formatted match summary lines
        alert_num (int): Current alert number
        total_alerts (int): Total alerts for the day
        timestamp (str): Formatted timestamp string
        
    Returns:
        list: Formatted lines for the alert block
    """
    formatted_lines = []
    
    # Add notice line
    formatted_lines.append(f"Alert triggered for match {match_id}: {notice}")
    
    # Add blank line
    formatted_lines.append("")
    
    # Add header with numbering system
    formatted_lines.append("=" * ALERT_HEADER_WIDTH)
    formatted_lines.append(f"#{alert_num} of {total_alerts} ALERT TRIGGERED: {alert_name.upper()} @ {timestamp}")
    formatted_lines.append("=" * ALERT_HEADER_WIDTH)
    
    # Add blank line
    formatted_lines.append("")
    
    # Add each line of the match summary
    formatted_lines.extend(match_summary_lines)
    
    # Add final line
    formatted_lines.append("Alert processing complete")
    
    return formatted_lines


# Usage examples (for documentation):
if __name__ == "__main__":
    # Example of formatting betting odds
    ml_odds = format_moneyline_odds("1.95", "3.50", "4.00", "4")
    hc_odds = format_handicap_odds("1.80", "-1.0", "2.10", "4")
    ou_odds = format_overunder_odds("1.90", "3.5", "2.00", "4")
    
    odds_lines = [ml_odds, hc_odds, ou_odds]
    formatted_odds = format_odds_display(odds_lines)
    
    print("BETTING ODDS DISPLAY EXAMPLE:")
    print(formatted_odds)
    
    # Example of setting up and using alert logger
    test_logger = setup_alert_logger("TEST")
    
    # Simple example match summary
    summary = [
        "",
        MATCH_SUMMARY_HEADER,
        f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}",
        "Match ID: TEST-123",
        "Competition: English Premier League (England)",
        "Match: Manchester United vs Liverpool FC",
        "Score: 2 - 1 (HT: 1 - 0)",
        "Status: In Progress (45')",
        "",
    ] + odds_lines + [""]
    
    # Log with proper formatting
    log_alert_with_match_summary(test_logger, "TEST-123", "Test alert message", summary)
    
    print("Test logger example created at: Alerts/TEST.logger")
