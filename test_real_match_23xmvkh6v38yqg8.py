#!/usr/bin/env python3
"""
Test script to send a real Telegram alert for a specific match ID.
This script uses the actual alert system and formatter to demonstrate
the full alert with real match data.
"""
import os
import sys
import json
import importlib
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('telegram_test')

# Real match ID to test
REAL_MATCH_ID = "23xmvkh6v38yqg8"

def main():
    """Main test function."""
    print("🔍 DEBUG — CWD:", os.getcwd())
    print("🔍 DEBUG — PYTHONPATH:", os.environ.get('PYTHONPATH'))
    
    # Try to import the alert system
    try:
        # Import directly
        from football.live_alerts import alert_system
        logger.info("Imported alert_system directly")
    except ImportError:
        try:
            # Import using importlib
            alert_system = importlib.import_module('football.live_alerts.alert_system')
            logger.info("Imported alert_system using importlib")
        except ImportError as e:
            logger.error(f"Failed to import alert_system: {e}")
            sys.exit(1)
    
    # Try to import 3o_u_alert module
    try:
        # Import using importlib (needed for modules that start with numbers)
        ou_alert = importlib.import_module('football.live_alerts.3o_u_alert')
        logger.info("Loaded 3o_u_alert module")
    except ImportError as e:
        logger.error(f"Failed to import 3o_u_alert module: {e}")
        sys.exit(1)
    
    # Try to import telegram module
    try:
        # Check if telegram module is available
        from football.telegram import send_telegram_message
        logger.info("✓ Telegram module found and imported successfully")
    except ImportError:
        logger.error("× Failed to import telegram module")
        sys.exit(1)
    
    # Create sample data for the specific match ID
    match_data = {
        "id": REAL_MATCH_ID,
        "home_team": "Hapoel Ramat Gan",
        "away_team": "Maccabi Herzliya",
        "competition": "Israel Leumit League",
        "country": "Israel",
        "status_id": 1,  # In Play
        "status_name": "In Play",
        "home_score": 2,
        "away_score": 0,
        "ht_home_score": 2,
        "ht_away_score": 0,
        "competition_id": "v2y8m4zhv6ql074",
        # Odds data - setting O/U line to 3.0 to trigger alert
        "ou_handicap": 3.0,  
        "ou_over_american": "+110",
        "ou_under_american": "-130",
        "odds_time_minutes": 4,
        "ml_home_american": "-105",
        "ml_draw_american": "+300",
        "ml_away_american": "+210",
        "ah_handicap": 0.25,
        "ah_home_american": "-130",
        "ah_away_american": "+102"
    }
    
    # Process the match with the alert system
    logger.info("Processing match data with real Telegram sending...")
    result = alert_system.process_match_with_alerts(match_data)
    
    # Check if an alert was triggered
    if result and '3o_u_alert' in result and result['3o_u_alert']:
        logger.info(f"REAL TELEGRAM ALERT SENT! Result: {result}")
        print("\n✓ TELEGRAM ALERT SENT SUCCESSFULLY!")
        print("Check your Telegram for the message")
    else:
        logger.error(f"Failed to send Telegram alert. Result: {result}")
        print("\n✗ FAILED TO SEND TELEGRAM ALERT")

if __name__ == "__main__":
    main()
