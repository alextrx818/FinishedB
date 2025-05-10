#!/usr/bin/env python3
"""
Consolidated Environment Alert Module

This alert module specifically handles missing environment data alerts.
It consolidates multiple alerts over a 30-minute period to reduce notification noise
while still ensuring all important missing data is communicated.

This follows the system architecture by maintaining separation between regular
sports alerts and the live alert system.
"""

import os
import sys
import time
import threading
from datetime import datetime
import pytz
from typing import Dict, Tuple, List, Set, Optional

# Dictionary to store matches with missing environment data
# Format: {match_id: (teams, competition, timestamp)}
pending_environment_alerts = {}

# Set to track matches that have already been alerted about
alerted_matches = set()

# Lock for thread safety when accessing shared data
alerts_lock = threading.Lock()

# Time when the next consolidated alert should be sent (Unix timestamp)
next_alert_time = time.time() + 1800  # 30 minutes from module load

# Timer object for sending consolidated alerts
alert_timer = None

def get_eastern_time():
    """Get current time in Eastern timezone as a formatted string"""
    try:
        utc_now = datetime.now(pytz.utc)
        eastern = pytz.timezone('America/New_York')
        eastern_time = utc_now.astimezone(eastern)
        return eastern_time.strftime("%m/%d/%Y %I:%M:%S %p ET")
    except Exception:
        # Fallback if timezone conversion fails
        return datetime.now().strftime("%m/%d/%Y %I:%M:%S")

def send_consolidated_alert():
    """Send a consolidated alert for all pending matches with missing environment data"""
    global next_alert_time, alert_timer, pending_environment_alerts
    
    with alerts_lock:
        if not pending_environment_alerts:
            # No alerts to send, reset timer and return
            next_alert_time = time.time() + 1800  # 30 minutes
            _start_timer()
            return
        
        match_count = len(pending_environment_alerts)
        print(f"[ENV_ALERT] Sending consolidated alert for {match_count} matches with missing environment data")
        
        # Format alert message
        alert_title = f"⚠️ Missing environment data in {match_count} matches"
        alert_description = "The following matches are missing weather, temperature or wind data:"
        
        # Build the match list
        match_list = []
        for match_id, (teams, competition, timestamp) in pending_environment_alerts.items():
            # Add each match to the list
            match_list.append(f"• {teams} [{competition}] (ID: {match_id})")
        
        # Join the match list with newlines, limit to 10 with indication if there are more
        if len(match_list) > 10:
            match_text = "\n".join(match_list[:10])
            match_text += f"\n...and {len(match_list) - 10} more matches"
        else:
            match_text = "\n".join(match_list)
        
        # Compose the full message
        message = f"{alert_title}\n\n{alert_description}\n\n{match_text}"
        
        # Send the alert through the main telegram system
        try:
            # Use system alert since this covers multiple matches
            from football.telegram import send_system_alert
            send_system_alert(
                message,
                alert_type="warning"
            )
            print(f"[ENV_ALERT] Sent consolidated alert for {match_count} matches")
        except Exception as e:
            print(f"[ENV_ALERT] Error sending consolidated alert: {e}")
        
        # Clear pending alerts and reset the timer
        pending_environment_alerts.clear()
        next_alert_time = time.time() + 1800  # 30 minutes
        _start_timer()

def _start_timer():
    """Start a timer for sending the next consolidated alert"""
    global alert_timer, next_alert_time
    
    # Cancel any existing timer
    if alert_timer is not None:
        try:
            alert_timer.cancel()
        except Exception:
            pass
    
    # Calculate seconds until next alert
    seconds_until_next = max(1, next_alert_time - time.time())
    
    # Create and start a new timer
    alert_timer = threading.Timer(seconds_until_next, send_consolidated_alert)
    alert_timer.daemon = True
    alert_timer.start()
    
    print(f"[ENV_ALERT] Next environment alert scheduled in {int(seconds_until_next)} seconds")

def process_match_data(match_data, previous_match_data=None):
    """
    Process match data to check for missing environment information
    
    Args:
        match_data: Current match data dictionary
        previous_match_data: Previous match data for the same match (not used in this alert)
        
    Returns:
        bool: True if an alert was triggered, False otherwise
    """
    # Extract relevant fields
    match_id = match_data.get('id')
    if not match_id:
        return False
    
    # Skip matches we've already processed
    if match_id in alerted_matches:
        return False
    
    # Check for missing environment data
    has_weather = bool(match_data.get('weather'))
    has_temperature = bool(match_data.get('temperature')) 
    has_wind = bool(match_data.get('wind'))
    
    # If ANY environment data is missing, we'll consolidate an alert
    if not (has_weather or has_temperature or has_wind):
        with alerts_lock:
            # Get team and competition info
            teams = f"{match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}"
            competition = match_data.get('competition', 'Unknown Competition')
            
            # Add to pending alerts
            pending_environment_alerts[match_id] = (teams, competition, time.time())
            
            # Mark as alerted so we don't process it again
            alerted_matches.add(match_id)
            
            # Make sure a timer is running
            if alert_timer is None:
                _start_timer()
            
            print(f"[ENV_ALERT] Added match {match_id} to pending environment alerts (total: {len(pending_environment_alerts)})")
            return True
    
    return False

# Initialize the timer when the module is loaded
_start_timer()

# Alert module required functions
def get_name():
    """Return the name of this alert module"""
    return "Environment Data Alert"

def get_description():
    """Return a description of what this alert checks for"""
    return "Checks for matches missing environment data and sends consolidated alerts every 30 minutes"

# Test function when run directly
if __name__ == "__main__":
    # Create a test match with missing environment data
    test_match = {
        'id': 'test123',
        'home_team': 'Test Home',
        'away_team': 'Test Away',
        'competition': 'Test League',
        'weather': '',  # Empty weather
        'temperature': '',  # Empty temperature
        'wind': ''  # Empty wind
    }
    
    # Process the test match
    result = process_match_data(test_match)
    print(f"Alert triggered: {result}")
    
    # Force an immediate alert for testing
    next_alert_time = time.time()
    send_consolidated_alert()
