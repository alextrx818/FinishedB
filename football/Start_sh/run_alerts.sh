#!/bin/bash
# Script to run the football_alerts.py in continuous mode

echo "Starting Football Alerts System..."
echo "Press Ctrl+C to stop"
echo "Started at: $(date)"
echo "========================================"

# Run the football_alerts.py script
cd "/root/CascadeProjects/sports bot"
python3 football/football_alerts.py
