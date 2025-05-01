#!/bin/bash
# Main Log Management System Wrapper
# Provides convenient access to Main_log_logic.py functionality

# Define paths
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
MAIN_LOG_SCRIPT="$SCRIPT_DIR/logs/Main_log_logic.py"

# Ensure the script is executable
chmod +x "$MAIN_LOG_SCRIPT" 2>/dev/null

# Display banner
echo "======================================================"
echo "       MAIN LOG MANAGEMENT SYSTEM"
echo "======================================================"

# Forward all arguments to the Python script
python3 "$MAIN_LOG_SCRIPT" "$@"
