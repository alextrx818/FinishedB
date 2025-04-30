#!/usr/bin/env python3
"""
Base Log Scanner Alert Class
Provides common functionality for all log-based alerts
"""

import os
import logging
import requests
from datetime import datetime, timedelta, timezone

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S ET',
    handlers=[
        logging.FileHandler(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            "logs/log_alerts.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("log_alerts")

# Default Telegram settings
DEFAULT_TELEGRAM_TOKEN = "7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko"
DEFAULT_TELEGRAM_CHAT_ID = "6128359776"

# Eastern Time zone utility
def get_eastern_time():
    """Get current datetime in US Eastern Time (handles DST)"""
    # Get UTC time
    utc_now = datetime.now(timezone.utc)
    
    # Eastern Standard Time is UTC-5
    # Eastern Daylight Time is UTC-4
    # Python can determine if DST is in effect
    est_offset = -5
    edt_offset = -4
    
    # Check if DST is in effect (approximate method)
    # DST in US starts second Sunday in March and ends first Sunday in November
    year = utc_now.year
    dst_start = datetime(year, 3, 8, 2, 0, tzinfo=timezone.utc)  # 2 AM on second Sunday in March
    dst_start += timedelta(days=(6 - dst_start.weekday()) % 7)  # Adjust to Sunday
    
    dst_end = datetime(year, 11, 1, 2, 0, tzinfo=timezone.utc)  # 2 AM on first Sunday in November
    dst_end += timedelta(days=(6 - dst_end.weekday()) % 7)  # Adjust to Sunday
    
    # Determine if we're in DST
    is_dst = dst_start <= utc_now < dst_end
    offset = edt_offset if is_dst else est_offset
    
    # Apply offset
    et = utc_now + timedelta(hours=offset)
    return et

class LogScannerAlert:
    """Base class for log scanner alerts"""
    def __init__(self, name, telegram_token=None, telegram_chat_id=None):
        self.name = name
        self.telegram_token = telegram_token or DEFAULT_TELEGRAM_TOKEN
        self.telegram_chat_id = telegram_chat_id or DEFAULT_TELEGRAM_CHAT_ID
        self.tracked_matches = set()  # Keep track of matches we've already alerted on
        
    def scan_log_file(self, log_file):
        """Scan a log file for matches meeting the criteria"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def send_telegram_alert(self, message):
        """Send an alert message via Telegram"""
        telegram_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        
        # Add timestamp to message with Eastern Time
        timestamp = get_eastern_time().strftime("%Y-%m-%d %H:%M:%S ET")
        message = f"{message}\n\nTimestamp: {timestamp}"
        
        try:
            response = requests.post(
                telegram_url,
                json={
                    "chat_id": self.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
            )
            if response.status_code == 200:
                logger.info(f"Successfully sent Telegram alert for {self.name}")
            else:
                logger.error(f"Failed to send Telegram alert: {response.text}")
        except Exception as e:
            logger.error(f"Error sending Telegram alert: {e}")
