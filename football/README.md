# Football Live Monitoring System

A comprehensive system for monitoring live football matches, capturing odds data, and generating specialized logs for matches meeting specific criteria such as over/under lines.

## System Overview

This system fetches live football match data, processes it, and generates various logs for analysis and alerting. It's designed to run continuously and reliably in the background.

## Project Structure

The project is organized as follows:

```
football/
├── live.py                     # Core data processing engine (never modify this file)
│
├── logs/                       # Log directory
│   ├── alerts/                 # Specialized log alerts
│   │   └── 3Start.py           # System for tracking matches with O/U line ≥ 3.0
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
    ├── Reversed_Main_Log.log   # Same log with newest entries first
    └── log_alerts/             # Specialized log filters
        └── 3start/             # Over/Under 3.0 filter
            ├── 3_start.log     # Log of matches with O/U line ≥ 3.0
            └── log_filter.py   # Filter script
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
tail -f logs/log_alerts/3start/3_start.log
```

### Stopping the System

```bash
supervisorctl stop football-monitor
```

## Log Files

- **Main_Log.log**: Complete record of all matches
- **Reversed_Main_Log.log**: Same content with newest matches at the top
- **3_start.log**: Specialized log of matches with Over/Under line of 3.0 or higher

## Important Notes

1. `live.py` is the core engine of the system and should not be modified unless absolutely necessary
2. All timestamps in logs use Eastern Time (ET) for consistency
3. The system is designed to run continuously and will automatically restart if any component crashes
