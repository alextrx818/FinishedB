#!/bin/bash
# Script to run live.py in the foreground to display match data directly in the terminal

echo "Starting Football Live Monitor in FOREGROUND mode"
echo "Match data will display directly in this terminal"
echo "Press Ctrl+C to stop"
echo "Started at: $(date)"
echo "========================================"

# Change to the project directory
cd "/root/CascadeProjects/sports bot"

# Run live.py in continuous mode with 30-second updates
python3 football/live.py --continuous --interval 30
