#!/usr/bin/env python3
"""
# EDIT REPORT - 2025-05-09
# Impact of Resilience Enhancements on Telegram Alerts
#
# Changes impacting this functionality:
# 1. Normalized alert severity levels across the system:
#    - CRITICAL: Only unrecoverable startup/import failures
#    - ERROR: Thread and asyncio task exceptions
#    - WARNING: Non-critical component failures (e.g., Supabase connection)
#    - INFO: Expected operational messages
#
# 2. All calls to send_system_alert() now include explicit alert_type parameter
# 3. Enhanced error message content for critical failures
# 4. Combined failure test verifies that alerts are sent for all error types
#
# See EDIT_REPORT_TEST.md for complete details.
#

Centralized Telegram Notification System for Football Monitor

This module serves as the single point of contact for all Telegram communications,
including system alerts, match alerts, and general notifications.

Usage:
    from football.telegram import send_message, send_alert, send_match_alert, send_system_alert
    
    # General message
    send_message("Hello from the football monitor")
    
    # Alert with higher visibility
    send_alert("Important alert: API rate limit approaching")
    
    # Match-specific alert
    send_match_alert("Goal scored!", match_id="abc123", teams="Team A vs Team B", score="1-0")
    
    # System status alerts
    send_system_alert("System starting", alert_type="startup")
    send_system_alert("Error occurred", alert_type="error", error_details="Connection timeout")
"""

import os
import requests
import logging
import json
import time
from datetime import datetime
import traceback
import pytz

# Configure logging
logger = logging.getLogger(__name__)

# Telegram API credentials - using the existing credentials from the project
TELEGRAM_TOKEN = "7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko"
TELEGRAM_CHAT_ID = "6128359776"

# Rate limiting to avoid flooding Telegram API
RATE_LIMIT = {
    'last_sent': 0,
    'min_interval': 1,  # Minimum seconds between messages
    'burst_count': 0,
    'burst_limit': 5,   # Max messages in burst
    'burst_reset': 0,   # Time when burst count resets
    'burst_window': 60  # Seconds for burst window
}

# Alert categories and their emoji
ALERT_TYPES = {
    'startup': '🟢',       # Green circle for startup
    'shutdown': '🔴',      # Red circle for shutdown
    'error': '⚠️',         # Warning for errors
    'match': '⚽',         # Soccer ball for match alerts
    'goal': '🥅',          # Goal net for goals
    'odds': '📊',          # Chart for odds updates
    'weather': '🌤️',       # Weather icon for environment
    'status': '📡',        # Antenna for status updates
    'heartbeat': '💓',     # Heartbeat for monitoring
    'warning': '⚠️',       # Warning sign
    'info': 'ℹ️',          # Info symbol
    'default': '🔔'        # Bell for default messages
}

# History tracking to avoid duplicate messages in quick succession
MESSAGE_HISTORY = {
    'messages': [],
    'max_size': 10
}

# Import the datetime format constants from live.py
try:
    from football.live import API_DATETIME_FORMAT
except ImportError:
    # Define locally if import fails
    API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"

def get_eastern_time():
    """Get current time in Eastern timezone"""
    utc_now = datetime.now(pytz.utc)
    eastern = pytz.timezone('America/New_York')
    eastern_time = utc_now.astimezone(eastern)
    return eastern_time

def _is_duplicate_message(message):
    """Check if a message is a duplicate of recent messages"""
    # Compare with recent message history
    for timestamp, old_message in MESSAGE_HISTORY['messages']:
        # If the message text is identical and was sent in the last 5 minutes
        if old_message == message and (time.time() - timestamp) < 300:  # 5 minutes
            return True
    return False

def _add_message_to_history(message):
    """Add a message to the history tracker"""
    MESSAGE_HISTORY['messages'].append((time.time(), message))
    # Trim history if needed
    if len(MESSAGE_HISTORY['messages']) > MESSAGE_HISTORY['max_size']:
        MESSAGE_HISTORY['messages'] = MESSAGE_HISTORY['messages'][-MESSAGE_HISTORY['max_size']:]

