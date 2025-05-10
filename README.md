# Sports Bot - Football Match Tracker

A real-time football (soccer) match tracking system that monitors live matches and provides alerts, statistics, and analysis.

## Recent Updates (May 10, 2025)

### 1. Comprehensive Diagnostic System
Implemented a complete diagnostic test suite that verifies all components of the Sports Bot system:
- API connectivity tests for thesports.com API endpoints
- Database connectivity and query validation tests
- Telegram integration tests for alert functionality
- Logger system tests for file existence and rotation
- Integration tests for match data monitoring

The diagnostic tool can be run with:
```
python3 tools/diagnostics.py [--verbose] [--send-alerts]
```

Diagnostic results are displayed in the terminal and saved as JSON in the `/logs/diagnostics/` directory.

### 2. Match Data Monitor Integration
Integrated a real-time match data monitor that:
- Continuously watches the main logger output for missing match data
- Detects issues with environment data, odds, and other match details
- Sends alert notifications through Telegram when problems are detected
- Implements alert deduplication to prevent repeated alerts for the same condition

### 3. Logger System Improvements
Enhanced the logger system with multiple improvements:
- Implemented log rotation using TimedRotatingFileHandler
- Files now rotate at midnight with 30-day retention period
- Synchronized output formatting between terminal and log files
- Fixed console output duplication issues
- Added proper spacing and formatting for better readability
- Ensured diagnostic messages appear in both console and log file

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
- Log file rotation uses Python's TimedRotatingFileHandler with 30-day history retention
- Output formatting is synchronized between terminal and log files
- Performance optimized through selective logging and reduced serialization overhead

## Technical Structure

- `live.py`: Main match processing system (core component - never modify without authorization)
- `telegram/`: Telegram notification system for alerts and messages
  - `match_data_monitor.py`: Real-time monitor for missing match data detection
- `logger/`: Logging subsystem
  - `main_logger.py`: Customized logging system with rotation
  - `db_api.py`: Database logging interface
  - `UNIFIED_LOGGER_STANDARDS.md`: Logging standards documentation
- `tools/`: Support tools and utilities
  - `diagnostics.py`: Comprehensive diagnostic test suite

## Change Documentation Requirements

**CRITICAL**: Any changes to this system MUST include detailed documentation of:

1. Exact lines added, modified, and deleted (line-by-line changes)
2. Clear rationale explaining why each change was necessary
3. Assessment of potential system impacts
4. Simple natural language summary of changes

This documentation must accompany ALL changes, no matter how minor, especially for core files:
- `live.py` - Foundation of the system, requires extreme caution when modifying
- `logger/main_logger.py` - Critical to logging functionality
- Any supporting files these components depend on

When documenting changes, use the following format:

```markdown
## [File Name] Changes

### New Lines Added (Not Replacements)
```python
# Added code
```

### Lines Modified (Changed Functionality)
Before → After
```python
# Before
# After
```

### Lines Replaced (Deleted and Added as Replacements)
DELETED → REPLACEMENT
```python
# Deleted code
# Replacement code
```

### Lines Deleted Without Replacement
```python
# Deleted code
```

### Rationale
[Explanation of why changes were made]

### Potential Impact
[How these changes may affect the system]
```

Failure to document changes properly can lead to system instability and make future maintenance impossible.
