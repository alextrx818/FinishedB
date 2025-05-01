# Sports Bot Monitoring System

This document outlines the consolidated monitoring and uptime tracking system for the Sports Bot. All monitoring functionality is now integrated directly into live.py for more efficient and comprehensive system oversight.

## Monitoring Features

### 1. Uptime Tracking

The system automatically logs all significant events related to uptime:

- **Startup events** - When the system starts
- **Shutdown events** - When the system stops (normal or abnormal)
- **Telegram listener** - When the message listening thread starts
- **Signal handling** - When system receives signals (e.g., status requests)

All events include:
- Precise timestamp (Eastern Time)
- Current uptime
- Process ID
- Event details

### 2. Telegram Integration

Monitor and interact with the system remotely using these Telegram commands:

| Command | Description |
|---------|-------------|
| `/status` | Shows current system status and uptime |
| `/history` | Shows recent uptime history (last 10 events) |
| `/help` | Lists all available commands |

### 3. Logging System

All monitoring data is stored in dedicated log files:

- **uptime_history.log** - Complete record of system uptime events
- **errors.log** - Detailed error information with context
- **daily_summary.log** - Daily system performance reports

## How To Use

### Checking System Status

**Via Telegram:**
1. Open Telegram chat with the bot
2. Send `/status` to get current status
3. Send `/history` to view recent uptime events

**Via Server:**
```bash
# Check the uptime history log
tail -f /root/CascadeProjects/sports_bot/football/logs/analysis/uptime_history.log

# Check error log for any issues
tail -f /root/CascadeProjects/sports_bot/football/logs/analysis/errors.log
```

### Monitoring Alerts

The system automatically sends Telegram alerts when:

1. **System starts** - 🚀 LIVE.PY STARTED
2. **System stops** - ⛔ LIVE.PY STOPPED
3. **Status requested** - 📊 LIVE.PY STATUS REPORT

### Service Integration

The monitoring system works seamlessly with systemd for automatic service management:

- **Auto-restart** - Service restarts automatically if it crashes
- **Status tracking** - All restarts are logged in uptime_history.log
- **Notifications** - Alerts sent on unexpected service stops

## Benefits Over Previous Monitoring

The new consolidated monitoring system provides several advantages:

1. **Real-time interaction** - Check status anytime via Telegram
2. **Historical data** - Complete uptime history is preserved
3. **Structured logging** - All data is in JSON format for easy parsing
4. **Zero configuration** - Works automatically without separate scripts
5. **Reduced complexity** - All monitoring in one system instead of separate scripts

## Technical Implementation

All monitoring functionality is implemented directly in live.py through these key components:

- **uptime_logger** - Dedicated logger for uptime events
- **log_uptime_event()** - Records uptime events with timestamps
- **get_uptime_history()** - Retrieves and formats uptime history
- **telegram_listener()** - Processes monitoring commands
- **atexit handler** - Tracks normal shutdowns
- **error_logger** - Captures application errors

This consolidated approach ensures that monitoring is always active when the system is running.