def _enforce_rate_limit():
    """Enforces rate limiting for Telegram API calls"""
    now = time.time()
    
    # Reset burst count if window has passed
    if now - RATE_LIMIT['burst_reset'] > RATE_LIMIT['burst_window']:
        RATE_LIMIT['burst_count'] = 0
        RATE_LIMIT['burst_reset'] = now
        
    # Check if we need to wait due to individual message timing
    time_since_last = now - RATE_LIMIT['last_sent']
    if time_since_last < RATE_LIMIT['min_interval']:
        time.sleep(RATE_LIMIT['min_interval'] - time_since_last)
        
    # Check if we've hit burst limit
    if RATE_LIMIT['burst_count'] >= RATE_LIMIT['burst_limit']:
        # Wait until burst window resets
        sleep_time = RATE_LIMIT['burst_reset'] + RATE_LIMIT['burst_window'] - now
        if sleep_time > 0:
            logger.info(f"Rate limit hit, waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            RATE_LIMIT['burst_count'] = 0
            RATE_LIMIT['burst_reset'] = time.time()
    
    # Update rate limiting trackers
    RATE_LIMIT['last_sent'] = time.time()
    RATE_LIMIT['burst_count'] += 1

def _send_telegram_message(message, parse_mode="Markdown", disable_notification=False):
    """
    Low-level function to send a message to Telegram
    
    Args:
        message: Text message to send
        parse_mode: Telegram parse mode (Markdown or HTML)
        disable_notification: If True, sends the message silently
        
    Returns:
        dict: Response from Telegram API or None if failed
    """
    if not message:
        logger.warning("Empty message not sent to Telegram")
        return None
        
    # Check for duplicate messages
    if _is_duplicate_message(message):
        logger.info(f"Skipping duplicate message: {message[:30]}...")
        return None
        
    # Enforce rate limiting
    _enforce_rate_limit()
    
    # Add to history tracker
    _add_message_to_history(message)
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": parse_mode,
            "disable_notification": disable_notification
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code != 200:
            logger.error(f"Failed to send Telegram message: {response.text}")
            return None
            
        return response.json()
        
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return None

def send_message(message, silent=False):
    """
    Send a general message to Telegram
    
    Args:
        message: Text message to send
        silent: If True, sends without notification sound
    """
    return _send_telegram_message(message, disable_notification=silent)

def send_alert(message, icon=None):
    """
    Send an alert message with higher visibility
    
    Args:
        message: Alert text to send
        icon: Optional emoji to prefix the message
    """
    icon = icon or ALERT_TYPES['warning']
    formatted_message = f"{icon} *ALERT* {icon}\n\n{message}"
    return _send_telegram_message(formatted_message)

def send_match_alert(message, match_id=None, teams=None, score=None, competition=None, alert_type="match"):
    """
    Send a match-specific alert with relevant details
    
    Args:
        message: Main alert message
        match_id: Optional match identifier
        teams: Optional team names (e.g., "Team A vs Team B")
        score: Optional current score
        competition: Optional competition name
        alert_type: Type of match alert (match, goal, odds)
    """
    icon = ALERT_TYPES.get(alert_type, ALERT_TYPES['match'])
    
    formatted_message = f"{icon} *MATCH ALERT* {icon}\n\n"
    formatted_message += f"{message}\n\n"
    
    if teams:
        formatted_message += f"*Match:* {teams}\n"
    
    if score:
        formatted_message += f"*Score:* {score}\n"
        
    if competition:
        formatted_message += f"*Competition:* {competition}\n"
        
    if match_id:
        formatted_message += f"*ID:* `{match_id}`\n"
        
    eastern_time = get_eastern_time()
    formatted_message += f"\n*Time:* {eastern_time.strftime(API_DATETIME_FORMAT)}"
    
    return _send_telegram_message(formatted_message)

def send_system_alert(message, alert_type="info", error_details=None, include_trace=False):
    """
    Send a system status alert
    
    Args:
        message: Main alert message
        alert_type: Type of system alert (startup, shutdown, error, warning, info)
        error_details: Optional error details if alert_type is 'error'
        include_trace: If True and exception occurred, include stack trace
    """
    icon = ALERT_TYPES.get(alert_type, ALERT_TYPES['default'])
    
    if alert_type == "startup":
        title = "SYSTEM STARTING"
    elif alert_type == "shutdown":
        title = "SYSTEM STOPPING"
    elif alert_type == "error":
        title = "SYSTEM ERROR"
    elif alert_type == "warning":
        title = "SYSTEM WARNING" 
    elif alert_type == "heartbeat":
        title = "SYSTEM HEARTBEAT"
    else:
        title = "SYSTEM NOTIFICATION"
    
    formatted_message = f"{icon} *{title}* {icon}\n\n"
    formatted_message += f"{message}\n"
    
    if error_details:
        formatted_message += f"\n*Error details:* ```\n{error_details}\n```"
        
    if include_trace and sys.exc_info()[0] is not None:
        trace = traceback.format_exc()
        formatted_message += f"\n*Stack trace:* ```\n{trace[:800]}```"  # Limit length
        
    eastern_time = get_eastern_time()
    formatted_message += f"\n*Time:* {eastern_time.strftime(API_DATETIME_FORMAT)}"
    
    # Critical alerts shouldn't be silent
    silent = alert_type in ["info", "heartbeat"]
    
    return _send_telegram_message(formatted_message, disable_notification=silent)

# Convenience aliases for common notifications
def notify_startup():
    """Notify that the system is starting up"""
    return send_system_alert("Football monitor is starting", alert_type="startup")
    
def notify_shutdown():
    """Notify that the system is shutting down"""
    return send_system_alert("Football monitor is stopping", alert_type="shutdown")
    
def notify_error(error_message, error_details=None):
    """Notify about a system error"""
    return send_system_alert(f"Error: {error_message}", 
                           alert_type="error", 
                           error_details=error_details,
                           include_trace=True)

# Module initialization
if __name__ == "__main__":
    # If run directly, send a test message
    send_message("Telegram notification system test message")
    print("Test message sent. Check your Telegram!")
