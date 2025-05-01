#!/bin/bash
# Football Monitor - Supervisor Runner Script
# This script is used by Supervisor to run the football monitor with continuous mode

# Define project paths
PROJECT_DIR="/root/CascadeProjects/sports bot"
FOOTBALL_DIR="$PROJECT_DIR/football"
SCRIPTS_DIR="$FOOTBALL_DIR/Start_sh"

# Ensure we're in the right directory
cd "$FOOTBALL_DIR" || exit 1

# Start the monitor with continuous flag
"$SCRIPTS_DIR/start_monitor.sh" --continuous

# If the script exits for any reason, sleep before exiting
# This prevents Supervisor from restarting too quickly if there's a problem
sleep 5
