# Football Monitoring System - Project Structure

This document explains the overall structure and flow of the Football Monitoring System, providing a high-level overview of how components interact.

## Directory Structure

```
football/
├── 3start.sh               # Shortcut to 3+ total log management
├── main_log.sh             # Shortcut to Main Log management
├── alerts/                 # Alert processing system
│   └── log_alerts/         # Log-based alerting modules
│       ├── __init__.py     # Package initialization
│       ├── base.py         # Base alert functionality
│       ├── scanner.py      # Main log scanning logic
│       └── three_ht_zero.py # Specific alert for 3-0 half-time scores
├── logs/                   # Log storage directory
│   ├── Main_Log.log        # Main log file with all historical data
│   ├── Reversed_Main_Log.log # Main log with newest entries first
│   ├── Main_log_logic.py   # Main Log management system
│   ├── Main_Log/           # Main Log management files
│   │   ├── main_log_pid.txt # PID file for the Main Log processor
│   │   └── main_log_process.log # Process log for Main Log management
│   └── log_alerts/         # Log alert filters
│       └── 3start/         # 3+ Total log system
│           ├── 3_start.log       # Filtered log for high-total matches
│           ├── 3start.sh         # Combined start/view script
│           ├── log_filter.py     # Log filter implementation
│           ├── log_filter_pid.txt # PID file for the log filter
│           ├── match_history.json # Tracks processed matches to prevent duplicates
│           └── log_filter_process.log # Process log for the log filter
├── Readme/                 # Documentation directory
│   ├── ALERTS_README.md    # Information about the alerts system
│   ├── FIELD_MAPPING.md    # API field mapping documentation
│   ├── PROJECT_STRUCTURE.md # This file - overall project structure
│   └── START_STRUCTURE.md   # Detailed info about the startup flow
├── Start_sh/               # Startup and control scripts
│   ├── daemon_launcher.py  # Daemon process manager for 24/7 operation
│   ├── run_live.py         # Robust Python wrapper for live.py
│   └── start_monitor.sh    # Main entry script with various operating modes
├── live.py                 # Core functionality - TheSports API integration
├── live_monitor_wrapper.py # Wrapper with notification capabilities
└── running_pids.txt        # Tracks PIDs of running processes
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
- Daemon operation (`--daemon`)
- Custom refresh intervals (`--interval 60`)

### 2. Process Management Layer

The `start_monitor.sh` script:
1. Creates the appropriate runtime environment (background/foreground/terminal/daemon)
2. Records the process ID in `running_pids.txt`
3. Launches the Python wrapper (`run_live.py`)

For terminal mode, it:
- Creates a tmux/screen session named "football_monitor"
- Allows detaching/reattaching to view output while running in background

For daemon mode, it:
- Launches daemon_launcher.py for persistent background operation
- Provides auto-restart on crashes
- Manages process monitoring and health checks

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

4. **Log Management**
   - Automatically starts 3+ total log filter
   - Automatically starts Main Log management system
   - Ensures all logging components work together

### 4. Log Management Systems

The system has two specialized log management components:

1. **3+ Total Log System (3start.sh)**
   - Monitors Main_Log.log for matches with Over/Under line ≥ 3.0
   - Creates filtered log (3_start.log) with newest entries at the top
   - Prevents duplicate entries
   - Provides convenient viewing commands

2. **Main Log Management System (main_log.sh)**
   - Monitors Main_Log.log in real-time
   - Creates Reversed_Main_Log.log with newest entries at the top
   - Provides advanced viewing options similar to 3start.sh
   - Works alongside the original Main_Log.log without modifying it

### 5. Core Business Logic (live.py)

The `live.py` script (unmodified):
1. Authenticates with TheSports API (user: thenecpt)
2. Fetches live match data every 30 seconds (configurable)
3. Processes match information, including:
   - Match details and scores
   - Team information
   - Competition data
   - Betting odds (processed for specific time frames)
   - Environmental data (with wind speed in m/s and mph)

### 6. Data Flow

```
User Command
    ↓
start_monitor.sh (shell)
    ↓
run_live.py (Python wrapper) ───┬─────► 3start.sh (3+ total log filter)
    ↓                           └─────► Main_log_logic.py (Main Log manager)
live.py (Core API integration)
    ↓
TheSports API ⟷ live.py (JSON data exchange)
    ↓
Processed data → Terminal output + Main_Log.log
    │                                   ↓
    │                    ┌───────────────────────────┐
    │                    │ Main_log_logic.py creates │
    │                    │ Reversed_Main_Log.log     │
    │                    └───────────────────────────┘
    ↓
Log analysis → Alert conditions → Telegram notifications
```

## Startup Options

### Option 1: Daemon Mode (Recommended for 24/7 operation)
```bash
./Start_sh/start_monitor.sh --daemon
```
- Runs as a true daemon process (persists after terminal closes)
- Automatically restarts if it crashes
- Provides heartbeat monitoring and status tracking
- Sends Telegram notifications for important events
- Check status with: `./Start_sh/start_monitor.sh --daemon-status`

### Option 2: Background with Terminal View
```bash
./Start_sh/start_monitor.sh --terminal --background
```
- Starts in background (keeps running if you close the terminal)
- Creates a terminal session you can connect to
- To view: `tmux attach -t football_monitor` or `screen -r football_monitor`
- To detach (leave running): `Ctrl+B then D` (tmux) or `Ctrl+A then D` (screen)

### Option 3: Pure Background
```bash
./Start_sh/start_monitor.sh --background
```
- Runs silently in the background
- No terminal output (logs to Main_Log.log)
- Check status with: `./main_log.sh view` or `./3start.sh view`

### Option 4: Terminal Session Only
```bash
./Start_sh/start_monitor.sh --terminal
```
- Creates a terminal session and attaches to it
- If you close the terminal window, the script keeps running
- Reconnect with `tmux attach -t football_monitor`

### Option 5: Foreground
```bash
./Start_sh/start_monitor.sh
```
- Runs in the current terminal
- Ctrl+C to stop
- Will terminate if you close the terminal

## Log Viewing Commands

The system provides convenient commands for viewing log files:

### View 3+ Total Matches
```bash
./3start.sh view                   # Show recent entries (newest first)
./3start.sh view -n 10             # Show 10 newest entries
./3start.sh view -s "Premier"      # Search for matches with "Premier"
./3start.sh view -f                # Follow log updates in real-time
```

### View Main Log
```bash
./main_log.sh view                 # Show recent entries (newest first)
./main_log.sh view -n 50           # Show 50 newest entries
./main_log.sh view -s "search term" # Search in the log
./main_log.sh view -f              # Follow log updates in real-time
./main_log.sh view -N              # View in normal order (oldest first)
```

## Reliability Features

The system implements a multi-level reliability strategy:

1. **Process Manager Level**
   - Daemon mode with auto-restart functionality
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
- Daemon status updates (when using daemon mode)

Telegram integration uses:
- Token: 7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko
- Chat ID: 6128359776

## Logging System

The system creates several specialized log files:

1. **Main_Log.log**
   - Standard log file with all data (oldest entries first)
   - Records match data, errors, system events, API responses
   - Includes session markers for start/stop events

2. **Reversed_Main_Log.log**
   - Same content as Main_Log.log but with newest entries first
   - Automatically generated and updated by Main_log_logic.py
   - Easier to read when checking recent events

3. **3_start.log**
   - Filtered log containing only matches with O/U line ≥ 3.0
   - Shows newest entries first
   - Prevents duplicate entries
   - Includes match details and betting odds
