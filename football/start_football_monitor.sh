#!/bin/bash
# Main entry script for Football Monitor
# This script serves as a simple entry point to launch the monitoring system

echo "===== Football Live Data Monitor ====="
echo "Starting live monitor with output to terminal and Main_Log.log..."
echo "All data is being preserved in Main_Log.log for historical reference"

# Execute the run_live_main.sh script from the Start_sh directory
bash "$(dirname "$0")/Start_sh/run_live_main.sh"

# Note: The script now maintains a continuous log in Main_Log.log
# with session start/stop markers for reference
