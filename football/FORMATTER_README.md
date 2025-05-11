# Formatter Documentation

This document preserves the logic and functionality of the Formatter module before its removal.

## Overview

The Formatter module was a utility package for normalizing, formatting, and displaying sports match data. It provided functions for converting odds between different formats, normalizing raw match data, and formatting match summaries for display or alerts.

## Key Components

### Time & Formatting Constants
- Uses Eastern Time Zone (America/New_York) for all timestamps
- Standardized date/time formats for API interaction and display

### Conversion Functions
- `decimal_to_american`: Converts European decimal odds to American format
- `hk_to_american`: Converts Hong Kong odds to American format

### Utility Functions
- `get_eastern_time`: Returns current time in Eastern Time (ET)
- `pick_latest`: Selects odds data preferentially from minutes 4-6, or falls back to the latest available

### Normalization
- `normalize_match_data`: Unpacks raw JSON into named fields and converts odds to American format
  - Processes score data (home/away, halftime/fulltime)
  - Processes odds data (moneyline, spread, over/under)
  - Preserves original data structure while adding normalized fields

### Formatting
- `format_odds_display`: Renders ML, Spread, and Over/Under blocks with formatted odds
  - Prioritizes odds from minutes 4-6 of the match
  - Applies consistent formatting with proper signs (+/-) for American odds
  - Handles edge cases like missing data

- `generate_match_summary_text`: Builds the core summary block from normalized data
  - Includes match metadata (ID, competition, teams)
  - Shows current score and status
  - Displays formatted betting odds
  - Includes environment data (weather, temperature, humidity, wind)

- `format_full_match_block`: Creates complete framed output with headers and separators
  - Adds summary set number and timestamp
  - Includes formatted separator lines

- `format_alert`: Creates specialized alert messages
  - Formats different alert types (e.g., over/under alerts, goal alerts)
  - Maintains consistent styling with match summaries
  - Includes relevant match and odds information

## Data Processing Logic

1. Raw match data is received from external source
2. Data is normalized into a consistent structure
3. Odds are converted to American format for display
4. Data is formatted into human-readable text blocks
5. Display prioritizes odds from minutes 4-6 of matches
6. Special formatting applied for alerts and notifications

This document preserves the knowledge of how the Formatter module processed match data, in case similar functionality needs to be reimplemented in the future.
