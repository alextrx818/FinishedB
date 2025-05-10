#!/usr/bin/env python3
"""
Test the consolidated alert system with sample match data.
This script demonstrates how the alert system analyzes match data
and generates comprehensive alert messages.
"""

import os
import sys
import json
from datetime import datetime

# Add project root to path to allow imports
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../..'))
sys.path.append(project_root)

# Import the consolidated alert system
from football.live_alerts.alert_system import (
    analyze_match_for_alerts, 
    generate_alert_message,
    parse_odds_data,
    parse_environment_data,
    HIGH_OVERUNDER_THRESHOLD
)

def create_sample_match():
    """Create a sample match with comprehensive data for testing"""
    return {
        "id": "8yomo4h3wkj8q0j",
        "home_team": "D. Concepcion",
        "away_team": "Santiago Morning",
        "competition": "Chilean Primera B (Chile)",
        "competition_id": "l965mkyhdgr1ge4",
        "status_id": "2",  # In-play (First Half)
        "minute": "15",
        "home_score": "1",
        "away_score": "0",
        "ht_home_score": "0",
        "ht_away_score": "0",
        "venue": "Estadio Municipal de Concepcion",
        "environment": {
            "weather": {
                "code": "16"  # Sunny
            },
            "temperature": {
                "temp": 22.5  # Celsius
            },
            "humidity": 39,
            "wind": {
                "speed": 1.2,  # m/s
                "direction": "NE"
            }
        },
        "odds": {
            # Money Line odds
            "ML": [
                {
                    "time_of_match": "4",
                    "home_win": "+137",
                    "draw": "+200",
                    "away_win": "+187"
                },
                {
                    "time_of_match": "0",
                    "home_win": "+145",
                    "draw": "+210",
                    "away_win": "+175"
                }
            ],
            # Spread/handicap odds
            "SPREAD": [
                {
                    "time_of_match": "4",
                    "home": "-101",
                    "handicap": "0.25",
                    "away": "-130"
                },
                {
                    "time_of_match": "0",
                    "home": "-105",
                    "handicap": "0.0",
                    "away": "-120"
                }
            ],
            # Over/Under odds with high line value to trigger alert
            "Over/Under": [
                {
                    "time_of_match": "4",
                    "over": "+105",
                    "line": "3.5",
                    "under": "-133"
                },
                {
                    "time_of_match": "0",
                    "over": "+100",
                    "line": "3.0",
                    "under": "-125"
                }
            ]
        },
        "timestamp": datetime.now().strftime("%m/%d/%Y %I:%M:%S %p ET")
    }

def test_parsing_functions():
    """Test the individual parsing functions"""
    print("\n===== TESTING INDIVIDUAL PARSING FUNCTIONS =====\n")
    
    match_data = create_sample_match()
    
    # Test odds parsing
    odds_data = parse_odds_data(match_data)
    print("ODDS PARSING RESULT:")
    print(f"Has ML odds: {odds_data['has_ml']}")
    print(f"Has Spread odds: {odds_data['has_spread']}")
    print(f"Has Over/Under odds: {odds_data['has_ou']}")
    
    # Check for high over/under line
    high_ou_found = False
    for minute, values in odds_data["ou_values"].items():
        line = values.get("line", "0")
        try:
            line_float = float(line)
            if line_float >= HIGH_OVERUNDER_THRESHOLD:
                high_ou_found = True
                print(f"\nHIGH OVER/UNDER DETECTED: {line_float} (threshold: {HIGH_OVERUNDER_THRESHOLD})")
                print(f"Minute: {minute}, Over: {values.get('over')}, Under: {values.get('under')}")
                break
        except (ValueError, TypeError):
            pass
    
    if not high_ou_found:
        print("\nNo high over/under line detected.")
    
    # Test environment parsing
    env_data = parse_environment_data(match_data)
    print("\nENVIRONMENT PARSING RESULT:")
    print(f"Weather: {env_data.get('weather')}")
    print(f"Temperature: {env_data.get('temperature_c')}°C / {env_data.get('temperature_f')}°F")
    print(f"Humidity: {env_data.get('humidity')}%")
    print(f"Wind Speed: {env_data.get('wind_speed_ms')}m/s ({env_data.get('wind_speed_mph')} mph)")

def test_alert_analysis():
    """Test the full alert analysis pipeline"""
    print("\n===== TESTING FULL ALERT ANALYSIS =====\n")
    
    match_data = create_sample_match()
    
    # Run match through alert analysis
    alert_analysis = analyze_match_for_alerts(match_data)
    
    # Print alert analysis summary
    print("ALERT ANALYSIS RESULT:")
    print(f"Should Alert: {alert_analysis['should_alert']}")
    if alert_analysis['alert_reasons']:
        print("Alert Reasons:")
        for reason in alert_analysis['alert_reasons']:
            print(f"  • {reason}")
    else:
        print("No alert reasons found.")
    
    # Generate alert message
    print("\n===== TESTING ALERT MESSAGE GENERATION =====\n")
    alert_message = generate_alert_message(alert_analysis, "odds")
    
    # Print formatted alert message
    print(alert_message)
    
    return alert_analysis, alert_message

if __name__ == "__main__":
    print("Testing the consolidated Alert System...")
    
    # Test individual parsing functions
    test_parsing_functions()
    
    # Test full alert pipeline
    analysis, message = test_alert_analysis()
    
    print("\n===== TESTING DIFFERENT ALERT TYPES =====\n")
    
    # Generate messages with different alert types to show formatting differences
    types = ["odds", "score", "environment", "general"]
    for alert_type in types:
        if alert_type != "odds":  # We already showed the odds type above
            print(f"\nAlert Type: {alert_type.upper()}")
            type_message = generate_alert_message(analysis, alert_type)
            # Just show the first few lines to demonstrate the difference
            print("\n".join(type_message.split("\n")[:5]))
            print("...")
    
    print("\nAlert System tests completed successfully!")
