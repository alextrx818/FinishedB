# Football Live Data Script (live.py)

## Overview
This script fetches and displays live football match data including match details, team information, competition data, and betting odds from TheSports API. It supports parallel processing for optimized performance and implements specific filtering rules for different types of odds.

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `https://api.thesports.com/v1/football/match/detail_live` | Fetches live match data |
| `https://api.thesports.com/v1/football/match/recent/list` | Fetches detailed match information |
| `https://api.thesports.com/v1/football/team/additional/list` | Fetches team information |
| `https://api.thesports.com/v1/football/competition/additional/list` | Fetches competition information |
| `https://api.thesports.com/v1/football/country/list` | Fetches country information |
| `https://api.thesports.com/v1/football/odds/history` | Fetches odds history data |

## API Credentials
- User: `thenecpt`
- Secret: `0c55322e8e196d6ef9066fa4252cf386`

## Odds Filtering Rules

All odds types (European, Asia Handicap, and Over/Under) are filtered to only include data from match minutes 4-6. If no data is available from these minutes, the script will fall back to using other available data.

### European (Money Line) Odds
- **Source field**: `eu` in odds data
- **Default bookmaker**: Bookmaker ID 2
- **Priority time window**: Minutes 4-6 of the match
- **Conversion**: Decimal odds to American odds
- **Format**: Standard American odds with +/- signs (e.g., `-150`, `+240`)

### Asia Handicap (SPREAD) Odds
- **Source field**: `asia` in odds data
- **Priority time window**: Minutes 4-6 of the match
- **Conversion**: Hong Kong odds to American odds
- **Format**: Standard American odds with +/- signs (e.g., `-110`, `+120`)

### Big Small (Over/Under) Odds
- **Source field**: `bs` in odds data
- **Priority time window**: Minutes 4-6 of the match
- **Conversion**: Hong Kong odds to American odds
- **Format**: Standard American odds with +/- signs (e.g., `-110`, `+120`)

## Odds Conversion Formulas

### Decimal to American Odds (European/Money Line)
- For decimal odds ≥ 2.0: `(decimal - 1) * 100` (with + sign)
- For decimal odds < 2.0: `-100 / (decimal - 1)` (with - sign)

### Hong Kong to American Odds (SPREAD and Over/Under)
- For Hong Kong odds ≥ 1.0: `odds * 100` (with + sign)
- For Hong Kong odds < 1.0: `-100 / odds` (with - sign)

## Score Data Extraction
Updated: 2025-04-30

The script now extracts score data directly from the detailed structure in the `detail_live` API response. The score data is provided in a nested array structure:

```
score:[
  0:"dn1m1ghlv62vmoe"  // Match ID
  1:2                  // Unknown field
  2:[                  // Home team scores array
    0:1                // Current home score (may include text like "(Home Live)")
    1:1                // Half-time home score (may include text)
    2:0                // Other score fields
    ...
  ]
  3:[                  // Away team scores array
    0:0                // Current away score (may include text like "(Away Live Score)")
    1:0                // Half-time away score (may include text)
    2:0                // Other score fields
    ...
  ]
]
```

The script parses this structure to extract both current and half-time scores, handling cases where the API might include descriptive text along with numeric scores.

## Output Display
The script outputs a formatted summary for each match including:
- Match teams and score
- Competition name and country
- Match environment (weather, temperature, wind, humidity)
- Betting odds in American format with proper +/- signs for:
  - SPREAD (Asia Handicap)
  - ML (Money Line)
  - Over/Under

## Command Line Usage
```bash
# Run once (default mode)
python football/live.py

# Run in continuous mode, updating every 30 seconds
python football/live.py --continuous

# Run in continuous mode with custom interval (e.g., 45 seconds)
python football/live.py --continuous --interval 45

# Short command options are also available
python football/live.py -c -i 30
```

### Continuous Monitoring Mode
The script supports 24/7 continuous monitoring with automatic refreshing. When run with the `--continuous` flag, it will:

1. Fetch and display all live matches
2. Wait for the specified interval (default: 30 seconds)
3. Show a timestamp for when the next update will occur
4. Refresh the data and display updated match information
5. Repeat until manually stopped with Ctrl+C

This mode is ideal for keeping track of live matches over extended periods. The script displays timestamps with each update, making it easy to track when data was last refreshed.

## Alerts System

The project includes a comprehensive alerts system that monitors live matches and sends notifications via Telegram when specific criteria are met. Full documentation is available in:

- [ALERTS_README.md](./ALERTS_README.md) - General alerts documentation
- [MATCH_START_ALERTS_README.md](./MATCH_START_ALERTS_README.md) - Match start alert documentation
- [STARTUP_README.md](./STARTUP_README.md) - How to run the system 24/7

### Available Alert Types

| Alert Type | Description | File |
|------------|-------------|------|
| 3HT0 | Alerts when matches with Over/Under line ≥3.0 reach halftime with 0-0 score | alerts/ThreeHtZero.py |
| 3 O/U Started | Alerts when a match starts with Over/Under line ≥3.0 | alerts/match_start/three_ou.py |

### Running the Alerts System

```bash
# Run as a daemon process (background)
bash football/start_24_7_monitoring.sh
```

