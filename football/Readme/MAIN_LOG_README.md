# Main Log System

## Overview

The Main Log system is a critical component of the Football Monitoring infrastructure. This document explains how the Main Log works and how to make modifications to its behavior.

## Important Principle: Single Source of Truth

**The Main Log system follows a key design principle: Main_Log.log is the single source of truth.**

This means:
- Main_Log.log is the primary log file written directly by live.py
- All other log views (including Reversed_Main_Log.log) are derived from this source file
- **DO NOT modify live.py or its logging behavior directly** - this could break the system

## Main Log Components

```
logs/
├── Main_Log.log              # Primary log file (written by live.py)
├── Reversed_Main_Log.log     # Reversed view with newest entries first
├── Main_log_logic.py         # Log processor that creates the reversed view
└── Main_Log/                 # Directory for Main Log management files
    ├── main_log_pid.txt      # PID file for the processor
    └── main_log_process.log  # Process log for the Main Log management
```

## Main_log_logic.py: The Central Control Point

**Any changes to how Main Log content is presented should be made in Main_log_logic.py.**

This script is designed to:
1. Monitor Main_Log.log in real-time without modifying it
2. Create Reversed_Main_Log.log with newest entries at the top
3. Apply any custom formatting or filtering rules
4. Provide viewing capabilities through a command interface

## How The System Works

```
live.py
   │
   ▼
Main_Log.log ◄────────┐
   │                  │
   │                  │ Monitored by
   ▼                  │
Main_log_logic.py ────┘
   │
   ▼
Reversed_Main_Log.log
```

1. **live.py writes to Main_Log.log**: The core application writes log entries to Main_Log.log in standard format (oldest entries at bottom).

2. **Main_log_logic.py monitors the file**: The log processor watches Main_Log.log for changes.

3. **Changes are processed**: When new entries appear, they are processed according to rules in Main_log_logic.py.

4. **Reversed view is created**: New entries are added to the top of Reversed_Main_Log.log.

## Making Changes to Log Presentation

If you need to modify how log entries are displayed or processed:

1. Edit Main_log_logic.py - this is the ONLY file you should modify
2. Look for the process_log() function - this handles how entries are processed
3. Make your changes (adding formatting, filtering, etc.)
4. Restart the Main Log processor: `./main_log.sh restart`

## Examples of Modifications You Can Make

All these modifications should be made in Main_log_logic.py, NOT by creating new files:

1. **Change entry formatting**:
   ```python
   # Find in process_log() function:
   for entry in reversed(entries):
       if entry.strip():
           # Modify how entries are formatted here
           formatted_entry = f"### {entry.strip()} ###"
           rev.write(f"{formatted_entry}\n\n")
   ```

2. **Add filtering rules**:
   ```python
   # Find in process_log() function:
   for entry in reversed(entries):
       # Add filtering logic
       if "ERROR" in entry or "WARNING" in entry:
           rev.write(f"{entry.strip()}\n\n")
   ```

3. **Create categorized sections**:
   ```python
   # Find in process_log() function:
   errors = []
   warnings = []
   info = []
   
   for entry in entries:
       if "ERROR" in entry:
           errors.append(entry)
       elif "WARNING" in entry:
           warnings.append(entry)
       else:
           info.append(entry)
   
   # Write categorized entries
   rev.write("=== ERRORS ===\n\n")
   for entry in reversed(errors):
       rev.write(f"{entry.strip()}\n\n")
       
   rev.write("=== WARNINGS ===\n\n")
   # etc.
   ```

## Command Interface

The `main_log.sh` script provides a convenient interface to the Main Log system:

```bash
# View the Main Log (newest first)
./main_log.sh view

# Other commands
./main_log.sh status   # Check processor status
./main_log.sh stop     # Stop the processor
./main_log.sh restart  # Restart after making changes

# Advanced viewing
./main_log.sh view -n 50              # Show last 50 entries
./main_log.sh view -s "search term"   # Search in the log
./main_log.sh view -f                 # Follow updates in real-time
./main_log.sh view -N                 # View in normal order (oldest first)
```

## Startup Flow

The Main Log system starts automatically as part of the football monitoring system:

1. User runs `./Start_sh/start_monitor.sh` (with any mode)
2. This launches `run_live.py`
3. `run_live.py` automatically starts `Main_log_logic.py`
4. `Main_log_logic.py` begins monitoring Main_Log.log and updating Reversed_Main_Log.log

You don't need to manually start the Main Log processor - it's integrated into the system startup.

## Important Notes

1. **DO NOT modify live.py** - This is a core file that should remain untouched
2. **DO NOT create new log files directly** - All log files should be derived from Main_Log.log
3. **DO make all changes through Main_log_logic.py** - This is the designated control point
4. **DO restart the processor after changes** - Use `./main_log.sh restart` to apply changes

By following these guidelines, you'll maintain a clean and consistent logging system that won't interfere with the core functionality of the football monitoring system.
