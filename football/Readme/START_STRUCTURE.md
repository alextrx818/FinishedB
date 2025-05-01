# Football Monitor - Startup Structure

This document explains the startup flow and component structure of the Football Monitoring System.

## Startup Flow

The system uses a hierarchical startup process to ensure all components work together properly:

```
start_monitor.sh
    │
    ├─► run_live.py (wrapper with reliability features)
    │       │
    │       ├─► live.py (core API functionality)
    │       │
    │       └─► Exception handling, Telegram alerts, Heartbeat monitoring
    │
    ├─► 3start.sh (3+ total log management)
    │       │
    │       └─► log_filter.py (filters high-total matches)
    │
    ├─► Main_log_logic.py (Main Log management)
    │       │
    │       └─► Creates Reversed_Main_Log.log (newest entries first)
    │
    └─► daemon_launcher.py (if daemon mode)
            │
            └─► Auto-restart, persistent background operation
```

### 1. Primary Entry Point: start_monitor.sh

The shell script [./Start_sh/start_monitor.sh](../Start_sh/start_monitor.sh) is the main switch that launches everything:

```bash
# Start in terminal mode with background operation:
./Start_sh/start_monitor.sh --terminal --background

# Start as a persistent daemon (runs in background, auto-restarts):
./Start_sh/start_monitor.sh --daemon

# Other options:
./Start_sh/start_monitor.sh              # Foreground mode
./Start_sh/start_monitor.sh --background # Background mode without terminal
./Start_sh/start_monitor.sh --terminal   # Terminal mode that attaches to session
./Start_sh/start_monitor.sh --daemon-stop    # Stop the daemon
./Start_sh/start_monitor.sh --daemon-status  # Check daemon status
./Start_sh/start_monitor.sh --daemon-restart # Restart the daemon
```

This script:
- Takes command-line arguments for different operating modes
- Creates terminal sessions (tmux/screen) if needed
- Handles proper background operation
- Records PIDs for process management
- Launches the Python wrapper (run_live.py)
- Can start the system as a true daemon process (via daemon_launcher.py)

### 2. Python Wrapper: run_live.py

The Python wrapper [./Start_sh/run_live.py](../Start_sh/run_live.py) provides:

- Exception handling with Telegram notifications
- Watchdog monitoring for process freezes
- Heartbeat functionality for uptime verification
- Complete output capture to Main_Log.log
- Automatic startup of specialized log filters

This script:
1. Sets up global exception handling
2. Records its PID to running_pids.txt
3. Starts monitoring threads (heartbeat, watchdog)
4. **Automatically starts 3+ total log filter** via 3start.sh
5. **Automatically starts Main Log management system** via Main_log_logic.py
6. Launches live.py (core functionality)

### 3. Log Filter: 3start.sh and log_filter.py

The consolidated 3+ total log system consists of:

- **All-in-one command script**: [./3start.sh](../3start.sh) - Unified command for managing 3+ total logs
- **Filter implementation**: [./logs/log_alerts/3start/log_filter.py](../logs/log_alerts/3start/log_filter.py) - Does the actual filtering

The 3start.sh script provides these functions:
```bash
# Start the 3+ total filter
./3start.sh start

# View 3+ total log entries (newest first)
./3start.sh view

# Other commands
./3start.sh stop      # Stop the filter
./3start.sh status    # Check filter status
./3start.sh restart   # Restart the filter

# Advanced viewing options
./3start.sh view -n 10              # Show last 10 matches
./3start.sh view -s "Premier League" # Search for Premier League matches
./3start.sh view -f                 # Follow log updates in real-time
```

The log filter:
1. Monitors Main_Log.log in real-time
2. Extracts matches meeting specific criteria (O/U ≥ 3.0)
3. Logs them to 3_start.log with sequential numbering
4. Writes new entries at the top of the log (newest first)
5. Prevents duplicate entries via match tracking

### 4. Main Log Management: main_log.sh and Main_log_logic.py

The Main Log Management system consists of:

