#!/usr/bin/env python3
"""
Test script to verify alert formatting with a real match example.
Uses a specific match ID to generate an alert and send it to Telegram.
"""
import sys
import os
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('real_match_test')

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the required modules
from football.live_alerts.alert_system import discover_alert_modules, process_match_with_alerts, add_module_to_alert_system

# Import the 3o_u_alert module using importlib (we can't directly import modules starting with numbers)
import importlib
try:
    alert_module = importlib.import_module('football.live_alerts.3o_u_alert')
    logger.info("Successfully imported 3o_u_alert module")
except ImportError:
    # Try relative import as fallback
    try:
        alert_module = importlib.import_module('.3o_u_alert', package='football.live_alerts')
        logger.info("Successfully imported 3o_u_alert module via relative import")
    except ImportError as e:
        logger.error(f"Failed to import 3o_u_alert module: {e}")
        raise

# The specific match ID to test with
MATCH_ID = "23xmvkh6v38yqg8"

def load_match_data(match_id: str) -> Optional[Dict[str, Any]]:
    """
    Load match data for a specific match ID.
    
    First tries to load from a local file, then falls back to sample data.
    
    Args:
        match_id: The match ID to load data for
    
    Returns:
        Match data dictionary or None if not found
    """
    # Paths to check for match data
    paths = [
        f"/root/CascadeProjects/sports_bot/football/data/matches/{match_id}.json",
        f"/root/CascadeProjects/sports_bot/data/matches/{match_id}.json",
        f"/root/CascadeProjects/sports_bot/football/data/{match_id}.json",
        f"/root/CascadeProjects/sports_bot/data/{match_id}.json"
    ]
    
    # Try to load from a file
    for path in paths:
        if os.path.exists(path):
            logger.info(f"Loading match data from {path}")
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON in {path}")
            except Exception as e:
                logger.error(f"Error loading match data: {str(e)}")
    
    # If we can't find a file, create sample data based on the match info
    logger.warning(f"Match data file not found for {match_id}, creating sample data")
    
    # Create sample data with O/U line of 3.0 to trigger the alert
    sample_data = {
        "id": match_id,
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
        # Odds data
        "ou_handicap": 3.0,  # Setting Over/Under line to 3.0 to trigger alert
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
    
    return sample_data

def main():
    """
    Main test function.
    """
    logger.info(f"Starting real match alert test with match ID: {MATCH_ID}")
    
    # Load match data
    match_data = load_match_data(MATCH_ID)
    if not match_data:
        logger.error("Failed to load match data")
        return
    
    # Set a high Over/Under line to ensure the alert is triggered
    if match_data.get('ou_handicap', 0) < 3.0:
        logger.info(f"Setting Over/Under line to 3.0 to ensure alert is triggered")
        match_data['ou_handicap'] = 3.0
    
    # Initialize the alert system
    logger.info("Initializing alert system")
    alert_modules = discover_alert_modules()
    
    # Add the 3o_u_alert module
    logger.info("Adding 3o_u_alert module to alert system")
    add_module_to_alert_system('3o_u_alert', alert_module)
    
    # Process the match data
    logger.info("Processing match data")
    result = process_match_with_alerts(match_data)
    
    if result and '3o_u_alert' in result and result['3o_u_alert']:
        logger.info("Alert triggered successfully!")
        print(json.dumps(result, indent=2))
    else:
        logger.error("No alert was triggered")
        print("Match data:", json.dumps(match_data, indent=2))
        print("Result:", json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
