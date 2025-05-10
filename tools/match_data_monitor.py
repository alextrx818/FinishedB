#!/usr/bin/env python3
"""
Match Data Monitor

This script monitors the main.logger file for missing match data and sends
Telegram alerts when issues are detected. It runs independently and doesn't 
require modifications to live.py.

Usage:
    python3 match_data_monitor.py
"""

import os
import sys
import time
import re
from datetime import datetime
import pytz

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

# Import Telegram notification function
try:
    from football.telegram import send_match_alert
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Telegram import failed: {e}")
    print("⚠️ Running without Telegram notification capability")
    TELEGRAM_AVAILABLE = False

# Configure paths
LOGGER_PATH = os.path.join(project_root, 'football', 'logger', 'main.logger')

# Patterns to detect in logs
PATTERNS = {
    'match_start': r'==================================================\n(MATCH #\d+ OF \d+)',
    'match_id': r'Match ID: ([a-zA-Z0-9]+)',
    'teams': r'Match: (.+?)\n',
    'competition': r'Competition: (.+?) \(',
    'empty_env': r'--- MATCH ENVIRONMENT ---\nNo environment data available for this match',
    'empty_ml': r'ML \(Money Line\):\nNo money line odds available for this match',
    'empty_spread': r'SPREAD \(Asia Handicap\):\nNo handicap odds available for this match',
    'empty_total': r'Over/Under:\nNo over/under odds available for this match',
}

# Track already alerted matches to avoid duplicates
alerted_matches = set()
# Track position in file
file_position = 0

def get_eastern_time():
    """Get current time in Eastern timezone"""
    utc_now = datetime.now(pytz.utc)
    eastern = pytz.timezone('America/New_York')
    eastern_time = utc_now.astimezone(eastern)
    return eastern_time.strftime("%m/%d/%Y %I:%M:%S %p ET")

def send_alert(alert_type, match_id, teams, competition):
    """Send a Telegram alert for missing match data"""
    if not TELEGRAM_AVAILABLE or match_id in alerted_matches:
        return
    
    # Add match to alerted set to avoid duplicates
    alerted_matches.add(match_id)
    
    # Determine alert message based on type
    if alert_type == 'environment':
        message = f"Missing environment data"
    elif alert_type == 'ml_odds':
        message = f"Missing money line odds"
    elif alert_type == 'spread_odds':
        message = f"Missing handicap/spread odds"
    elif alert_type == 'total_odds':
        message = f"Missing over/under odds"
    else:
        message = f"Missing data detected"
    
    # Send the alert
    try:
        send_match_alert(
            message,
            match_id=match_id,
            teams=teams,
            competition=competition,
            alert_type="odds" if "odds" in alert_type else "weather"
        )
        print(f"Alert sent: {message} for {teams}")
    except Exception as e:
        print(f"Error sending alert: {e}")

def process_log_chunk(chunk):
    """Process a chunk of log data to detect missing match data"""
    # Extract match information
    match_id = None
    teams = None
    competition = None
    
    # Try to extract match details
    match_id_match = re.search(PATTERNS['match_id'], chunk)
    if match_id_match:
        match_id = match_id_match.group(1)
    
    teams_match = re.search(PATTERNS['teams'], chunk)
    if teams_match:
        teams = teams_match.group(1)
    
    comp_match = re.search(PATTERNS['competition'], chunk)
    if comp_match:
        competition = comp_match.group(1)
    
    # Only proceed if we have match identification
    if match_id and teams:
        # Check for missing environment data
        if re.search(PATTERNS['empty_env'], chunk):
            send_alert('environment', match_id, teams, competition)
        
        # Check for missing odds data
        if re.search(PATTERNS['empty_ml'], chunk):
            send_alert('ml_odds', match_id, teams, competition)
            
        if re.search(PATTERNS['empty_spread'], chunk):
            send_alert('spread_odds', match_id, teams, competition)
            
        if re.search(PATTERNS['empty_total'], chunk):
            send_alert('total_odds', match_id, teams, competition)

def monitor_log_file():
    """Monitor the log file for new data and process it"""
    global file_position
    
    try:
        # If file doesn't exist yet, wait for it
        if not os.path.exists(LOGGER_PATH):
            print(f"Waiting for log file to be created at {LOGGER_PATH}...")
            return
        
        with open(LOGGER_PATH, 'r', encoding='utf-8') as f:
            # Move to the last processed position
            f.seek(file_position)
            
            # Read new content
            new_content = f.read()
            if new_content:
                # Update position for next read
                file_position = f.tell()
                
                # Split into match chunks
                match_sections = re.split(PATTERNS['match_start'], new_content)
                
                # Process each match section
                for i in range(1, len(match_sections), 2):
                    if i < len(match_sections) - 1:
                        match_num = match_sections[i]
                        match_data = match_sections[i+1]
                        process_log_chunk(f"MATCH {match_num}\n{match_data}")
    
    except Exception as e:
        print(f"Error monitoring log file: {e}")

def main():
    """Main function to run the monitor"""
    print(f"Starting match data monitor at {get_eastern_time()}")
    print(f"Monitoring log file: {LOGGER_PATH}")
    
    # Run continuously
    try:
        while True:
            monitor_log_file()
            time.sleep(5)  # Check every 5 seconds
    except KeyboardInterrupt:
        print("Monitor stopped by user")
    except Exception as e:
        print(f"Monitor failed: {e}")

if __name__ == "__main__":
    main()
