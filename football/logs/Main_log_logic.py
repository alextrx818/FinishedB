#!/usr/bin/env python3
"""
Main_log_logic.py - Comprehensive Main Log Management System
===========================================================

This script serves as the central management system for Main_Log.log.
It provides:
1. Reversed log generation (newest entries first)
2. Extensible filtering framework
3. Real-time monitoring and processing
4. Simple command interface for viewing and managing the log

This design follows the same pattern as the 3+ total log system,
providing a consistent experience across the football monitoring platform.
"""

import os
import sys
import time
import re
import json
import logging
import hashlib
import subprocess
from datetime import datetime
import signal
import argparse

# Configure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
MAIN_LOG = os.path.join(SCRIPT_DIR, "Main_Log.log")
REVERSED_LOG = os.path.join(SCRIPT_DIR, "Reversed_Main_Log.log")
MAIN_LOG_DIR = os.path.join(SCRIPT_DIR, "Main_Log")
PROCESS_LOG = os.path.join(MAIN_LOG_DIR, "main_log_process.log")
PID_FILE = os.path.join(MAIN_LOG_DIR, "main_log_pid.txt")
POSITION_FILE = os.path.join(MAIN_LOG_DIR, "main_log_position.json")

# Ensure the Main_Log directory exists
os.makedirs(MAIN_LOG_DIR, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(PROCESS_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("main_log_logic")

# Save PID for management
def save_pid():
    """Save the current process ID to the PID file"""
    pid = os.getpid()
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))
    logger.info(f"PID {pid} saved to {PID_FILE}")

# Handle graceful shutdown
def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Received shutdown signal. Exiting...")
    sys.exit(0)

# Initialize the reversed log file
def initialize_reversed_log(timestamp=None):
    """
    Create or initialize the reversed log file with header
    
    Args:
        timestamp (str, optional): Specific timestamp to use in the header.
                                  If None, current time will be used.
    """
    if not os.path.exists(REVERSED_LOG):
        logger.info(f"Creating new reversed log file: {REVERSED_LOG}")
    
    # Use provided timestamp or current time
    if timestamp is None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
    # Create/overwrite the file with the header
    with open(REVERSED_LOG, 'w') as f:
        f.write("======================================================================\n")
        f.write("                     REVERSED MAIN LOG\n")
        f.write(f"                 Last Updated: {timestamp}\n")
        f.write("======================================================================\n\n")
        f.write("(Newest entries appear at the top)\n\n")

# Save the current position
def save_position(position):
    """Save the current position in the main log to resume later"""
    with open(POSITION_FILE, 'w') as f:
        json.dump({"position": position, "timestamp": time.time()}, f)

# Load the last position
def load_position():
    """Load the previous position in the main log"""
    if os.path.exists(POSITION_FILE):
        try:
            with open(POSITION_FILE, 'r') as f:
                data = json.load(f)
                return data.get('position', 0)
        except Exception as e:
            logger.error(f"Error loading position: {e}")
    return 0

