# Live Sports Alerts System

## Overview

The Live Sports Alerts System monitors match data for specific conditions and triggers alerts via Telegram when those conditions are met. This is separate from the system alerts functionality and focuses exclusively on sports/match conditions.

## System Architecture

The alerts system uses a modular, plugin-based architecture:

1. **Central Coordinator**: `alert_system.py` - Manages alert modules and routes match data
2. **Alert Modules**: Individual `*_alert.py` files that each focus on a specific alert condition
3. **Alert Flow**: live.py → alert_system.py → individual alert modules → Telegram notification

## Alert Modules

Each alert module follows a standard pattern:

| Module | Description | Alert Condition |
|--------|-------------|----------------|
| `three_overunder_alert.py` | Monitors matches with higher point totals | Over/Under line ≥ 3.0 |
| `high_overunder_alert.py` | Checks for extreme over/under lines | Over/Under line > HIGH_OVERUNDER_THRESHOLD |
| `missing_odds_alert.py` | Detects when odds data is incomplete | Missing key odds components |
| `halftime_alert.py` | Alerts on halftime status transitions | Match enters halftime (Status ID: 3) |
| `consolidated_env_alert.py` | Batches missing environment data alerts | Consolidates alerts over 30 minutes |

### Consolidated Environment Alerts

The `consolidated_env_alert.py` module provides a specialized handling of missing environment data alerts:

- **Batching**: Instead of sending an individual alert for each match with missing environment data, this module collects all such matches over a 30-minute period
- **Consolidated Notification**: At the end of each 30-minute window, a single notification is sent containing a list of all affected matches
- **Reduced Noise**: This significantly reduces notification fatigue, especially during periods where many matches might be missing environment data
- **Complete Information**: The consolidated alert includes match names, competitions, and IDs for all affected matches

This approach maintains the separation between sports alerts and system alerts while ensuring you still get all relevant information in a more organized, less intrusive manner.

## Creating New Alert Modules

To create a new alert module:

1. Create a new file named `[alert_name]_alert.py` in the `live_alerts` directory
2. Implement the required `process_match_data(match_data, previous_data=None)` function
3. Return `True` when alert should trigger, `False` otherwise
4. Use the `should_deduplicate_alert()` utility to avoid duplicate alerts

### Template for New Alert Modules

```python
#!/usr/bin/env python3
"""
[Alert Name] Alert

This sports alert module monitors matches for [specific condition].
"""

import os
from typing import Dict, Any, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Track matches we've already alerted on to avoid duplicate alerts
alerted_matches = {}

# Import utilities from the consolidated alert system
try:
    from football.live_alerts.alert_system import should_deduplicate_alert
except ImportError as e:
    print(f"Error importing alert_system utilities: {e}")

def process_match_data(match_data: Dict[str, Any], previous_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Process a match to check for [alert condition].
    
    Args:
        match_data: The current match data dictionary
        previous_data: Previous match data for comparison (optional)
        
    Returns:
        True if an alert should be triggered, False otherwise
    """
    # Extract match ID and basic info for logging
    match_id = match_data.get('id', 'unknown')
    
    # Extract team names for logging
    home_team = match_data.get('home_team', 'Home Team')
    away_team = match_data.get('away_team', 'Away Team')
    
    # Implement your alert condition logic here
    # ...
    
    # Example alert condition check
    alert_condition_met = False  # Replace with actual condition check
    
    if alert_condition_met:
        # Check if we've already alerted on this match for this condition
        alert_key = "your_alert_type"
        alert_details = ["Detail 1", "Detail 2"] # Relevant details for deduplication
        
        if should_deduplicate_alert(match_id, alert_key, alert_details, alerted_matches):
            return False
        
        # Return True to indicate this alert was triggered
        return True
    else:
        # Condition not met
        return False

def reset_alert_cache():
    """Reset the alert cache to prevent memory leaks in long-running processes"""
    global alerted_matches
    alerted_matches = {}
    return True
```

## Alert System Utilities

The main `alert_system.py` provides utilities for alert modules:

- `should_deduplicate_alert()`: Prevents duplicate alerts for the same condition
- `parse_odds_data()`: Extracts and formats betting odds
- `parse_environment_data()`: Extracts weather and environment info
- `parse_score_data()`: Handles score parsing and differencing

## Alerting via Telegram

Alerts are sent via Telegram through a specific flow:

1. Alert modules return `True` when a condition is met
2. `alert_system.py` collects these results
3. `live.py` handles the actual sending of alerts through its Telegram integration

## Best Practices

1. **Modularity**: Each alert type should be in its own module
2. **Statelessness**: Alert modules should maintain minimal state
3. **Deduplication**: Always use the deduplication utilities to prevent alert spam
4. **Error Handling**: Add proper error handling to prevent crashes
5. **Naming Convention**: Always use the format `name_alert.py` for alert module files
6. **Documentation**: Include a docstring explaining the alert condition
7. **Threshold Configuration**: Define configurable thresholds at the top of your modules

## Troubleshooting

- **Missing Alerts**: Check the return value from `process_match_data()`
- **Duplicate Alerts**: Ensure you're using the deduplication utility properly
- **Alert Module Not Loading**: Verify the file follows naming convention `*_alert.py`
- **Runtime Errors**: Look for logged errors from the alert system

## Running the System

The alert system is automatically initialized when the sports bot starts:

```bash
python3 live.py
```

The system will automatically discover and load all alert modules that follow the naming pattern `*_alert.py`.
