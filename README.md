# Sports Bot - Football Match Tracker

A real-time football (soccer) match tracking system that monitors live matches and provides alerts, statistics, and analysis.

## Recent Fixes (May 4, 2025)

### 1. Team Name Resolution Fix
Fixed issue where team names and competition information were showing as "Unknown" in match summaries. The problem was that team IDs were being extracted from the live matches API response, but they actually exist in the match details response. Modified the data flow to:
- First fetch live matches to get match IDs
- Then fetch match details to extract team and competition IDs
- Finally fetch team and competition info using those IDs

### 2. Output Duplication Fix
Fixed issue where terminal output was being duplicated. The problem was redundant console output:
- The `new_print()` function was already outputting to the terminal
- The logger also had a console handler sending logs to the terminal again
- Removed the redundant console handler from the logger setup

## Features

- Real-time tracking of live football matches
- Match details with team names, scores, and status
- Betting odds information 
- Environment data (weather, humidity, wind)
- Match summary logging
- Telegram notifications

## API

The system uses the TheSports API to fetch football match data.

## Usage

```
cd /root/CascadeProjects/sports_bot/football
python3 live.py
```

## Logging

- Logs are stored in `/football/logger/main.logger`
- Daily logs are rotated at midnight with date suffix (e.g., `main.logger.2025-05-04`)
- Logs contain match summaries with team names, competition, score, and betting information

## Technical Structure

- `live.py`: Main match processing system
- `alerts.py`: Telegram notification system
- `logger/main_logger.py`: Customized logging system
- `logger/UNIFIED_LOGGER_STANDARDS.md`: Logging standards documentation
