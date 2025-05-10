#!/usr/bin/env python3
"""
Live Alerts Package

This package contains all components related to live sports alerts, 
including JSON parsing logic, alert criteria definitions, and alert delivery mechanisms.
"""

from .alert_system import (
    # Core analysis functions
    analyze_match_for_alerts,
    generate_alert_message,
    should_deduplicate_alert,
    
    # Data parsing functions
    parse_odds_data,
    parse_score_data,
    parse_environment_data,
    
    # Alert condition checkers
    check_odds_alert_conditions,
    check_score_change,
    check_environment_alert_conditions,
    
    # Helper functions
    get_weather_description,
    format_american_odds,
    decimal_to_american,
    hk_to_american
)

# Package metadata
__version__ = '1.0.0'
