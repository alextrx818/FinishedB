#!/usr/bin/env python3
"""
Log Scanner Script
Scans log files for specific match criteria and sends alerts via Telegram
"""

import os
import time
import datetime
import argparse
import logging
from pathlib import Path

# Import alert types
from .base import LogScannerAlert, get_eastern_time
from .three_ht_zero import ThreeHtZeroLoggerAlert

# Configure logging
logger = logging.getLogger("log_alerts")

# Configuration
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")

def scan_logs(alerts, specific_date=None):
    """Scan log files for alerts"""
    # Determine which log file to scan
    if specific_date:
        log_date = specific_date
    else:
        log_date = get_eastern_time().strftime("%Y-%m-%d")
        
    log_file = os.path.join(LOG_DIR, f"football_fetches_{log_date}.log")
    
    if not os.path.exists(log_file):
        logger.error(f"Log file {log_file} not found.")
        return
        
    logger.info(f"Scanning log file: {log_file}")
    
    # Run each alert scanner on the log file
    for alert in alerts:
        try:
            alert.scan_log_file(log_file)
        except Exception as e:
            logger.error(f"Error scanning with {alert.name}: {e}")

def continuous_scanning(alerts, interval=60):
    """Continuously scan logs for alerts at the specified interval"""
    logger.info(f"Starting continuous log scanning every {interval} seconds")
    
    try:
        while True:
            scan_logs(alerts)
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Log scanning stopped by user.")
    except Exception as e:
        logger.error(f"Error in log scanning: {e}")

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Log Alerts System for Football Data')
    parser.add_argument('-c', '--continuous', action='store_true',
                        help='Run in continuous mode, scanning logs at regular intervals')
    parser.add_argument('-i', '--interval', type=int, default=60,
                        help='Interval between scans in seconds (default: 60)')
    parser.add_argument('-d', '--date', type=str, default=None,
                        help='Specific date to scan logs for (YYYY-MM-DD, default: today in Eastern Time)')
    parser.add_argument('-t', '--telegram-token', type=str, default=None,
                        help='Telegram bot token')
    parser.add_argument('-chat', '--telegram-chat-id', type=str, default=None,
                        help='Telegram chat ID')
    args = parser.parse_args()
    
    # Create alert instances
    alerts = [
        ThreeHtZeroLoggerAlert(args.telegram_token, args.telegram_chat_id)
    ]
    
    # Make sure logs directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Show current Eastern Time on startup
    et_now = get_eastern_time().strftime("%Y-%m-%d %H:%M:%S ET")
    logger.info(f"Log scanner starting at {et_now}")
    
    if args.continuous:
        continuous_scanning(alerts, args.interval)
    else:
        scan_logs(alerts, args.date)

if __name__ == "__main__":
    main()
