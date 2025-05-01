#!/usr/bin/env python3
"""
Football Monitor Daemon Launcher
===============================
This script launches the football monitoring system as a persistent background daemon.
It handles:
1. Background operation (continues after terminal closes)
2. Automatic restart on crashes
3. Heartbeat monitoring and alerts
4. Logging of daemon status

Usage:
  python3 daemon_launcher.py start   # Start in background mode
  python3 daemon_launcher.py stop    # Stop the daemon
  python3 daemon_launcher.py status  # Check if daemon is running
"""

import os
import sys
import time
import signal
import subprocess
import logging
import datetime
import traceback
import atexit
import json
from pathlib import Path

# Get base directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(SCRIPT_DIR)
LOG_DIR = os.path.join(BASE_DIR, "logs")
DAEMON_DIR = os.path.join(LOG_DIR, "daemon")

# Create daemon directory if it doesn't exist
os.makedirs(DAEMON_DIR, exist_ok=True)

# Daemon files
PID_FILE = os.path.join(DAEMON_DIR, "football_daemon.pid")
LOG_FILE = os.path.join(DAEMON_DIR, "daemon.log")
HEARTBEAT_FILE = os.path.join(DAEMON_DIR, "heartbeat.json")
STATUS_FILE = os.path.join(DAEMON_DIR, "status.json")

# Telegram details (from memory)
TELEGRAM_TOKEN = "7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko"
CHAT_ID = "6128359776"

# Paths to other scripts
RUN_LIVE_SCRIPT = os.path.join(SCRIPT_DIR, "run_live.py")
LOG_FILTER_SCRIPT = os.path.join(BASE_DIR, "3start.sh")

# Configure logging for daemon
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("football_daemon")

def send_telegram_message(message):
    """Send a message via Telegram"""
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message,
            "disable_notification": False
        }
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Failed to send Telegram message: {e}")
        return False

def daemonize():
    """
    Turn the process into a proper daemon that will
    continue running after terminal closes
    """
    try:
        # First fork
        pid = os.fork()
        if pid > 0:
            # Exit first parent
            sys.exit(0)
    except OSError as e:
        logger.error(f"Fork #1 failed: {e}")
        sys.exit(1)

    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)

    try:
        # Second fork
        pid = os.fork()
        if pid > 0:
            # Exit from second parent
            sys.exit(0)
    except OSError as e:
        logger.error(f"Fork #2 failed: {e}")
        sys.exit(1)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    # Write PID file
    pid = str(os.getpid())
    with open(PID_FILE, 'w+') as f:
        f.write(pid + '\n')
    
    # Set up cleanup on exit
    atexit.register(lambda: os.remove(PID_FILE) if os.path.exists(PID_FILE) else None)

def update_heartbeat():
    """Update the heartbeat file with latest timestamp"""
    try:
        heartbeat_data = {
            "last_heartbeat": datetime.datetime.now().isoformat(),
            "pid": os.getpid()
        }
        with open(HEARTBEAT_FILE, 'w') as f:
            json.dump(heartbeat_data, f)
    except Exception as e:
        logger.error(f"Failed to update heartbeat: {e}")

def update_status(status, details=None):
    """Update the status file with process information"""
    try:
        status_data = {
            "status": status,
            "details": details or {},
            "last_update": datetime.datetime.now().isoformat(),
            "pid": os.getpid()
        }
        with open(STATUS_FILE, 'w') as f:
            json.dump(status_data, f)
    except Exception as e:
        logger.error(f"Failed to update status: {e}")

