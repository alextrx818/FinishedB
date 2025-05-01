#!/bin/bash
# Simple wrapper script for live.py
# This script runs live.py without modifying it

cd /root/CascadeProjects/sports_bot/football || exit 1

# Set timezone to ensure correct timestamps
export TZ="America/New_York"

# Install python-systemd if not present (needed for watchdog)
if ! python3 -c "import systemd.daemon" &>/dev/null; then
    echo "Installing python-systemd package..."
    apt-get update && apt-get install -y python3-systemd
fi

# Send Telegram alert for system startup
python3 -c "import sys; sys.path.append('/root/CascadeProjects/sports_bot'); from football.telegram import send_system_alert; send_system_alert('Sports Bot System Started', alert_type='startup')"

# Define cleanup function to send shutdown notification
cleanup() {
    echo "Shutting down sports bot..."
    python3 -c "import sys; sys.path.append('/root/CascadeProjects/sports_bot'); from football.telegram import send_system_alert; send_system_alert('Sports Bot System Shut Down', alert_type='shutdown')"
    exit 0
}

# Register the cleanup function for various signals
trap cleanup SIGINT SIGTERM

# Create a temporary watchdog script
cat > /tmp/watchdog_wrapper.py << 'EOL'
#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import threading
from systemd import daemon

# Path to the original live.py script
LIVE_PY = "/root/CascadeProjects/sports_bot/football/live.py"

def watchdog_thread():
    """Thread that sends periodic watchdog pings to systemd"""
    while True:
        # Ping systemd to let it know we're still alive
        daemon.notify('WATCHDOG=1')
        time.sleep(15)  # Send a ping every 15 seconds (half of WatchdogSec)

def main():
    # Tell systemd we're ready
    daemon.notify('READY=1')
    
    # Start the watchdog thread
    t = threading.Thread(target=watchdog_thread, daemon=True)
    t.start()
    
    # Launch live.py with the specified arguments
    args = [sys.executable, LIVE_PY]
    if '-c' in sys.argv:
        args.append('-c')
    
    # Run the original live.py - this will block until it completes
    process = subprocess.run(args)
    
    # Stop sending watchdog pings and exit with the same code
    sys.exit(process.returncode)

if __name__ == '__main__':
    main()
EOL

# Make the watchdog script executable
chmod +x /tmp/watchdog_wrapper.py

# Tell systemd we're ready to start
python3 -c "from systemd import daemon; daemon.notify('READY=1')"

# Run live.py through the watchdog wrapper in continuous mode
python3 /tmp/watchdog_wrapper.py -c

# If we get here, it means live.py exited unexpectedly
python3 -c "import sys; sys.path.append('/root/CascadeProjects/sports_bot'); from football.telegram import send_system_alert; send_system_alert('Sports Bot Exited Unexpectedly', alert_type='error', error_details='live.py process terminated')"