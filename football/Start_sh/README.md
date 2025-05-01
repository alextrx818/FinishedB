# Football Monitor Startup System

This directory contains the scripts responsible for starting the football monitoring system and ensuring reliable execution.

## Key Components

### start_monitor.sh

The main entry point for the football monitoring system. This script provides various startup options:

```bash
./start_monitor.sh [options]
```

Options:
- `--auto, -a`: Start with automatic continuous execution via Supervisor (recommended)
- `--continuous, -c`: Run in continuous mode (keeps running after one cycle)
- `--background, -b`: Run in background mode
- `--terminal, -t`: Run in a terminal session with tmux
- `--daemon, -d`: Run as a daemon process
- `--interval, -i N`: Set refresh interval to N seconds

### auto_start.sh

Handles the complete setup of continuous execution via Supervisor:

```bash
sudo ./auto_start.sh
```

This script:
1. Installs and configures Supervisor if needed
2. Sets up the football monitor for continuous execution
3. Starts all components and ensures they run reliably

### run_live.py

Python wrapper script that provides reliability features for `live.py`:

1. Exception handling and recovery
2. Logging and output redirection
3. Heartbeat monitoring
4. Process management

## Usage Examples

### Recommended: Full Automatic Setup

```bash
./start_monitor.sh --auto
```

### Other Start Methods

```bash
# Start in continuous mode
./start_monitor.sh --continuous

# Start in background mode
./start_monitor.sh --background

# Start in a terminal session
./start_monitor.sh --terminal

# Start with a custom refresh interval (60 seconds)
./start_monitor.sh --interval 60 --continuous
```

## Important Notes

1. The `--auto` flag is the recommended approach for reliable operation
2. Supervisor provides automatic restart capabilities if any component crashes
3. The system is designed to keep running until explicitly stopped
4. Don't modify `live.py` directly as it's the core data processing engine
