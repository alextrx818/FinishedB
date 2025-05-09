# Football Live Monitoring System

A comprehensive system for monitoring live football matches, capturing odds data, and generating specialized logs for matches meeting specific criteria.

## System Overview

This system fetches live football match data, processes it, and generates various logs for analysis and alerting. It's designed to run continuously and reliably in the background.

## Project Structure

The project is organized as follows:

```
football/
├── live.py                     # Core data processing engine (never modify this file)
│
├── logger/                     # Logging system components
│   ├── main_logger.py          # Logging system that overrides print() function
│   ├── main.logger             # Log file containing all console output
│   ├── __init__.py             # Package initialization
│   └── README.md               # Documentation for the logging system
│
├── logs/                       # Log directory
│   ├── alerts/                 # Specialized log alerts
│
├── telegram/                   # Telegram notification components
│   ├── __init__.py             # Module initialization
│   └── notifier.py             # Centralized notification system
│
├── Start_sh/                   # Startup and monitoring scripts
│   ├── start_monitor.sh        # Main entry point script
│   ├── auto_start.sh           # Automatic continuous execution script
│   └── run_live.py             # Wrapper for live.py with reliability features
│
├── Continuous_Run/             # Continuous execution components
│   ├── run_forever.sh          # Supervisor management script
│   ├── run_with_supervisor.sh  # Script executed by Supervisor
│   └── football-monitor.conf   # Supervisor configuration
│
└── logs/                       # Log directory
    ├── Main_Log.log            # Main log of all matches (source of truth)
    └── Reversed_Main_Log.log   # Same log with newest entries first
```

## Getting Started

### Installation

1. Ensure Python 3.7+ is installed
2. Install required dependencies:
   ```bash
   pip install requests psutil
   ```
3. Install Supervisor (handled automatically by the startup scripts):
   ```bash
   apt-get install -y supervisor
   ```

### Starting and Managing the System

**IMPORTANT:** When referring to "starting the program", "starting the app", or "starting the project", this means using the systemd service:

```bash
# Start the sports bot
sudo systemctl start sportsbot.service

# Check status
sudo systemctl status sportsbot.service

# Restart the sports bot
sudo systemctl restart sportsbot.service

# Stop the sports bot
sudo systemctl stop sportsbot.service
```

The system is configured to:
- Run continuously with automatic updates every 30 seconds
- Display timestamps in Eastern Time (ET)
- Send Telegram notifications on startup, shutdown, or unexpected errors
- Restart automatically if it crashes

**Note:** Never modify live.py as it is the foundation of the sports bot system.

### Alternative Start Methods

```bash
# Start with continuous mode only (no supervisor)
./Start_sh/start_monitor.sh --continuous

# Start using Supervisor manually
./Continuous_Run/run_forever.sh configure
./Continuous_Run/run_forever.sh start
```

### Checking Status

```bash
# Check Supervisor status
supervisorctl status football-monitor

# Check logs
tail -f logs/Main_Log.log
```

### Stopping the System

```bash
supervisorctl stop football-monitor
```

## Logging System

The system uses a comprehensive logging approach with multiple log files:

- **main.logger**: Complete record of all console output from live.py, captured by the `main_logger.py` module
- **Main_Log.log**: Structured record of all matches from the specialized logging system
- **Reversed_Main_Log.log**: Same content with newest matches at the top

### Main Logger

The Main Logger system automatically captures all console output:

1. It intercepts all calls to `print()` in live.py
2. Writes identical output to both the console and the log file
3. Preserves formatting, timestamps, and session markers
4. Initializes automatically when imported

To ensure the Main Logger is active:
- Import it at the top of your main script: `import logger.main_logger`
- All `print()` calls will be automatically captured in `logger/main.logger`

For full documentation of the Main Logger system, see `logger/README.md`.

## Recent Updates (May 2025)

### Process Locking Enhancement
- Added file-based process locking to ensure only one instance of live.py runs at a time
- Prevents 409 Conflict errors with the Telegram API that occur with multiple instances
- Implemented proper error messaging when attempting to start a duplicate instance
- Automatic cleanup of lock files upon process termination

### Telegram Functionality
- Enhanced Telegram listener to properly respond to `/status` commands
- Fixed issues with Telegram bot API conflicts
- Added debug logging for Telegram message processing
- Created test_telegram_status.py for diagnostic testing of Telegram functionality

### Logging System
- Implemented main logger system to capture all console output
- Created `logger/main_logger.py` to override the print function
- Added `logger/main.logger` file to store all console output
- Ensured proper rotation of log files
- Configured logging for debugging and operational tracking
- Protected the logging structure which is essential for the 3start alert system

### Documentation
- Added detailed documentation in the Readme/ directory
- Created separate documentation files for different components
- Updated main README with recent changes and system overview
- Added README for the logging system

## Important Notes

1. `live.py` is the core engine of the system and should not be modified unless absolutely necessary
2. All timestamps in logs use Eastern Time (ET) for consistency
3. The system is designed to run continuously and will automatically restart if any component crashes
4. Never run multiple instances of live.py manually - the process lock will prevent this
5. If you encounter "Another instance is already running" message and are sure no other instance exists, delete the lock file at `/root/CascadeProjects/sports_bot/football/live.lock`
6. The 3start alert system depends on live.py and the main logging system to function properly

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
