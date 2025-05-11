#!/usr/bin/env python3
"""
Main Match Alerts Bridge

This module serves as a bridge between live.py and individual alert modules.
It provides a clean integration point for alert modules to receive match data 
and generate alerts with minimal changes to live.py.

How to use:
1. Import this module in live.py with minimal modifications
2. Call process_match() from live.py when new match data is available
3. Create alert modules (like ThreeOU.py) in the same directory

This architecture follows the separation of concerns principle:
- live.py: Core data fetching and processing (minimal modifications)
- main_match_alerts.py: Alert system orchestration
- Individual alert modules: Specific alert detection logic
- telegram_config.py: Alert delivery

Example minimal integration with live.py:
```python
# At the top of live.py with other imports
from all_alerts.live_match_alerts import main_match_alerts

# In the match processing section
main_match_alerts.process_match(match_data)
```
"""

import os
import sys
import importlib
import inspect
import logging
import traceback
from typing import Dict, List, Any, Optional, Set
from datetime import datetime

# Add parent directory to path to allow imports from all_alerts
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import telegram config for sending alerts
try:
    import sys
    import os
    # Add parent directory to path if needed
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    from telegram_config import send_system_alert
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Warning: telegram_config not available. Alerts will not be sent.")
    traceback.print_exc()

# Set up logging for the orchestration layer (without creating a dedicated file)
try:
    # Add project root to path if needed
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.append(project_root)
    
    # Import the get_alert_logger function from main_logger.py
    from logger.main_logger import get_alert_logger
    
    # Set up a standard logger without a file for this orchestration module
    logger = logging.getLogger('sports_alerts.orchestrator')
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # We have access to main_logger.py for creating alert module loggers
    USING_MAIN_LOGGER = True
    
except ImportError:
    # Fall back to standard logging if main_logger.py isn't available
    logger = logging.getLogger('sports_alerts.orchestrator')
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    logger.warning("Failed to import main_logger.py, using fallback logging")
    USING_MAIN_LOGGER = False

# Module configuration
CONFIG = {
    'enabled': True,
    'debug': True,           # Set to True for verbose logging
    'alert_modules_dir': os.path.dirname(os.path.abspath(__file__)),
    'modules_to_skip': ['__pycache__', 'main_match_alerts.py']
}

# Dictionary to store module references
loaded_modules = {}

# Cache of previous match data by match_id for change detection
match_data_cache = {}

# Processed alert keys for deduplication
processed_alerts = set()