- **Command interface**: [./main_log.sh](../main_log.sh) - Convenient access to Main Log management
- **Core implementation**: [./logs/Main_log_logic.py](../logs/Main_log_logic.py) - Monitors and processes Main_Log.log

The main_log.sh script provides:
```bash
# View the Main Log (newest entries first)
./main_log.sh view

# Other commands
./main_log.sh status   # Check status
./main_log.sh stop     # Stop the processor
./main_log.sh restart  # Restart the processor

# Advanced viewing options
./main_log.sh view -n 50             # Show last 50 entries
./main_log.sh view -s "search term"  # Search for specific text
./main_log.sh view -f                # Follow log updates in real-time
./main_log.sh view -N                # Normal order (oldest first)
```

The Main Log management system:
1. Monitors Main_Log.log in real-time without modifying it
2. Creates Reversed_Main_Log.log with newest entries at the top
3. Provides advanced viewing options via command-line interface
4. Starts automatically with the football monitoring system

### 5. Daemon Launcher: daemon_launcher.py

The daemon launcher [./Start_sh/daemon_launcher.py](../Start_sh/daemon_launcher.py) provides:

- True daemon process (runs after terminal closes)
- Automatic restart on crashes
- Exponential backoff for repeated crashes
- Telegram alerts for status updates
- Heartbeat monitoring and status tracking

This script:
1. Daemonizes the process using proper Unix fork techniques
2. Manages heartbeat and status files
3. Automatically restarts the main process on failure
4. Provides command-line controls (start/stop/status/restart)

### 6. Core Functionality: live.py

The main application [./live.py](../live.py):

- Connects to TheSports API
- Fetches live match data
- Processes and formats match information
- Outputs detailed match summaries

## Component Architecture

The system is designed with a clean separation of concerns:

| Component           | Responsibility                                   | File                       |
|---------------------|--------------------------------------------------|----------------------------|
| **Startup**         | Process management, mode selection               | start_monitor.sh           |
| **Reliability**     | Exception handling, monitoring, alerting         | run_live.py                |
| **Daemon**          | Persistent operation, auto-restart               | daemon_launcher.py         |
| **Log Management**  | Consolidated commands for 3+ total logs          | 3start.sh                  |
| **Log Filtering**   | Specialized logging based on criteria            | 3start/log_filter.py       |
| **Main Log Manager**| Reversed Main Log with newest entries first      | Main_log_logic.py          |
| **Core Logic**      | API integration, data processing                 | live.py                    |
| **Logging**         | Data preservation, history tracking              | logs/Main_Log.log          |
| **Notifications**   | Centralized Telegram alerts                      | telegram/notifier.py       |

## Runtime Modes

### Terminal Mode

When running with `--terminal`:
- Creates a tmux/screen session named "football_monitor"
- Shows live output in the terminal
- Allows detaching/reattaching without stopping processes
- Use `tmux attach -t football_monitor` to reconnect

### Background Mode

When running with `--background`:
- Runs silently without terminal output
- Logs everything to Main_Log.log
- Monitors and filters continue to operate
- Can use `tail -f logs/Main_Log.log` to view activity

### Daemon Mode (NEW)

When running with `--daemon`:
- Runs as a true daemon process (continues after terminal closes)
- Automatically restarts if the process crashes
- Provides heartbeat monitoring and status tracking
- Sends Telegram notifications for important events
- Logs daemon activity to logs/daemon/daemon.log

When using daemon mode:
- The process will continue running even if you close the terminal
- It will automatically restart if it crashes
- Status information is available in logs/daemon/ directory
- Use `./Start_sh/start_monitor.sh --daemon-status` to check status

### Foreground Mode

When running without options:
- Runs in the current terminal
- Shows all output directly
- Terminates when you press Ctrl+C

## Process Management

All components record their PIDs for management:
- Main process ID is stored in `running_pids.txt`
- Log filter PID is stored in `logs/log_alerts/3start/log_filter_pid.txt`
- Main Log manager PID is stored in `logs/Main_Log/main_log_pid.txt`
- Daemon PID is stored in `logs/daemon/football_daemon.pid`

