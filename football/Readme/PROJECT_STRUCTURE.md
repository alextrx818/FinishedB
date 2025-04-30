# Football Monitoring System - Project Structure

This document explains the overall structure and flow of the Football Monitoring System, providing a high-level overview of how components interact.

## Directory Structure

```
football/
├── alerts/                  # Alert processing system
│   └── log_alerts/          # Log-based alerting modules
│       ├── __init__.py      # Package initialization
│       ├── base.py          # Base alert functionality
│       ├── scanner.py       # Main log scanning logic
│       └── three_ht_zero.py # Specific alert for 3-0 half-time scores
├── logs/                    # Log storage directory
│   └── Main_Log.log         # Main log file with all historical data
├── Readme/                  # Documentation directory
│   ├── ALERTS_README.md     # Information about the alerts system
│   ├── FIELD_MAPPING.md     # API field mapping documentation
│   ├── PROJECT_STRUCTURE.md # This file - overall project structure
│   └── ...                  # Other documentation files
├── Start_sh/                # Startup and control scripts
│   ├── run_live.py          # Robust Python wrapper for live.py
│   └── start_monitor.sh     # Main entry script with terminal/background options
├── live.py                  # Core functionality - TheSports API integration
├── live_monitor_wrapper.py  # Wrapper with notification capabilities
└── running_pids.txt         # Tracks PIDs of running processes
```

## System Flow

The Football Monitoring System follows a multi-layered architecture for reliability:

### 1. User Entry Point

The system starts with the user running:
```bash
./Start_sh/start_monitor.sh [options]
```

This script provides options for:
- Background operation (`--background`)
- Terminal visibility (`--terminal`)
- Custom refresh intervals (`--interval 60`)

### 2. Process Management Layer

The `start_monitor.sh` script:
1. Creates the appropriate runtime environment (background/foreground/terminal)
2. Records the process ID in `running_pids.txt`
3. Launches the Python wrapper (`run_live.py`)

For terminal mode, it:
- Creates a tmux/screen session named "football_monitor"
- Allows detaching/reattaching to view output while running in background

### 3. Reliability Layer (run_live.py)

The Python wrapper `run_live.py` provides:
1. **Exception Handling**
   - Global exception hook for uncaught errors
   - Telegram notifications for errors
   - Proper logging of all exceptions

2. **Monitoring Systems**
   - Heartbeat pings to external health check service
   - Watchdog to detect stuck processes
   - Activity monitoring with inactivity alerts

3. **Session Management**
   - Log file session markers
   - Startup/shutdown Telegram notifications
   - Clean startup/shutdown processes

### 4. Core Business Logic (live.py)

The `live.py` script (unmodified):
1. Authenticates with TheSports API (user: thenecpt)
2. Fetches live match data every 30 seconds (configurable)
3. Processes match information, including:
   - Match details and scores
   - Team information
   - Competition data
   - Betting odds (processed for specific time frames)
   - Environmental data (with wind speed in m/s and mph)

### 5. Data Flow

```
User Command
    ↓
start_monitor.sh (shell)
    ↓
run_live.py (Python wrapper)
    ↓
live.py (Core API integration)
    ↓
TheSports API ⟷ live.py (JSON data exchange)
    ↓
Processed data → Terminal output + Main_Log.log
    ↓
Log analysis → Alert conditions → Telegram notifications
```

## Startup Options

### Option 1: Background with Terminal View (Recommended)
```bash
./Start_sh/start_monitor.sh --terminal --background
```
- Starts in background (keeps running if you log out)
- Creates a terminal session you can connect to
- To view: `tmux attach -t football_monitor` or `screen -r football_monitor`
- To detach (leave running): `Ctrl+B then D` (tmux) or `Ctrl+A then D` (screen)

### Option 2: Pure Background
```bash
./Start_sh/start_monitor.sh --background
```
- Runs silently in the background
- No terminal output (logs to Main_Log.log)
- Check status with: `tail -f logs/Main_Log.log`

### Option 3: Terminal Session Only
```bash
./Start_sh/start_monitor.sh --terminal
```
- Creates a terminal session and attaches to it
- If you close the terminal window, the script keeps running
- Reconnect with `tmux attach -t football_monitor`

### Option 4: Foreground
```bash
./Start_sh/start_monitor.sh
```
- Runs in the current terminal
- Ctrl+C to stop
- Will terminate if you close the terminal

## Reliability Features

The system implements a 3-level reliability strategy:

1. **Process Manager Level**
   - External process manager (systemd/Supervisor/PM2) can restart the entire system
   - PID tracking for clean process management

2. **Application Level**
   - Exception handling with notifications
   - Session tracking and recovery
   - Telegram alerts for critical errors

3. **Monitoring Level**
   - External heartbeat service integration
   - Watchdog for frozen processes
   - Inactivity detection and alerting

This multi-layered approach ensures the system operates reliably 24/7 with minimal manual intervention.

## Notifications

The system sends Telegram notifications for:
- System startup/shutdown
- Error conditions
- Match alerts based on configurable criteria
- System inactivity

Telegram integration uses:
- Token: 7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko
- Chat ID: 6128359776

## Logging System

All activity is logged to `logs/Main_Log.log`, which preserves the complete history of:
- Match data fetches
- Errors and exceptions
- System starts and stops
- API responses

The log file includes session markers to clearly delineate start/stop events.
