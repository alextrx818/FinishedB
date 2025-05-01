#!/bin/bash
# Football Monitor - Main Entry Script
# This script serves as the entry point for the football monitoring system
# It starts the Python wrapper which handles all the reliability features

# Define project paths
PROJECT_DIR="/root/CascadeProjects/sports bot"
FOOTBALL_DIR="$PROJECT_DIR/football"
SCRIPTS_DIR="$FOOTBALL_DIR/Start_sh"
LOGS_DIR="$FOOTBALL_DIR/logs"
WRAPPER_SCRIPT="$SCRIPTS_DIR/run_live.py"
DAEMON_SCRIPT="$SCRIPTS_DIR/daemon_launcher.py"
MAIN_LOG="$LOGS_DIR/Main_Log.log"

# Ensure log directory exists
mkdir -p "$LOGS_DIR"

# Display banner
echo "======================================================"
echo "       FOOTBALL LIVE DATA MONITORING SYSTEM"
echo "======================================================"
echo "Starting monitor at: $(date)"
echo "Logs will be saved to: $MAIN_LOG"
echo ""

# Make sure the wrapper script is executable
chmod +x "$WRAPPER_SCRIPT"
chmod +x "$DAEMON_SCRIPT" 2>/dev/null

# Default settings
BACKGROUND=false
TERMINAL=false
DAEMON=false
DAEMON_ACTION="start"
COMMAND="python3"
ARGS=""
AUTO_RUN=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --background|-b)
            BACKGROUND=true
            ;;
        --terminal|-t)
            TERMINAL=true
            ;;
        --daemon|-d)
            DAEMON=true
            ;;
        --daemon-stop)
            DAEMON=true
            DAEMON_ACTION="stop"
            ;;
        --daemon-status)
            DAEMON=true
            DAEMON_ACTION="status"
            ;;
        --daemon-restart)
            DAEMON=true
            DAEMON_ACTION="restart"
            ;;
        --interval|-i)
            ARGS="$ARGS --interval $2"
            shift
            ;;
        --continuous|-c)
            ARGS="$ARGS --continuous"
            ;;
        --auto|-a)
            AUTO_RUN=true
            ARGS="$ARGS --continuous"
            ;;
        *)
            echo "Unknown parameter: $1"
            echo "Usage: $0 [--background|-b] [--terminal|-t] [--daemon|-d] [--daemon-stop] [--daemon-status] [--daemon-restart] [--interval|-i N] [--continuous|-c] [--auto|-a]"
            exit 1
            ;;
    esac
    shift
done

# If auto-run mode is enabled, use the auto-start script
if [ "$AUTO_RUN" = true ]; then
    echo "Starting in auto-run mode with continuous execution via Supervisor..."
    exec sudo "$SCRIPTS_DIR/auto_start.sh"
    exit 0  # This line shouldn't be reached as exec replaces the current process
fi

# Run the wrapper script
cd "$PROJECT_DIR" || exit 1

# Handle daemon mode (full background process with auto-restart)
if [ "$DAEMON" = true ]; then
    echo "Operating football monitor in daemon mode..."
    
    # Check if daemon launcher exists
    if [ ! -f "$DAEMON_SCRIPT" ]; then
        echo "Error: Daemon launcher script not found at $DAEMON_SCRIPT"
        exit 1
    fi
    
    # Execute the appropriate daemon action
    "$COMMAND" "$DAEMON_SCRIPT" "$DAEMON_ACTION"
    exit $?
fi

# Handle terminal mode with tmux/screen
if [ "$TERMINAL" = true ]; then
    # Create a new terminal session with tmux or screen
    SESSION_NAME="football_monitor"
    
    # Kill any existing session with the same name
    if command -v tmux &> /dev/null; then
        # Using tmux
        tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true
        echo "Creating new tmux session for football monitor..."
        
        # Create a new detached session
        tmux new-session -d -s "$SESSION_NAME" "cd '$PROJECT_DIR' && python3 '$WRAPPER_SCRIPT' $ARGS; bash"
        
        # Save PID info
        PID=$(pgrep -f "$WRAPPER_SCRIPT")
        if [ -n "$PID" ]; then
            echo "$PID" > "$FOOTBALL_DIR/running_pids.txt"
            echo "Monitor started in tmux session: $SESSION_NAME"
            echo "PID: $PID saved to $FOOTBALL_DIR/running_pids.txt"
        fi
        
        echo ""
        echo "The monitor is now running in a tmux session."
        echo "To view the terminal output:"
        echo "  tmux attach -t $SESSION_NAME"
        echo ""
        echo "To detach from the session (leaving it running):"
        echo "  Press Ctrl+B then D"
        
        # If not in background mode, attach to the session
        if [ "$BACKGROUND" = false ]; then
            echo "Attaching to tmux session..."
            tmux attach -t "$SESSION_NAME"
        fi
        
    elif command -v screen &> /dev/null; then
        # Using screen
        screen -X -S "$SESSION_NAME" quit 2>/dev/null || true
        echo "Creating new screen session for football monitor..."
        
        # Create a new detached screen session
        screen -dmS "$SESSION_NAME" bash -c "cd '$PROJECT_DIR' && python3 '$WRAPPER_SCRIPT' $ARGS; bash"
        
        # Save PID info
        PID=$(pgrep -f "$WRAPPER_SCRIPT")
        if [ -n "$PID" ]; then
            echo "$PID" > "$FOOTBALL_DIR/running_pids.txt"
            echo "Monitor started in screen session: $SESSION_NAME"
            echo "PID: $PID saved to $FOOTBALL_DIR/running_pids.txt"
        fi
        
        echo ""
        echo "The monitor is now running in a screen session."
        echo "To view the terminal output:"
        echo "  screen -r $SESSION_NAME"
        echo ""
        echo "To detach from the session (leaving it running):"
        echo "  Press Ctrl+A then D"
        
        # If not in background mode, attach to the session
        if [ "$BACKGROUND" = false ]; then
            echo "Attaching to screen session..."
            screen -r "$SESSION_NAME"
        fi
        
    else
        echo "Error: Neither tmux nor screen is installed."
        echo "Please install one of these terminal multiplexers:"
        echo "  apt-get install tmux   # or"
        echo "  apt-get install screen"
        exit 1
    fi
    
elif [ "$BACKGROUND" = true ]; then
    # Standard background mode (no terminal)
    echo "Starting monitor in background mode..."
    nohup "$COMMAND" "$WRAPPER_SCRIPT" $ARGS > /dev/null 2>&1 &
    PID=$!
    echo "Monitor started with PID: $PID"
    echo "$PID" > "$FOOTBALL_DIR/running_pids.txt"
    echo "PID saved to: $FOOTBALL_DIR/running_pids.txt"
    echo "To check status: tail -f $MAIN_LOG"
    echo "To stop: kill $PID"
else
    # Standard foreground mode (current terminal)
    echo "Starting monitor in foreground mode..."
    echo "Press Ctrl+C to stop"
    echo "========================================"
    "$COMMAND" "$WRAPPER_SCRIPT" $ARGS
fi