def load_alert_modules() -> Dict[str, Any]:
    """
    Dynamically load all alert modules in the same directory.
    
    Modules are loaded from .py files in the same directory as this file.
    Each module should implement a process_match_data() function.
    
    Returns:
        Dict of module names to module objects
    """
    modules_dir = CONFIG['alert_modules_dir']
    modules_to_skip = CONFIG['modules_to_skip']
    
    if CONFIG['debug']:
        logger.info(f"Loading alert modules from {modules_dir}")
    
    modules = {}
    
    # Get all .py files in the directory
    try:
        files = [f for f in os.listdir(modules_dir) 
                if f.endswith('.py') and f not in modules_to_skip]
    except Exception as e:
        logger.error(f"Error listing directory {modules_dir}: {e}")
        return modules
    
    # Import each module
    for file in files:
        module_name = file[:-3]  # Remove .py extension
        if CONFIG['debug']:
            logger.info(f"Found alert module: {module_name}")
        
        try:
            # Import the module
            spec = importlib.util.spec_from_file_location(
                module_name, 
                os.path.join(modules_dir, file)
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Create a dedicated logger for this module if using main_logger.py
            if USING_MAIN_LOGGER:
                try:
                    from logger.main_logger import get_alert_logger
                    module_logger = get_alert_logger(module_name)
                    
                    # If the module doesn't already have a logger attribute, add it
                    if not hasattr(module, 'logger') or module.logger.name != f'sports_alerts.{module_name}':
                        module.logger = module_logger
                        logger.info(f"Added custom logger to {module_name}")
                except Exception as logger_error:
                    logger.warning(f"Failed to set up logger for {module_name}: {logger_error}")
            
            # Check if it has the required function
            if hasattr(module, 'process_match_data'):
                modules[module_name] = module
                logger.info(f"Successfully loaded {module_name}")
            else:
                logger.warning(f"Module {module_name} has no process_match_data function")
        except Exception as e:
            logger.error(f"Error importing {module_name}: {e}")
            logger.error(traceback.format_exc())
    
    if CONFIG['debug']:
        logger.info(f"Loaded {len(modules)} alert modules: {', '.join(modules.keys())}")
    
    return modules

def send_telegram_alert(alert_data: Dict[str, Any]) -> bool:
    """
    Send an alert to Telegram.
    
    Args:
        alert_data: Alert data to send
        
    Returns:
        True if alert was sent successfully, False otherwise
    """
    if not TELEGRAM_AVAILABLE:
        logger.warning("Telegram is not available. Alert not sent.")
        return False
        
    try:
        # Construct message from alert data
        title = alert_data.get('title', 'Alert')
        message = alert_data.get('message', 'No message')
        teams = alert_data.get('teams', 'Unknown Teams')
        competition = alert_data.get('competition', 'Unknown Competition')
        match_id = alert_data.get('match_id', 'unknown')
        
        # Build a formatted message
        formatted_message = f"*{title}*\n"
        formatted_message += f"Match: {teams}\n"
        formatted_message += f"Competition: {competition}\n"
        formatted_message += f"Message: {message}\n"
        
        # Add score if available
        if 'current_score' in alert_data:
            formatted_message += f"Score: {alert_data['current_score']}\n"
            
        # Add match ID for reference
        formatted_message += f"Match ID: {match_id}"
        
        # Send the message
        if TELEGRAM_AVAILABLE:
            send_system_alert(formatted_message)
        return True
    except Exception as e:
        logger.error(f"Error sending Telegram alert: {e}")
        traceback.print_exc()
        return False

def format_match_summary(match_data):
    """Generate a match summary in the exact same format as live.py"""
    try:
        lines = []
        lines.append("==================================================\n")
        
        # Center the MATCH line for visual clarity
        if '_loop_index' in match_data and '_total_matches' in match_data:
            match_line = f"MATCH #{match_data['_loop_index']} OF {match_data['_total_matches']}"
        else:
            match_line = f"MATCH ALERT: {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}"
            
        lines.append(match_line)
        lines.append("==================================================\n")
        
        lines.append("----- MATCH SUMMARY -----")
        # Use Eastern time for timestamp formatting
        timestamp = datetime.now(pytz.timezone('US/Eastern')).strftime("%m/%d/%Y %I:%M:%S %p ET")
        lines.append(f"Timestamp: {timestamp}")
        lines.append(f"Match ID: {match_data.get('id', 'Unknown')}")
        lines.append(f"Competition ID: {match_data.get('competition_id', 'Unknown')}")
        lines.append(f"Competition: {match_data.get('competition', 'Unknown')} ({match_data.get('country', 'Unknown')})")
        lines.append(f"Match: {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}")
        
        # Format score
        home_score = match_data.get('home_score', 0)
        away_score = match_data.get('away_score', 0)
        home_ht_score = match_data.get('home_ht_score', '')
        away_ht_score = match_data.get('away_ht_score', '')
        
        lines.append(f"Score: {home_score} - {away_score} (HT: {home_ht_score} - {away_ht_score})")
        lines.append(f"Status: {match_data.get('status', 'Unknown')} (Status ID: {match_data.get('status_id', 'Unknown')})")
        
        # Add betting odds section if available
        if match_data.get('ml_home') or match_data.get('ou_handicap'):
            lines.append("\n--- MATCH BETTING ODDS ---")
            
            # Money Line odds
            if match_data.get('ml_home'):
                lines.append("ML (Money Line):")
                ml_time = match_data.get('ml_time', '')
                ml_home = match_data.get('ml_home', '')
                ml_draw = match_data.get('ml_draw', '')
                ml_away = match_data.get('ml_away', '')
                lines.append(f"Time: {ml_time} | Home: {ml_home} | Draw: {ml_draw} | Away: {ml_away}")
                lines.append("")
            
            # Spread odds
            if match_data.get('ah_handicap'):
                lines.append("SPREAD (Asia Handicap):")
                ah_time = match_data.get('ah_time', '')
                ah_home = match_data.get('ah_home', '')
                ah_handicap = match_data.get('ah_handicap', '')
                ah_away = match_data.get('ah_away', '')
                lines.append(f"Time: {ah_time} | Home: {ah_home} | Handicap: {ah_handicap} | Away: {ah_away}")
                lines.append("")
            
            # Over/Under odds
            if match_data.get('ou_handicap'):
                lines.append("Over/Under:")
                ou_time = match_data.get('ou_time', '')
                ou_over = match_data.get('ou_over', '')
                ou_handicap = match_data.get('ou_handicap', '')
                ou_under = match_data.get('ou_under', '')
                lines.append(f"Time: {ou_time} | Over: {ou_over} | Line: {ou_handicap} | Under: {ou_under}")
        
        # Add environment section
        lines.append("\n--- MATCH ENVIRONMENT ---")
        env = []
        if match_data.get("weather"):     env.append(f"Weather: {match_data['weather']}")
        if match_data.get("temperature"): env.append(f"Temperature: {match_data['temperature']}")
        if match_data.get("humidity"):    env.append(f"Humidity: {match_data['humidity']}")
        if match_data.get("wind"):        env.append(f"Wind: {match_data['wind']}")
        
        if env:
            lines.extend(env)
        else:
            lines.append("No environment data available for this match")
            
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error formatting match summary: {e}")
        return f"Error generating match summary: {e}"

def process_match(match_data: Dict[str, Any]) -> None:
    """
    Process a match and check for alert conditions using all loaded modules.
    
    This is the main entry point for live.py to call.
    
    Args:
        match_data: The match data from live.py
    """
    if not CONFIG['enabled']:
        return
        
    match_id = match_data.get('id', match_data.get('match_id'))
    if not match_id:
        return
    
    # Enhanced debugging - log full details about the match to the main logger
    logger.info(f"Processing match {match_id}: {match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}")
    
    # Debug: Check for potential OU line fields
    ou_fields = {}
    for field in match_data.keys():
        # Look for any field that might have odds or line information
        if any(term in field.lower() for term in ['odd', 'line', 'handicap', 'total', 'ou', 'over', 'under', 'point']):
            ou_fields[field] = match_data.get(field)
    
    if ou_fields:
        logger.info(f"Found potential odds fields for match {match_id}: {ou_fields}")
    
    # Also log a sample of all available fields for analysis
    field_sample = dict(list(match_data.items())[:10])  # Just show first 10 fields to avoid overwhelming logs
    logger.info(f"Sample of available fields for match {match_id}: {field_sample}")
    
    
    # Get previous match data if available
    previous_data = match_data_cache.get(match_id)
    
    # Process through each alert module
    for module_name, module in loaded_modules.items():
        try:
            # Call the module's process_match_data function
            alert = module.process_match_data(match_data, previous_data)
            
            if not alert:
                # No alert for this module
                continue
                
            # Check for required fields
            if 'alert_type' not in alert or 'match_id' not in alert:
                logger.warning(f"Alert from {module_name} missing required fields")
                continue
                
            # Get deduplication key
            dedup_key = alert.get('dedup_key', f"{alert['alert_type']}_{alert['match_id']}")
            
            # Skip if already processed
            if dedup_key in processed_alerts:
                if CONFIG['debug']:
                    logger.info(f"Skipping duplicate alert {dedup_key}")
                continue
                
            # Mark as processed for deduplication
            dedup_key = alert.get('dedup_key', '')
            if dedup_key and dedup_key not in processed_alerts:
                processed_alerts.add(dedup_key)
                
                # Log the full match summary to the module's specific logger
                if USING_MAIN_LOGGER and hasattr(module, 'logger'):
                    # Format the match summary in the exact format from live.py
                    match_summary = format_match_summary(match_data)
                    
                    # Add alert-specific information
                    alert_info = (
                        f"\n=== ALERT DETECTED: {alert.get('title', 'Unknown')} ===\n"
                        f"Alert Type: {alert.get('alert_type', 'Unknown')}\n"
                        f"Message: {alert.get('message', 'No message')}\n"
                        f"Teams: {alert.get('teams', match_data.get('home_team', 'Unknown') + ' vs ' + match_data.get('away_team', 'Unknown'))}\n"
                        f"Competition: {alert.get('competition', match_data.get('competition', 'Unknown'))}\n"
                    )
                    
                    # Add line separators for visual clarity
                    module.logger.info("\n" + "=" * 50)
                    module.logger.info(alert_info)
                    module.logger.info(match_summary)
                    module.logger.info("=" * 50 + "\n")
                
                # Send the alert
                if CONFIG['debug']:
                    logger.info(f"Sending alert: {alert['title']}")
                    
                send_telegram_alert(alert)
        except Exception as e:
            logger.error(f"Error processing match in module {module_name}: {e}")
            logger.error(traceback.format_exc())
    
    # Update the match data cache with current data for next time
    match_data_cache[match_id] = match_data

def initialize() -> None:
    """
    Initialize the alert system.
    
    This should be called when first importing the module.
    """
    logger.info("Initializing match alert system")
    global loaded_modules
    loaded_modules = load_alert_modules()
    logger.info(f"Loaded {len(loaded_modules)} alert modules")

def reset() -> None:
    """
    Reset the module state and clear caches.
    
    This can be called to reset the state of the alert system.
    """
    processed_alerts.clear()
    match_data_cache.clear()
    logger.info("Match alerts state reset")
    
    # Reset all modules if they have a reset function
    for module_name, module in loaded_modules.items():
        if hasattr(module, 'reset'):
            try:
                module.reset()
                logger.info(f"Reset module {module_name}")
            except Exception as e:
                logger.error(f"Error resetting module {module_name}: {e}")

# Initialize on module import
initialize()

# Test the module when run directly
if __name__ == "__main__":
    # Enable debug mode for testing
    CONFIG['debug'] = True
    
    # Example test data
    test_match = {
        'id': 'test123',
        'match_id': 'test123',
        'home_team': 'Team A',
        'away_team': 'Team B',
        'competition': 'Test League',
        'home_score': 1,
        'away_score': 0,
        'status_id': 4,
        'status_description': 'Second Half'
    }
    
    # Process the match
    process_match(test_match)
    
    # Create a simple ThreeOU.py file for testing if it doesn't exist
    threeou_path = os.path.join(CONFIG['alert_modules_dir'], 'ThreeOU.py')
    if os.path.exists(threeou_path) and os.path.getsize(threeou_path) == 0:
        print("Creating sample ThreeOU.py for testing...")
        sample_code = '''
#!/usr/bin/env python3
"""Three Over/Under Alert Module

This module detects matches with an over/under line of 3.0 or higher.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger('sports_alerts.three_ou')

def process_match_data(match_data, previous_data=None):
    """Check if a match has an over/under line of 3.0 or higher.
    
    Args:
        match_data: Current match data
        previous_data: Previous match data (optional)
        
    Returns:
        Alert data dict or None if no alert
    """
    # Extract the over/under line
    ou_line = match_data.get('ou_handicap')
    match_id = match_data.get('id', match_data.get('match_id', 'unknown'))
    
    # Skip if no line available
    if not ou_line:
        return None
    
    # Convert to float if it's a string
    try:
        if isinstance(ou_line, str):
            ou_line = float(ou_line)
    except (ValueError, TypeError):
        return None
    
    # Check if line is 3.0 or higher
    if ou_line >= 3.0:
        return {
            'alert_type': 'three_ou',
            'match_id': match_id,
            'title': '3+ Over/Under Line',
            'message': f'Match has an over/under line of {ou_line}',
            'teams': f"{match_data.get('home_team', 'Unknown')} vs {match_data.get('away_team', 'Unknown')}",
            'competition': match_data.get('competition', 'Unknown'),
            'dedup_key': f'three_ou_{match_id}_{ou_line}'
        }
    
    return None
'''
        with open(threeou_path, 'w') as f:
            f.write(sample_code)
        print("Sample ThreeOU.py created. Run again to test.")
        # Re-initialize to load the new module
        initialize()
        process_match(test_match)
