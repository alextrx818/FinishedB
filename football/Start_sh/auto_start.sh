#!/bin/bash
# Football Monitor - Auto Start Script
# This script wraps start_monitor.sh and ensures continuous execution via Supervisor

# Define project paths
PROJECT_DIR="/root/CascadeProjects/sports bot"
FOOTBALL_DIR="$PROJECT_DIR/football"
SCRIPTS_DIR="$FOOTBALL_DIR/Start_sh"
CONTINUOUS_DIR="$FOOTBALL_DIR/Continuous_Run"

# Ensure script is running as root
if [ "$(id -u)" -ne 0 ]; then
    echo "This script must be run as root to configure Supervisor. Please use sudo."
    exit 1
fi

# Function to display banner
show_banner() {
    echo "======================================================"
    echo "       FOOTBALL LIVE DATA AUTO-START SYSTEM"
    echo "======================================================"
    echo "This script starts all components of the football monitoring system"
    echo "and ensures they run continuously until explicitly stopped."
    echo "======================================================"
    echo ""
}

# Display banner
show_banner

# STEP 1: Ensure Supervisor is installed and configured
echo "[1/4] Checking Supervisor installation and configuration..."

if ! command -v supervisorctl &> /dev/null; then
    echo "Installing Supervisor..."
    apt-get update
    apt-get install -y supervisor
    systemctl enable supervisor
    systemctl start supervisor
    echo "Supervisor installed successfully."
else
    echo "Supervisor is already installed."
fi

# Copy configuration file
echo "Configuring Supervisor for football monitor..."
mkdir -p "$CONTINUOUS_DIR/config"
cp "$CONTINUOUS_DIR/football-monitor.conf" /etc/supervisor/conf.d/
chmod 644 /etc/supervisor/conf.d/football-monitor.conf
chmod +x "$CONTINUOUS_DIR/run_with_supervisor.sh"

# STEP 2: Ensure log directories exist
echo "[2/4] Setting up log directories..."
mkdir -p "$FOOTBALL_DIR/logs"
mkdir -p "$FOOTBALL_DIR/logs/log_alerts/3start"

# STEP 3: Configure system for automatic restart
echo "[3/4] Configuring for continuous operation..."
supervisorctl reread
supervisorctl update

# Ensure previous football monitor instances are stopped
echo "Stopping any existing football monitor processes..."
supervisorctl stop football-monitor 2>/dev/null || true
pkill -f "start_monitor.sh" 2>/dev/null || true
pkill -f "live.py" 2>/dev/null || true

# STEP 4: Start the football monitor with Supervisor
echo "[4/4] Starting football monitor with continuous execution..."
supervisorctl start football-monitor

# Wait a moment to ensure the process has started
sleep 3

# Check if process is running
if supervisorctl status football-monitor | grep -q "RUNNING"; then
    echo ""
    echo "======================================================"
    echo "       FOOTBALL MONITOR STARTED SUCCESSFULLY"
    echo "======================================================"
    echo "The football monitoring system is now running with automatic"
    echo "restart capabilities via Supervisor."
    echo ""
    echo "To check status: supervisorctl status football-monitor"
    echo "To stop system:  supervisorctl stop football-monitor"
    echo "To view logs:    tail -f $FOOTBALL_DIR/logs/Main_Log.log"
    echo "======================================================"
else
    echo ""
    echo "======================================================"
    echo "       ERROR STARTING FOOTBALL MONITOR"
    echo "======================================================"
    echo "There was a problem starting the football monitor."
    echo "Please check the logs for more information:"
    echo "  Supervisor logs: tail -f $FOOTBALL_DIR/logs/supervisor_*.log"
    echo "======================================================"
    exit 1
fi