def start_log_filter():
    """Start the 3+ total log filter"""
    try:
        logger.info("Starting 3+ total log filter...")
        subprocess.Popen([LOG_FILTER_SCRIPT, "start"], 
                        cwd=os.path.dirname(LOG_FILTER_SCRIPT),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
        logger.info("3+ total log filter started successfully")
        return True
    except Exception as e:
        logger.error(f"Error starting log filter: {e}")
        return False

def run_monitor():
    """Run the football monitor with auto-restart on crash"""
    consecutive_crashes = 0
    max_consecutive_crashes = 5
    backoff_time = 5  # Starting backoff time in seconds
    
    while True:
        try:
            update_status("starting")
            update_heartbeat()
            
            # Start log filter if needed
            start_log_filter()
            
            # Run the monitor
            logger.info("Starting football monitor...")
            update_status("running")
            
            # Run the actual monitor process
            process = subprocess.Popen(
                [sys.executable, RUN_LIVE_SCRIPT],
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Send notification that monitor has started
            send_telegram_message("🟢 Football Monitor started in daemon mode")
            
            # Reset crash counter on successful start
            consecutive_crashes = 0
            backoff_time = 5
            
            # Heartbeat loop while process is running
            while process.poll() is None:
                update_heartbeat()
                time.sleep(30)  # Update heartbeat every 30 seconds
            
            # Process has terminated
            logger.warning(f"Monitor process exited with code: {process.returncode}")
            stderr = process.stderr.read().decode('utf-8', errors='replace')
            if stderr:
                logger.error(f"Error output: {stderr}")
            
            # Handle unexpected termination
            if process.returncode != 0:
                consecutive_crashes += 1
                update_status("crashed", {"exit_code": process.returncode, "error": stderr[:500]})
                
                # Only alert if crashes are occurring frequently
                if consecutive_crashes >= 3:
                    send_telegram_message(f"⚠️ Football Monitor crashed (attempt {consecutive_crashes}).\nRestarting in {backoff_time} seconds...")
                
                # Implement exponential backoff for repeated crashes
                logger.info(f"Backing off for {backoff_time} seconds before restart...")
                time.sleep(backoff_time)
                backoff_time = min(300, backoff_time * 2)  # Cap at 5 minutes
                
                # Give up after too many consecutive crashes
                if consecutive_crashes >= max_consecutive_crashes:
                    error_msg = f"❌ Football Monitor crashed {consecutive_crashes} times in a row. Giving up."
                    logger.error(error_msg)
                    send_telegram_message(error_msg)
                    update_status("failed", {"reason": "too_many_crashes"})
                    sys.exit(1)
            else:
                # Normal termination
                update_status("stopped", {"reason": "normal_exit"})
                send_telegram_message("🔴 Football Monitor stopped normally")
                break
                
        except Exception as e:
            logger.error(f"Daemon error: {e}\n{traceback.format_exc()}")
            update_status("error", {"error": str(e)})
            send_telegram_message(f"❌ Football Monitor daemon error: {str(e)}")
            time.sleep(10)  # Wait before retry

def start_daemon():
    """Start the daemon process"""
    if os.path.isfile(PID_FILE):
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        try:
            # Check if process is actually running
            os.kill(pid, 0)
            logger.error(f"Daemon already running with PID {pid}")
            print(f"Daemon already running with PID {pid}")
            sys.exit(1)
        except OSError:
            # Process not running, remove stale PID file
            os.remove(PID_FILE)
    
    # Start the daemon
    daemonize()
    logger.info("Football monitor daemon started")
    
    try:
        run_monitor()
    except Exception as e:
        logger.error(f"Daemon failed: {e}\n{traceback.format_exc()}")
        sys.exit(1)

def stop_daemon():
    """Stop the daemon process"""
    if not os.path.isfile(PID_FILE):
        logger.error("PID file not found, daemon not running?")
        print("PID file not found, daemon not running?")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        logger.info(f"Stopping daemon with PID {pid}")
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to terminate
        for _ in range(10):
            time.sleep(1)
            try:
                os.kill(pid, 0)
            except OSError:
                # Process is gone
                if os.path.exists(PID_FILE):
                    os.remove(PID_FILE)
                logger.info("Daemon stopped successfully")
                print("Daemon stopped successfully")
                return
        
        # Force kill if still running
        logger.warning(f"Daemon did not terminate gracefully, sending SIGKILL to PID {pid}")
        os.kill(pid, signal.SIGKILL)
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        print("Daemon forcefully terminated")
    except Exception as e:
        logger.error(f"Error stopping daemon: {e}")
        print(f"Error stopping daemon: {e}")

def status_daemon():
    """Check the status of the daemon"""
    if not os.path.isfile(PID_FILE):
        print("Daemon not running (no PID file)")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        try:
            # Check if process is actually running
            os.kill(pid, 0)
            print(f"Daemon running with PID {pid}")
            
            # Check heartbeat
            if os.path.exists(HEARTBEAT_FILE):
                with open(HEARTBEAT_FILE, 'r') as f:
                    heartbeat = json.load(f)
                    last_time = datetime.datetime.fromisoformat(heartbeat["last_heartbeat"])
                    time_diff = (datetime.datetime.now() - last_time).total_seconds()
                    if time_diff > 120:  # 2 minutes
                        print(f"WARNING: Last heartbeat was {int(time_diff)} seconds ago")
                    else:
                        print(f"Last heartbeat: {last_time.strftime('%Y-%m-%d %H:%M:%S')} ({int(time_diff)} seconds ago)")
            
            # Check status file
            if os.path.exists(STATUS_FILE):
                with open(STATUS_FILE, 'r') as f:
                    status = json.load(f)
                    print(f"Status: {status['status']}")
                    if 'details' in status and status['details']:
                        for key, value in status['details'].items():
                            print(f"  {key}: {value}")
            
        except OSError:
            print(f"Daemon not running (stale PID file exists)")
    except Exception as e:
        print(f"Error checking daemon status: {e}")

if __name__ == "__main__":
    # Process command line arguments
    if len(sys.argv) < 2 or sys.argv[1] not in ["start", "stop", "status", "restart"]:
        print(f"Usage: {sys.argv[0]} [start|stop|status|restart]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "start":
        print("Starting football monitor daemon...")
        start_daemon()
    elif command == "stop":
        print("Stopping football monitor daemon...")
        stop_daemon()
    elif command == "restart":
        print("Restarting football monitor daemon...")
        stop_daemon()
        time.sleep(2)
        start_daemon()
    elif command == "status":
        status_daemon()
