# SERVER-TEL-STATUS: Comprehensive Guide

This document serves as a comprehensive guide to the Sports Bot's server configuration, Telegram notification system, and status monitoring capabilities. It combines information from separate guides and includes the most recent changes to ensure proper operation.

## Table of Contents

1. [Critical Requirements](#critical-requirements)
2. [Supervisor Configuration](#supervisor-configuration)
3. [Telegram Notification System](#telegram-notification-system)
4. [Status Monitoring](#status-monitoring)
5. [Troubleshooting](#troubleshooting)
6. [Common Commands](#common-commands)

---

## Critical Requirements

### Execution Method
The sports bot **MUST** be executed directly using:
```bash
python3 live.py
```

**NEVER** use:
- Systemd services
- Python module execution (-m flag)

**WHY**: The Telegram notification system depends on direct execution to function properly.

### Import Structure
When using the Telegram notification system from live.py, always use:
```python
from telegram import send_message, send_alert, send_match_alert, send_system_alert
```

**NOT**:
```python
from football.telegram import ...
```

This is because live.py is run directly from the football directory.

### Directory Structure
Proper directory structure is essential:
```
/root/CascadeProjects/sports_bot/
└── football/
    ├── live.py
    ├── telegram/
    │   ├── __init__.py
    │   └── notifier.py
    └── … other files …
```

---

## Supervisor Configuration

### Installation and Setup

1. **Create livepy.conf file**
   ```bash
   sudo nano /etc/supervisor/conf.d/livepy.conf
   ```

2. **Configuration content**
   ```ini
   [program:livepy]
   directory=/root/CascadeProjects/sports_bot/football
   command=/usr/bin/python3 live.py
   autostart=true
   autorestart=true
   stdout_logfile=/var/log/livepy.out.log
   stderr_logfile=/var/log/livepy.err.log
   environment=TZ="America/New_York"
   user=root
   ```

3. **Apply configuration**
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   ```

### Legacy Cleanup

Before using Supervisor, clean up any previous implementations:

- **Remove systemd services**
  ```bash
  sudo systemctl stop sportsbot.service sportsbot-master.service
  sudo systemctl disable sportsbot.service sportsbot-master.service
  sudo mv /etc/systemd/system/sportsbot.service /etc/systemd/system/sportsbot.service.bak
  sudo mv /etc/systemd/system/sportsbot-master.service /etc/systemd/system/sportsbot-master.service.bak
  sudo systemctl daemon-reload
  ```

- **Remove cron entries**
  ```bash
  # Replace with environment settings only
  cat << 'EOF' | sudo crontab -
  PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
  TZ=America/New_York
  EOF
  ```

- **Clear stale files**
  ```bash
  sudo rm /root/CascadeProjects/sports_bot/football/live.lock
  sudo rm /opt/sportsbot_wrapper.sh.bak
  ```

### Benefits of Supervisor

- **Direct Python Execution**: Maintains proper Telegram functionality
- **Automatic Startup**: No need for cron jobs
- **Fault Tolerance**: Auto-restarts on crash
- **Enhanced Logging**: Separate stdout and stderr logs

---

## Telegram Notification System

### Core Functions

The centralized Telegram notification system provides four main functions:

1. **send_message()** - Basic message with no special formatting
2. **send_alert()** - Important alerts with appropriate icons
3. **send_match_alert()** - Match-specific notifications
4. **send_system_alert()** - System status and operational alerts

### Usage Examples

```python
# Import the notification functions
from telegram import send_message, send_alert, send_match_alert, send_system_alert

# Basic message
send_message("Data updated successfully")

# Important alert
send_alert("API rate limit reached. Waiting 5 minutes before retry.")

# Match-specific alert
send_match_alert("Goal scored!", 
                match_id="abc123", 
                teams="Team A vs Team B", 
                score="1-0")

# System alerts by type
send_system_alert("Sports bot is starting", alert_type="startup")  # 🟢
send_system_alert("Sports bot is stopping", alert_type="shutdown") # 🔴
send_system_alert("Current system status...", alert_type="status") # 📡
```

### Alert Types and Icons

| Alert Type | Icon | Description |
|------------|------|-------------|
| startup    | 🟢   | System starting |
| shutdown   | 🔴   | System stopping |
| error      | ⚠️   | Error condition |
| status     | 📡   | Status update |
| match      | ⚽   | General match alert |
| goal       | 🥅   | Goal scored |
| odds       | 📊   | Odds update |
| warning    | ⚠️   | Warning condition |
| default    | 🔔   | Default alert |

---

## Status Monitoring

### Automatic Status Alerts

The system automatically sends Telegram alerts for key events:

1. **Startup** - 🟢 SYSTEM STARTING (when the bot starts)
2. **Shutdown** - 🔴 SYSTEM STOPPING (when the bot stops)
3. **Status Reports** - 📡 STATUS REPORT (when requested via Telegram)

### Telegram Commands

Monitor and interact with the system remotely:

| Command | Description |
|---------|-------------|
| `/status` | Shows current system status and uptime |
| `/history` | Shows recent uptime history (last 10 events) |
| `/help` | Lists all available commands |

### Monitoring via Logs

All system output is captured to log files:

```bash
# View live output
sudo tail -f /var/log/livepy.out.log

# View error log
sudo tail -f /var/log/livepy.err.log
```

---

## Troubleshooting

### Lock File Issues

If the bot fails to start due to a lock file:

```bash
# Check if lock file exists
ls -la /root/CascadeProjects/sports_bot/football/live.lock

# Remove lock file (only if bot is not actually running)
rm -f /root/CascadeProjects/sports_bot/football/live.lock

# Restart the service
sudo supervisorctl restart livepy
```

### Import Errors

If seeing "ModuleNotFoundError: No module named 'football'" or similar errors:

1. Ensure you're importing from the local path:
   ```python
   from telegram import send_message, send_alert, send_match_alert, send_system_alert
   ```

2. Verify the Supervisor configuration is using the proper directory:
   ```ini
   directory=/root/CascadeProjects/sports_bot/football
   command=/usr/bin/python3 live.py
   ```

### Telegram Not Working

If Telegram notifications aren't sending:

1. Check the error log:
   ```bash
   sudo tail -n 50 /var/log/livepy.err.log
   ```

2. Verify the import statement in live.py:
   ```python
   from telegram import send_message, send_alert, send_match_alert, send_system_alert
   ```

3. Ensure the notification module contains the current token and chat ID

---

## Common Commands

### Supervisor Management

```bash
# Check status
sudo supervisorctl status livepy

# Stop the bot
sudo supervisorctl stop livepy

# Start the bot
sudo supervisorctl start livepy

# Restart the bot
sudo supervisorctl restart livepy
```

### Log Viewing

```bash
# View standard output logs
sudo tail -f /var/log/livepy.out.log

# View error logs
sudo tail -f /var/log/livepy.err.log
```

### Testing Notifications

1. **Startup Alert**: 
   ```bash
   sudo supervisorctl restart livepy
   # Should receive 🟢 SYSTEM STARTING notification
   ```

2. **Status Command**:
   Send `/status` in Telegram
   # Should receive status report

3. **Shutdown Alert**:
   ```bash
   sudo supervisorctl stop livepy
   # Should receive 🔴 SYSTEM STOPPING notification
   ```