# Extract log entries from text content
def extract_log_entries(content):
    """Split log content into individual entries based on timestamp patterns"""
    # This regex looks for lines that start with a timestamp format
    entries = re.split(r'\n(?=\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    return [entry.strip() for entry in entries if entry.strip()]

# Extract timestamp from log content
def extract_log_timestamp(content):
    """Extract the most recent timestamp from log content"""
    # Look for refreshing or timestamp patterns
    refresh_match = re.search(r'REFRESHING DATA AT: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    if refresh_match:
        return refresh_match.group(1)
    
    # If no refresh timestamp found, check for entry timestamps
    timestamp_match = re.search(r'Timestamp: (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', content)
    if timestamp_match:
        return timestamp_match.group(1)
    
    # If no timestamps found in content, return None
    return None

# Process new entries and add them to the top of the reversed log
def process_log(last_position=0):
    """Process new entries in the main log"""
    # Check if main log exists
    if not os.path.exists(MAIN_LOG):
        logger.warning(f"Main log file not found: {MAIN_LOG}")
        return last_position
    
    try:
        with open(MAIN_LOG, 'r') as f:
            # Seek to the last position
            f.seek(last_position)
            
            # Read new content
            new_content = f.read()
            current_position = f.tell()
            
            # If there's new content, add it to the reversed log
            if new_content:
                # Extract entries from the new content
                entries = extract_log_entries(new_content)
                
                # Extract timestamp from new content
                log_timestamp = extract_log_timestamp(new_content)
                
                if entries:
                    # Add each new entry to the top of the reversed log
                    logger.info(f"Adding {len(entries)} new entries to reversed log")
                    
                    # Read the current content of the reversed log (skipping header)
                    existing_content = ""
                    if os.path.exists(REVERSED_LOG):
                        with open(REVERSED_LOG, 'r') as rev:
                            lines = rev.readlines()
                            # Find where the actual log entries start (after header)
                            for i, line in enumerate(lines):
                                if "(Newest entries appear at the top)" in line:
                                    existing_content = "".join(lines[i+2:])  # +2 to skip the line and the following blank line
                                    break
                    
                    # Write the reversed log with new entries at the top using the actual data timestamp
                    initialize_reversed_log(log_timestamp)  # Use extracted timestamp for the header
                    
                    with open(REVERSED_LOG, 'a') as rev:
                        # Write new entries (newest first)
                        for entry in reversed(entries):
                            if entry.strip():
                                rev.write(f"{entry}\n\n")
                                rev.write("------------------------------------------------------------\n\n")
                        
                        # Write existing content
                        if existing_content.strip():
                            rev.write(existing_content)
            
            # Save the new position
            save_position(current_position)
            return current_position
    
    except Exception as e:
        logger.error(f"Error processing log: {e}")
        return last_position

# View the main log with various options
def view_main_log(args):
    """View the Main_Log.log entries with various options"""
    log_file = REVERSED_LOG if args.reverse else MAIN_LOG
    
    if not os.path.exists(log_file):
        print(f"Error: Log file not found: {log_file}")
        return
    
    # Display log info
    print(f"Viewing: {os.path.basename(log_file)}")
    print(f"Total lines: {sum(1 for _ in open(log_file))}")
    print(f"Last updated: {datetime.fromtimestamp(os.path.getmtime(log_file)).strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    try:
        # Parse lines to show argument
        lines_to_show = 100  # Default
        if args.lines and args.lines != "all":
            lines_to_show = int(args.lines)
        elif args.lines == "all":
            # Show the entire file
            with open(log_file, 'r') as f:
                print(f.read())
            return
        
        # Handle search option
        if args.search:
            print(f"Searching for: {args.search}")
            # Create a grep-like pattern
            pattern = args.search.replace("\"", "").replace("'", "")
            
            # Use grep to find matching lines
            result = subprocess.run(
                ["grep", "-i", pattern, log_file],
                capture_output=True, 
                text=True
            )
            
            if result.stdout:
                print(result.stdout)
            else:
                print(f"No matches found for: {pattern}")
        else:
            # Normal viewing mode
            if args.lines == "all":
                with open(log_file, 'r') as f:
                    print(f.read())
            elif args.reverse:
                # Already using reversed log, just show top lines
                subprocess.run(["head", "-n", str(lines_to_show), log_file])
            else:
                # Normal viewing of tail
                subprocess.run(["tail", "-n", str(lines_to_show), log_file])
    except ValueError:
        print(f"Error: Invalid number of lines: {args.lines}")

# Main monitoring function
def main_monitor():
    """Main function that monitors and processes the main log"""
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Save the PID
    save_pid()
    
    logger.info("Starting Main Log Management System...")
    
    try:
        # Initialize the reversed log
        initialize_reversed_log()
        
        # Get the last position in the main log
        last_position = load_position()
        logger.info(f"Starting from position: {last_position}")
        
        # Main monitoring loop
        logger.info("Main Log Management System started successfully")
        while True:
            # Process any new entries
            last_position = process_log(last_position)
            
            # Wait before checking again
            time.sleep(1)
    
    except Exception as e:
        logger.error(f"Error in main monitor: {e}")
        raise

# Command-line interface
def cli():
    """Command-line interface for Main_log_logic.py"""
    parser = argparse.ArgumentParser(description="Main Log Management System")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the main log monitor")
    start_parser.add_argument("--foreground", "-f", action="store_true", help="Run in foreground mode")
    
    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop the main log monitor")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Check the status of the main log monitor")
    
    # View command
    view_parser = subparsers.add_parser("view", help="View the main log")
    view_parser.add_argument("--lines", "-n", help="Number of lines to show, or 'all' for all lines")
    view_parser.add_argument("--search", "-s", help="Search for text in the log")
    view_parser.add_argument("--reverse", "-r", action="store_true", default=True, help="Show newest entries first (default)")
    view_parser.add_argument("--normal", "-N", action="store_false", dest="reverse", help="Show entries in normal order (oldest first)")
    
    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart the main log monitor")
    restart_parser.add_argument("--foreground", "-f", action="store_true", help="Run in foreground mode")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "start":
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
                try:
                    os.kill(int(pid), 0)  # Check if process exists
                    print(f"Main log monitor is already running with PID {pid}")
                    return
                except OSError:
                    # Process not running, remove stale PID file
                    os.remove(PID_FILE)
        
        if args.foreground:
            print("Starting main log monitor in foreground mode...")
            main_monitor()
        else:
            print("Starting main log monitor in background mode...")
            subprocess.Popen(
                [sys.executable, __file__, "start", "--foreground"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True
            )
    
    elif args.command == "stop":
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
                try:
                    print(f"Stopping main log monitor (PID: {pid})...")
                    os.kill(int(pid), signal.SIGTERM)
                    print("Main log monitor stopped.")
                except OSError as e:
                    print(f"Error stopping process: {e}")
        else:
            print("No PID file found. Main log monitor may not be running.")
    
    elif args.command == "status":
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
                try:
                    os.kill(int(pid), 0)  # Check if process exists
                    print(f"Main log monitor is running with PID {pid}")
                    
                    # Show last few process log entries
                    if os.path.exists(PROCESS_LOG):
                        print("\nLast 5 log entries:")
                        subprocess.run(["tail", "-n", "5", PROCESS_LOG])
                except OSError:
                    print("Main log monitor is not running (stale PID file).")
        else:
            print("Main log monitor is not running.")
    
    elif args.command == "view":
        view_main_log(args)
    
    elif args.command == "restart":
        # First stop
        if os.path.exists(PID_FILE):
            with open(PID_FILE, 'r') as f:
                pid = f.read().strip()
                try:
                    print(f"Stopping main log monitor (PID: {pid})...")
                    os.kill(int(pid), signal.SIGTERM)
                    time.sleep(1)  # Wait for process to terminate
                except OSError:
                    pass
        
        # Then start
        if args.foreground:
            print("Starting main log monitor in foreground mode...")
            main_monitor()
        else:
            print("Starting main log monitor in background mode...")
            subprocess.Popen(
                [sys.executable, __file__, "start", "--foreground"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True
            )
    
    else:
        parser.print_help()

# Entry point
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "start" and "--foreground" in sys.argv:
        main_monitor()
    else:
        cli()