## Daily Log Fetcher

A companion script (`daily_log_fetcher.py`) is included to create a continuous log of all live match data for analysis purposes. This tool runs `live.py` at regular intervals (default: 30 seconds) and logs the complete output to daily log files.

### Starting the Daily Logger

```bash
# Start the daily logger in the background
bash football/start_daily_logging.sh
```

### Viewing Daily Logs

```bash
# View today's logs
cat football/logs/football_fetches_$(date +%Y-%m-%d).log

# Use the log viewer tool
python3 football/view_daily_logs.py

# View logs for a specific date
python3 football/view_daily_logs.py --date 2025-04-28

# View detailed fetch information
python3 football/view_daily_logs.py --detailed

# List all available log files
python3 football/view_daily_logs.py --list
```

### Stopping the Daily Logger

```bash
# Stop the daily logger
bash football/stop_daily_logging.sh
```

### Log Features

- Creates a new log file each day (format: `football_fetches_YYYY-MM-DD.log`)
- Records timestamp for each fetch
- Captures match details, odds lines, and status information
- Provides end-of-day summary statistics
- Analyzes matches by competition, status, and O/U line
- Tracks unique matches seen throughout the day
- All logs are stored in the `football/logs/` directory

## Performance Optimizations
- Uses concurrent.futures.ThreadPoolExecutor for parallel API requests
- Implements LRU caching with functools.lru_cache to minimize duplicate API calls
- Uses a single session for all HTTP requests to improve connection efficiency

## Error Handling
- Gracefully handles missing or invalid data fields
- Provides detailed debug output for odds conversion
- Implements proper exception handling and diagnostic information

## Match Status Codes
The script maps numeric status IDs from the API to human-readable descriptions:

| Status ID | Description |
|-----------|-------------|
| 1 | Not started |
| 2 | First half |
| 3 | Half-time break |
| 4 | Second half |
| 5 | Extra time |
| 6 | Penalty shootout |
| 7 | Finished |
| 8 | Finished |
| 9 | Postponed |
| 10 | Canceled |
| 11 | To be announced |
| 12 | Interrupted |
| 13 | Abandoned |
| 14 | Suspended |

These status codes are fetched from the `https://api.thesports.com/v1/football/match/recent/list` endpoint and displayed in the match summary section of each match.

## Recent Changes
Last updated: 2025-04-30

### Score Data Improvements
The system was enhanced to extract more accurate score data from the nested array structure in the `detail_live` API response. Previously, the system was using the simpler `home_score`, `away_score`, `home_score_half`, and `away_score_half` fields, which occasionally had issues with accuracy.

Now, the system directly parses the more detailed `score` array structure, which contains both current and half-time scores for home and away teams. This approach:

1. Ensures more accurate score reporting
2. Handles special cases where scores may include descriptive text
3. Properly extracts half-time scores even when they're not available in the simpler fields
4. Updates every 30 seconds to keep score data current

This change improved the system's reliability for score reporting, especially for in-progress matches.

## Field Mapping Reference
Last updated: 2025-04-30

## ⚠️ IMPORTANT NOTE ⚠️
**live.py is the foundation of this project and must NOT be modified without explicit permission from the project owner. This file serves as the core data processing engine and any unauthorized changes could disrupt the entire system.**

### Match Summary Section

| Displayed Field | API Endpoint | JSON Field | Notes |
|-----------------|--------------|------------|-------|
| Competition ID | match/detail_live | `competition_id` | Used to fetch competition details |
| Competition Name | competition/additional/list | `results[0].name` | Fetched using competition ID |
| Competition Country | country/list | `results[X].name` | X is the country ID from competition info |
| Match Teams | team/additional/list | `results[0].name` | Fetched for both home and away team IDs |
| Score (Current) | match/detail_live | `score[2][0]`, `score[3][0]` | Home & away current scores |
| Score (Half-time) | match/detail_live | `score[2][1]`, `score[3][1]` | Home & away half-time scores |
| Status | match/recent/list | `status_id` | Mapped to readable description (see status codes) |
| Match Time | match/recent/list | `match_time` | Unix timestamp of match start |
| Environment Data | match/recent/list | `environment` | Contains weather, temperature, wind, humidity |

### Betting Odds Section

| Displayed Field | API Endpoint | JSON Field | Notes |
|-----------------|--------------|------------|-------|
| ML (Money Line) | odds/history | `results[X].eu.book_2` | X is match ID, bookmaker ID is 2 |
| SPREAD (Asia Handicap) | odds/history | `results[X].asia` | Converted to American odds format |
| Over/Under | odds/history | `results[X].bs` | Converted to American odds format |
| Time | odds/history | `results[X].time_of_match` | Minutes into the match when odds were recorded |

### Environment Section

| Displayed Field | API Endpoint | JSON Field | Notes |
|-----------------|--------------|------------|-------|
| Weather | match/recent/list | `environment.weather` | Numeric code converted to description |
| Temperature | match/recent/list | `environment.temperature` | Converted from °C to °F |
| Wind | match/recent/list | `environment.wind` | Converted from m/s to mph |
| Humidity | match/recent/list | `environment.humidity` | Percentage value |
