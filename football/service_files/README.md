# Sports Bot System Service Files

This directory contains important configuration files for the Sports Bot system's systemd services. These files should be used for reference purposes - the active versions are located in `/etc/systemd/system/`.

## Service Files Overview

### 1. sportsbot-master.service
**Purpose**: Master control service that coordinates starting all sports bot components at once
**Location**: `/etc/systemd/system/sportsbot-master.service`
**Dependencies**: sportsbot.service, terminal-display.service
**Management Commands**:
```
systemctl start|stop|restart|status sportsbot-master.service
```

### 2. sportsbot.service
**Purpose**: Main service running live.py (the foundation of the sports bot)
**Location**: `/etc/systemd/system/sportsbot.service`
**Key Components**: Uses sportsbot_wrapper.sh to launch live.py with watchdog support

### 3. terminal-display.service
**Purpose**: Displays live match data from Terminal_Output.log
**Location**: `/etc/systemd/system/terminal-display.service`
**Note**: Follows and displays the log in real-time

### 4. sportsbot_wrapper.sh
**Purpose**: Wrapper script that launches live.py with proper configuration
**Location**: `/opt/sportsbot_wrapper.sh`
**Key Feature**: Includes watchdog functionality to monitor the health of live.py

## System Dependencies

The sports bot system has a specific dependency structure:

1. `live.py` - Core system that fetches data and processes matches
2. Main logging system - Writes match data to Main_Log.log
3. 3start alert system - Monitors the Main_Log.log for matches with Over/Under line ≥ 3.0

## Log Files

The system maintains several log files:
- `/root/CascadeProjects/sports_bot/football/logs/Main_Log.log` - Machine-readable JSON match data
- `/root/CascadeProjects/sports_bot/football/logs/Terminal_Output.log` - Human-readable match display
- `/root/CascadeProjects/sports_bot/football/logs/Fetch_History.log` - API fetch history

## Boot Process

On system start, the following sequence occurs:
1. sportsbot-master.service activates
2. sportsbot.service starts, launching live.py through the wrapper
3. terminal-display.service starts, showing the output from Terminal_Output.log

## Maintenance

To update these configuration files:
1. Edit the files in their system locations (/etc/systemd/system/)
2. Run `systemctl daemon-reload` to apply changes
3. Copy the updated files to this directory for reference