To stop processes:
```bash
# Stop main process (if not in daemon mode)
kill $(cat running_pids.txt)

# Stop the daemon
./Start_sh/start_monitor.sh --daemon-stop

# Stop just the log filter
./3start.sh stop

# Stop just the Main Log manager
./main_log.sh stop
```

## Log Files

The system creates several log files:

| Log File                               | Contains                                       |
|----------------------------------------|------------------------------------------------|
| logs/Main_Log.log                      | All match data and system events               |
| logs/Reversed_Main_Log.log             | Same as Main_Log but with newest entries first |
| logs/log_alerts/3start/3_start.log     | Matches with Over/Under line ≥ 3.0            |
| logs/log_alerts/3start/log_filter_process.log | Log filter status and processing events |
| logs/daemon/daemon.log                 | Daemon process activity and status             |
| logs/daemon/heartbeat.json             | Latest heartbeat timestamp from daemon         |
| logs/daemon/status.json                | Current daemon status and details              |

## Automated Integration

All components start automatically - you only need to run start_monitor.sh:

1. Start the system in daemon mode (recommended for 24/7 operation):
   ```bash
   ./Start_sh/start_monitor.sh --daemon
   ```

2. All processes will begin:
   - live.py fetches data from TheSports API
   - Data is logged to Main_Log.log
   - Main_log_logic.py creates Reversed_Main_Log.log
   - log_filter.py filters and creates specialized logs
   - 3_start.log collects matches with high totals
   - daemon_launcher.py monitors and restarts if needed

3. You can view the output:
   ```bash
   # View main log (newest first)
   ./main_log.sh view
   
   # View 3+ total matches
   ./3start.sh view
   
   # Check daemon status
   ./Start_sh/start_monitor.sh --daemon-status
   ```

## Start Script Options

```
Usage: ./Start_sh/start_monitor.sh [options]

Options:
  --background, -b    Run in background mode
  --terminal, -t      Create a tmux/screen session
  --daemon, -d        Run as persistent daemon (continues after terminal closes)
  --daemon-stop       Stop the running daemon
  --daemon-status     Check daemon status
  --daemon-restart    Restart the daemon
  --interval, -i N    Set refresh interval in seconds
  --continuous, -c    Run in continuous mode
```

## 3+ Total Log Management

The consolidated 3start.sh script provides a unified interface for managing the 3+ total log system:

```
Usage: ./3start.sh [command] [options]

Commands:
  start         Start the log filter
    -f, --foreground    Run in foreground mode

  stop          Stop the log filter

  restart       Restart the log filter
    -f, --foreground    Run in foreground mode

  status        Check if the filter is running

  view          View the 3+ Total log file
    -n, --lines N       Show last N entries (default: 20)
    -f, --follow        Follow log updates in real-time
    -s, --search TEXT   Search for text in log
    -a, --all           Show entire log file
    -r, --reverse       Show newest entries first (default)
    -N, --normal        Show entries in normal chronological order
```

## Main Log Management

The main_log.sh script provides a unified interface for managing and viewing the Main Log:

```
Usage: ./main_log.sh [command] [options]

Commands:
  start         Start the Main Log processor
    -f, --foreground    Run in foreground mode

  stop          Stop the Main Log processor

  restart       Restart the Main Log processor
    -f, --foreground    Run in foreground mode

  status        Check if the processor is running

  view          View the Main Log
    -n, --lines N       Show last N entries (default: 100)
    -f, --follow        Follow log updates in real-time
    -s, --search TEXT   Search for text in log
    -r, --reverse       Show newest entries first (default)
    -N, --normal        Show entries in normal chronological order
```

## Deployment Recommendations

For production use:
1. Use daemon mode for 24/7 operation with auto-restart:
   ```bash
   ./Start_sh/start_monitor.sh --daemon
   ```

2. Set up regular log rotation for Main_Log.log

3. Monitor daemon status periodically:
   ```bash
   ./Start_sh/start_monitor.sh --daemon-status
   ```
