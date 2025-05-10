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
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

# Import Telegram notification function
# Use absolute import path when dynamically loaded
from football.telegram.alerts import send_match_alert
TELEGRAM_AVAILABLE = True

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

# Track already alerted match conditions to avoid duplicates
# Format: (match_id, alert_type)
alerted_conditions = set()
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
    if not TELEGRAM_AVAILABLE:
        return
        
    # Create a unique key for this condition (match_id + alert_type)
    condition_key = (match_id, alert_type)
    
    # Check if this specific condition has already been alerted
    if condition_key in alerted_conditions:
        print(f"Skipping duplicate alert: {alert_type} for match {match_id}")
        return
    
    # Add this condition to the alerted set to avoid duplicates
    alerted_conditions.add(condition_key)
    
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
        print(f"Found match ID: {match_id}")
    else:
        print("No match ID found in chunk")
    
    teams_match = re.search(PATTERNS['teams'], chunk)
    if teams_match:
        teams = teams_match.group(1)
        print(f"Found teams: {teams}")
    
    comp_match = re.search(PATTERNS['competition'], chunk)
    if comp_match:
        competition = comp_match.group(1)
        print(f"Found competition: {competition}")
    
    # Only proceed if we have match identification
    if match_id and teams:
        print(f"Processing alerts for match {match_id} - {teams}")
        
        # Look for environment data section
        env_section = re.search(r'--- MATCH ENVIRONMENT ---(.+?)(?:---|$)', chunk, re.DOTALL)
        if env_section:
            env_text = env_section.group(1).strip()
            print(f"Environment section: '{env_text[:50]}...'")
            
            # Check for missing environment data
            if "No environment data available for this match" in env_text:
                print(f"DETECTED: Missing environment data for {match_id}")
                send_alert('environment', match_id, teams, competition)
            else:
                print(f"Environment data present for {match_id}")
        else:
            print(f"No environment section found for {match_id}")
        
        # Check for missing odds data
        if re.search(PATTERNS['empty_ml'], chunk):
            print(f"DETECTED: Missing money line odds for {match_id}")
            send_alert('ml_odds', match_id, teams, competition)
            
        if re.search(PATTERNS['empty_spread'], chunk):
            print(f"DETECTED: Missing spread odds for {match_id}")
            send_alert('spread_odds', match_id, teams, competition)
            
        if re.search(PATTERNS['empty_total'], chunk):
            print(f"DETECTED: Missing total odds for {match_id}")
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
                print(f"Read {len(new_content)} bytes from log file")
                
                # Find all matches in the content
                match_markers = re.findall(r'==+\n(MATCH #\d+ OF \d+)', new_content)
                print(f"Found {len(match_markers)} match markers in log")
                
                # Split into match chunks
                match_sections = re.split(r'==+\n(?:MATCH #\d+ OF \d+)', new_content)
                print(f"Split into {len(match_sections)} sections")
                
                # Skip the first section (before any match)
                if len(match_sections) > 1:
                    # Process each match section
                    for i in range(1, len(match_sections)):
                        # Get the corresponding match marker
                        marker_idx = i-1
                        if marker_idx < len(match_markers):
                            match_marker = match_markers[marker_idx]
                            print(f"Processing {match_marker}")
                            
                            # Process this chunk with full marker
                            full_chunk = f"{'='*50}\n{match_marker}\n{match_sections[i]}"
                            process_log_chunk(full_chunk)
    
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
