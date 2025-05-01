#!/bin/bash
# Football Monitor - Master Control Script
# This script provides a unified interface for managing the football monitoring system
# using all available continuous run methods

# Define project paths
PROJECT_DIR="/root/CascadeProjects/sports bot"
FOOTBALL_DIR="$PROJECT_DIR/football"
SCRIPTS_DIR="$FOOTBALL_DIR/Start_sh"
CONTINUOUS_DIR="$FOOTBALL_DIR/Continuous_Run"

# Create required directories
mkdir -p "$CONTINUOUS_DIR/config"
mkdir -p "$FOOTBALL_DIR/logs"

# Function to display help
show_help() {
    echo "Football Monitor - Supervisor Control Script"
    echo "========================================"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start        Start the football monitor with Supervisor"
    echo "  stop         Stop the football monitor"
    echo "  restart      Restart the football monitor"
    echo "  status       Check the status of the football monitor"
    echo "  configure    Install and configure Supervisor"
    echo "  help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start     # Start using Supervisor"
    echo "  $0 stop      # Stop monitoring"
    echo "  $0 status    # Check status"
    echo ""
}

# Function to start with supervisor
start_with_supervisor() {
    echo "Starting football monitor using Supervisor..."
    
    # Check if supervisor is installed
    if ! command -v supervisorctl &> /dev/null; then
        echo "Error: Supervisor is not installed. Run '$0 configure' first."
        exit 1
    fi
    
    # Make run script executable
    chmod +x "$CONTINUOUS_DIR/run_with_supervisor.sh"
    
    # Update supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl start football-monitor
    
    echo "Football monitor started with Supervisor."
    echo "Check status with: $0 status"
}

# Function to stop supervisor
stop_supervisor() {
    echo "Stopping football monitor in Supervisor..."
    
    # Check if supervisor is installed
    if ! command -v supervisorctl &> /dev/null; then
        echo "Error: Supervisor is not installed."
        return
    fi
    
    sudo supervisorctl stop football-monitor
    echo "Football monitor stopped."
}

# Function to check supervisor status
check_supervisor_status() {
    echo "=== Football Monitor Status (Supervisor) ==="
    
    # Check if supervisor is installed
    if ! command -v supervisorctl &> /dev/null; then
        echo "Supervisor is not installed. Run '$0 configure' first."
        return
    fi
    
    sudo supervisorctl status football-monitor
    echo ""
    
    # Check for live.py process
    echo "Checking for live.py processes:"
    pgrep -fa "live.py" || echo "No live.py processes found"
    
    # Check log file status
    echo ""
    echo "Checking log file status:"
    ls -lh "$FOOTBALL_DIR/logs/"Main_Log.log 2>/dev/null || echo "Main log file not found"
    
    # Show latest log entries
    echo ""
    echo "Last 5 lines of Main_Log.log:"
    tail -n 5 "$FOOTBALL_DIR/logs/Main_Log.log" 2>/dev/null || echo "Cannot read log file"
}

# Function to configure supervisor
configure_supervisor() {
    echo "Installing and configuring Supervisor..."
    
    # Install supervisor if not already installed
    if ! command -v supervisorctl &> /dev/null; then
        echo "Installing Supervisor..."
        sudo apt-get update
        sudo apt-get install -y supervisor
        sudo systemctl enable supervisor
        sudo systemctl start supervisor
    else
        echo "Supervisor is already installed."
    fi
    
    # Ensure config directory exists
    mkdir -p "$CONTINUOUS_DIR/config"
    
    # Copy config file to the system location
    echo "Configuring Supervisor for Football Monitor..."
    sudo cp "$CONTINUOUS_DIR/football-monitor.conf" /etc/supervisor/conf.d/
    sudo chmod 644 /etc/supervisor/conf.d/football-monitor.conf
    
    # Make run script executable
    chmod +x "$CONTINUOUS_DIR/run_with_supervisor.sh"
    
    # Update supervisor
    sudo supervisorctl reread
    sudo supervisorctl update
    
    echo "Supervisor configuration complete."
    echo "To start the football monitor, run: $0 start"
}

# Process command line arguments
if [ $# -lt 1 ]; then
    show_help
    exit 1
fi

command=$1

case $command in
    start)
        start_with_supervisor
        ;;
    stop)
        stop_supervisor
        ;;
    restart)
        stop_supervisor
        sleep 2
        start_with_supervisor
        ;;
    status)
        check_supervisor_status
        ;;
    configure)
        configure_supervisor
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $command"
        show_help
        exit 1
        ;;
esac

exit 0
