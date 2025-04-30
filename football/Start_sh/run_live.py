#!/usr/bin/env python3
"""
Football Live Data Monitor - Wrapper Script
This script serves as a robust wrapper for live.py, providing:
1. Exception handling with notifications
2. Heartbeat monitoring for uptime verification
3. Main process execution

This allows live.py to remain focused on business logic while this wrapper
handles operational concerns like reliability and monitoring.
"""

import sys
import os
import threading
import time
import requests
import traceback
import logging
from datetime import datetime
import subprocess
import io
from contextlib import redirect_stdout, redirect_stderr

# Set up logging
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
MAIN_LOG = os.path.join(LOG_DIR, "Main_Log.log")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(MAIN_LOG),
        logging.StreamHandler()
    ]
)

# Add the parent directory to sys.path so we can import from football
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import the main function from live.py
try:
    from football.live import main as live_main
except ImportError:
    # Try relative import if the above fails
    sys.path.append(os.path.dirname(parent_dir))
    try:
        from live import main as live_main
    except ImportError:
        logging.error("Could not import main function from live.py")
        sys.exit(1)

# Telegram notification configuration
TELEGRAM_TOKEN = "7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko"
TELEGRAM_CHAT_ID = "6128359776"

def send_telegram_alert(message):
    """Send an alert message via Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code != 200:
            logging.error(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        logging.error(f"Error sending Telegram alert: {str(e)}")

def handle_exception(exc_type, exc_value, exc_tb):
    """Global exception handler that logs and notifies on unhandled exceptions"""
    # Format the exception details
    exception_message = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    
    # Create a user-friendly message for notifications
    error_msg = f"⚠️ *FOOTBALL MONITOR ERROR* ⚠️\n\n"
    error_msg += f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    error_msg += f"*Error:* {exc_value}\n\n"
    error_msg += f"The monitor will be automatically restarted."
    
    # Log the full exception
    logging.error(f"Unhandled exception: {exception_message}")
    
    # Send Telegram notification
    send_telegram_alert(error_msg)
    
    # Add a separator in the main log
    with open(MAIN_LOG, "a") as log_file:
        log_file.write("\n=== ERROR OCCURRED - RESTARTING MONITOR ===\n\n")
    
    # Re-raise the exception so systemd/Supervisor will restart it
    sys.exit(1)

# Install the global exception hook
sys.excepthook = handle_exception

# Setup the "heartbeat" function
# This is a placeholder URL - replace with your actual healthcheck URL
HC_PING_URL = "https://hc-ping.com/your-uuid-here"

def heartbeat():
    """Send regular heartbeat pings to verify the application is alive"""
    while True:
        try:
            # Send the heartbeat ping
            requests.get(HC_PING_URL, timeout=5)
            logging.debug("Heartbeat ping sent successfully")
        except Exception as e:
            logging.warning(f"Failed to send heartbeat ping: {str(e)}")
        
        # Wait for the next interval
        time.sleep(60)  # Send heartbeat every minute

def watchdog():
    """Monitor the main process and report if no activity is detected"""
    last_log_size = 0
    last_activity = time.time()
    
    while True:
        try:
            # Check if the log file has been updated
            current_size = os.path.getsize(MAIN_LOG)
            
            if current_size != last_log_size:
                # Activity detected
                last_log_size = current_size
                last_activity = time.time()
            elif time.time() - last_activity > 300:  # 5 minutes of inactivity
                # No activity for 5 minutes, send an alert
                message = "⚠️ *WARNING: No activity detected* ⚠️\nThe football monitor has not logged any activity for 5 minutes."
                send_telegram_alert(message)
                # Reset the timer to avoid spamming alerts
                last_activity = time.time()
        
        except Exception as e:
            logging.error(f"Error in watchdog thread: {str(e)}")
        
        # Check again in 30 seconds
        time.sleep(30)

def record_pid():
    """Record the current process ID for management purposes"""
    pid = os.getpid()
    pid_file = os.path.join(parent_dir, "running_pids.txt")
    
    try:
        with open(pid_file, "w") as f:
            f.write(str(pid))
        logging.info(f"Process ID {pid} recorded to {pid_file}")
    except Exception as e:
        logging.error(f"Failed to record PID: {str(e)}")

def main():
    """Main function that initiates all monitoring and runs the live.py script"""
    # Record the current PID
    record_pid()
    
    # Log the startup
    startup_message = f"\n=== Football Live Monitor Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
    with open(MAIN_LOG, "a") as log_file:
        log_file.write(startup_message)
    
    # Send startup notification
    send_telegram_alert("🟢 *Football Monitor Starting* 🟢\nThe football live data monitor is now starting up.")
    
    # Start the heartbeat thread
    threading.Thread(target=heartbeat, daemon=True).start()
    logging.info("Heartbeat monitoring thread started")
    
    # Start the watchdog thread
    threading.Thread(target=watchdog, daemon=True).start()
    logging.info("Watchdog monitoring thread started")
    
    try:
        # Create a custom output capture that writes to both console and log
        class TeeOutput:
            def __init__(self, log_file_path):
                self.terminal = sys.stdout
                self.log_file = open(log_file_path, "a", buffering=1)  # Line buffered
                
            def write(self, message):
                self.terminal.write(message)
                self.log_file.write(message)
                
            def flush(self):
                self.terminal.flush()
                self.log_file.flush()
                
            def close(self):
                self.log_file.close()
        
        # Set up output capture
        tee = TeeOutput(MAIN_LOG)
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = tee
        sys.stderr = tee
        
        # Hand off to the main function from live.py
        logging.info("Starting live.py main function")
        try:
            live_main()
        finally:
            # Restore stdout and stderr even if there's an exception
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            tee.close()
            
    except Exception as e:
        # This should be caught by the global exception handler,
        # but just in case, we add this extra try/except
        logging.error(f"Error in main function: {str(e)}")
        send_telegram_alert(f"⚠️ *ERROR IN FOOTBALL MONITOR* ⚠️\n\n{str(e)}")
        sys.exit(1)
    finally:
        # Log the shutdown (if we ever get here normally)
        shutdown_message = f"\n=== Football Live Monitor Stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n"
        with open(MAIN_LOG, "a") as log_file:
            log_file.write(shutdown_message)

if __name__ == "__main__":
    main()
