#!/usr/bin/env python3
"""
Telegram Configuration File
Contains all settings and functions needed for sending alerts to Telegram
"""

import os
import requests
import logging
import json
import time
from datetime import datetime
import traceback
import sys
import pytz

# Configure logging
logger = logging.getLogger('sports_alerts.telegram')
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Telegram API credentials
TELEGRAM_TOKEN = "7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko"
TELEGRAM_CHAT_ID = "6128359776"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

# Rate limiting settings to avoid Telegram API throttling
RATE_LIMIT = {
    'last_sent': 0,
    'min_interval': 1,  # Minimum seconds between messages
    'burst_count': 0,
    'burst_limit': 5,   # Max messages in burst
    'burst_reset': 0,   # Time when burst count resets
    'burst_window': 60  # Seconds for burst window
}

# Message history for deduplication
MESSAGE_HISTORY = {
    'messages': [],
    'max_size': 10
}

# Alert type emojis for better visibility
ALERT_ICONS = {
    'startup': '🟢',       # Green circle for startup
    'shutdown': '🔴',      # Red circle for shutdown
    'error': '⚠️',         # Warning for errors
    'match': '⚽',         # Soccer ball for match alerts
    'goal': '🥅',          # Goal net for goals
    'odds': '📊',          # Chart for odds updates
    'weather': '🌤️',       # Weather icon for environment
    'status': '📡',        # Antenna for status updates
    'warning': '⚠️',       # Warning sign
    'info': 'ℹ️',          # Info symbol
    'default': '🔔'        # Bell for default messages
}

# Datetime format for consistency
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
    current_time = time.time()
    
    # Reset burst counter if we're outside the burst window
    if current_time - RATE_LIMIT['burst_reset'] > RATE_LIMIT['burst_window']:
        RATE_LIMIT['burst_count'] = 0
        RATE_LIMIT['burst_reset'] = current_time
    
    # Check if we're over the burst limit
    if RATE_LIMIT['burst_count'] >= RATE_LIMIT['burst_limit']:
        # Calculate sleep time to wait until burst window resets
        sleep_time = RATE_LIMIT['burst_reset'] + RATE_LIMIT['burst_window'] - current_time
        if sleep_time > 0:
            logger.warning(f"Rate limit exceeded. Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
            # Refresh time and reset burst after sleeping
            current_time = time.time()
            RATE_LIMIT['burst_count'] = 0
            RATE_LIMIT['burst_reset'] = current_time
    
    # Check minimum interval between messages
    elapsed = current_time - RATE_LIMIT['last_sent']
    if elapsed < RATE_LIMIT['min_interval']:
        sleep_time = RATE_LIMIT['min_interval'] - elapsed
        logger.debug(f"Enforcing minimum interval. Sleeping for {sleep_time:.2f} seconds")
        time.sleep(sleep_time)
    
    # Update state
    RATE_LIMIT['last_sent'] = time.time()
    RATE_LIMIT['burst_count'] += 1

def send_telegram_message(message, parse_mode="Markdown", disable_notification=False):
    """
    Send a message to Telegram
    
    Args:
        message: Text message to send
        parse_mode: Telegram parse mode (Markdown or HTML)
        disable_notification: If True, sends the message silently
        
    Returns:
        dict: Response from Telegram API or None if failed
    """
    # Skip duplicate messages
    if _is_duplicate_message(message):
        logger.info("Skipping duplicate message")
        return {"ok": True, "result": {"message_id": -1, "text": "DUPLICATE_SKIPPED"}}
    
    # Add to history
    _add_message_to_history(message)
    
    # Enforce rate limiting
    _enforce_rate_limit()
    
    # Prepare payload
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': parse_mode,
        'disable_notification': disable_notification
    }
    
    try:
        response = requests.post(TELEGRAM_API_URL, json=payload)
        response_json = response.json()
        
        if response.status_code == 200 and response_json.get('ok', False):
            logger.info(f"Message sent: {message[:50]}...")
            return response_json
        else:
            logger.error(f"Failed to send message: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return None

def send_simple_message(message, silent=False):
    """Send a basic message to Telegram"""
    return send_telegram_message(message, disable_notification=silent)

def send_alert(message, alert_type="info"):
    """Send a formatted alert message with appropriate icon"""
    icon = ALERT_ICONS.get(alert_type, ALERT_ICONS['default'])
    title = alert_type.upper()
    formatted_message = f"{icon} *{title} ALERT* {icon}\n\n{message}"
    
    # Add timestamp
    eastern_time = get_eastern_time()
    formatted_message += f"\n\n*Time:* {eastern_time.strftime(API_DATETIME_FORMAT)}"
    
    # Critical alerts shouldn't be silent
    silent = alert_type in ["info"]
    
    return send_telegram_message(formatted_message, disable_notification=silent)

def send_match_alert(message, match_id=None, teams=None, score=None, competition=None):
    """Send a match-specific alert with details"""
    icon = ALERT_ICONS.get('match', '⚽')
    formatted_message = f"{icon} *MATCH ALERT* {icon}\n\n{message}\n\n"
    
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
    
    return send_telegram_message(formatted_message)

def send_system_alert(message, alert_type="info", error_details=None, include_trace=False):
    """Send a system status alert"""
    icon = ALERT_ICONS.get(alert_type, ALERT_ICONS['default'])
    
    if alert_type == "startup":
        title = "SYSTEM STARTING"
    elif alert_type == "shutdown":
        title = "SYSTEM STOPPING"
    elif alert_type == "error":
        title = "SYSTEM ERROR"
    elif alert_type == "warning":
        title = "SYSTEM WARNING" 
    else:
        title = "SYSTEM NOTIFICATION"
    
    formatted_message = f"{icon} *{title}* {icon}\n\n{message}\n"
    
    if error_details:
        formatted_message += f"\n*Error details:* ```\n{error_details}\n```"
        
    if include_trace and sys.exc_info()[0] is not None:
        trace = traceback.format_exc()
        formatted_message += f"\n*Stack trace:* ```\n{trace[:800]}```"  # Limit length
        
    eastern_time = get_eastern_time()
    formatted_message += f"\n*Time:* {eastern_time.strftime(API_DATETIME_FORMAT)}"
    
    # Critical alerts shouldn't be silent
    silent = alert_type in ["info"]
    
    return send_telegram_message(formatted_message, disable_notification=silent)

# Test the configuration if run directly
if __name__ == "__main__":
    message = "Test alert from the new sports_bot alert system"
    print(f"Sending test message: {message}")
    result = send_telegram_message(message, parse_mode="")
    if result and result.get('ok'):
        print("✅ Test message sent successfully!")
    else:
        print("❌ Failed to send test message")
