# Football Monitor Continuous Execution System

This directory contains the scripts and configuration needed to run the football monitoring system continuously using Supervisor.

## What is Supervisor?

Supervisor is a process control system that ensures your scripts run continuously and restart automatically if they crash. It's the perfect tool for keeping your football monitoring system running reliably 24/7.

## Files in this Directory

- `run_forever.sh` - Management script for controlling the football monitor with Supervisor
- `run_with_supervisor.sh` - Script that Supervisor executes to run the football monitor
- `football-monitor.conf` - Supervisor configuration file

## How to Use

### Quick Start (Recommended Method)

The easiest way to use this system is through the main startup script:

```bash
./Start_sh/start_monitor.sh --auto
```

This automatically sets up and starts Supervisor with all the necessary configuration.

### Manual Operation

If you prefer to manage Supervisor directly:

1. Configure Supervisor:
   ```bash
   ./run_forever.sh configure
   ```
   This will install Supervisor if needed and set up the configuration.

2. Start the football monitor:
   ```bash
   ./run_forever.sh start
   ```

3. Check status:
   ```bash
   ./run_forever.sh status
   ```

4. Stop the football monitor:
   ```bash
   ./run_forever.sh stop
   ```

5. Restart the football monitor:
   ```bash
   ./run_forever.sh restart
   ```

## Key Benefits

- **Automatic Restart**: If the football monitor crashes, Supervisor will automatically restart it
- **Continuous Execution**: The system keeps running until explicitly stopped
- **Detailed Logging**: All output is captured in log files located in the logs directory

## Logs

- Main football log: `/root/CascadeProjects/sports bot/football/logs/Main_Log.log`
- Supervisor stdout log: `/root/CascadeProjects/sports bot/football/logs/supervisor_stdout.log`
- Supervisor stderr log: `/root/CascadeProjects/sports bot/football/logs/supervisor_stderr.log`

## Important Notes

1. Always use the `--continuous` flag when running the football monitor (handled automatically)
2. The 3+ total log filter (3_start.log) is automatically started by the main monitoring system
3. All logs use Eastern Time (ET) for consistency
4. The system is designed to respect core components like live.py, which should not be modified
