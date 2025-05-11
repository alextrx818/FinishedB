# JSON Raw Fetch Utility

## Overview
This utility allows you to fetch raw JSON data directly from TheSports API for football matches. It's designed to help with debugging, data analysis, and understanding the structure of the API responses.

## What it Does
The `fetch_match_json.py` script connects to TheSports API and retrieves:
1. Live match data with detailed information
2. Historical odds data for matches

## How to Use

### Basic Usage
Simply run the script to fetch all live matches and odds data:
```
python3 fetch_match_json.py
```

### Filtering Results
You can filter results by team name and/or competition ID:
```
python3 fetch_match_json.py "Team Name"
python3 fetch_match_json.py "Team Name" "Competition ID"
```

For example:
```
python3 fetch_match_json.py "Arsenal"
python3 fetch_match_json.py "Barcelona" "36"
```

## Features
- Uses the same API credentials as the main sports bot system
- Displays raw API responses in readable JSON format
- Allows filtering matches by:
  - Team name (case-insensitive partial matching)
  - Competition ID
  - Match ID (through code modification)
- Fetches both match details and associated odds data

## Technical Details
- The script imports credentials from the main `live.py` module
- API endpoints used:
  - `https://api.thesports.com/v1/football/match/detail_live`
  - `https://api.thesports.com/v1/football/odds/history`
- Results are pretty-printed with proper indentation for readability

## Use Cases
- Debugging data issues in the main sports bot
- Understanding the structure of TheSports API responses
- Testing API functionality independently from the main application
- Checking if specific matches or competitions are available in the API
