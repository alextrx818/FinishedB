#!/usr/bin/env python3
"""
3start_monitor.py - Monitor for 3.0+ Line Values in Over/Under Markets

This script monitors the Main_Log.log file for matches with betting line values
of 3.0 or higher in the Over/Under section. It uses pygtail to efficiently
tail the log file, ensuring only new lines are processed.

When a match with a high line value is found, it logs the details to 3Start.log.
"""

import os
import re
import sys
import time
import logging
from datetime import datetime
import signal

try:
    from pygtail import Pygtail
except ImportError:
    print("Required package 'pygtail' not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pygtail"])
    from pygtail import Pygtail

# Configure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
MAIN_LOG = os.path.join(LOGS_DIR, "Main_Log.log")
OUTPUT_LOG = os.path.join(SCRIPT_DIR, "3start_matches.log")
STATUS_LOG = os.path.join(SCRIPT_DIR, "3start_status.log")
OFFSET_FILE = os.path.join(SCRIPT_DIR, "3start_offset.txt")

# Configure logging for status messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(STATUS_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("3start_monitor")

# Configuration settings
MIN_LINE_VALUE = 3.0    # Minimum line value to capture (inclusive)
MAX_LINE_VALUE = 10.0   # Maximum line value to consider valid (inclusive)
CHECK_INTERVAL = 5      # How often to check for new log entries (seconds)
INACTIVITY_THRESHOLD = 300  # Seconds without main log updates before warning

class LineMonitor:
    """Monitor for high line values in football matches"""
    
    def __init__(self):
        self.last_activity_time = time.time()
        self.setup_signal_handlers()
        self.running = True
        
    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
    def signal_handler(self, sig, frame):
        """Handle shutdown signals"""
        logger.info("Received shutdown signal. Exiting...")
        self.running = False
        
    def log_status_message(self, message, level="INFO"):
        """Log a status message with timestamp"""
        if level == "INFO":
            logger.info(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "ERROR":
            logger.error(message)
            
    def log_match_to_file(self, match_data):
        """Log a match with high line value to the output file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(OUTPUT_LOG, 'a') as f:
            f.write(f"=== 3START LINE ALERT: {timestamp} ===\n")
            f.write(match_data.strip() + "\n")
            f.write("="*50 + "\n\n")
            
        logger.info(f"Match with 3+ line detected and logged to {OUTPUT_LOG}")
    
    def is_in_over_under_section(self, lines, current_index):
        """Check if the current line is within the Over/Under section"""
        # Look backward for the Over/Under header
        for i in range(current_index, max(0, current_index-10), -1):
            if i < len(lines) and "Over/Under:" in lines[i]:
                return True
                
        return False
        
    def extract_match_data(self, lines, match_line_index, line_value):
        """Extract relevant match data surrounding the high line value"""
        # First find the match summary section
        match_summary_start = None
        
        # Look backwards for match summary
        for i in range(match_line_index, max(0, match_line_index-50), -1):
            if i < len(lines) and "----- MATCH SUMMARY -----" in lines[i]:
                match_summary_start = i
                break
                
        if match_summary_start is None:
            # If can't find match summary, just include nearby lines
            start_index = max(0, match_line_index - 15)
            end_index = min(len(lines), match_line_index + 15)
            match_data = "\n".join(lines[start_index:end_index])
            return f"PARTIAL MATCH DATA (Line value: {line_value}):\n{match_data}"
        
        # Look forward for the end of this match section
        match_end = None
        for i in range(match_line_index, min(len(lines), match_line_index+50)):
            if i < len(lines) and (
                "==================================================\n" == lines[i] or
                "------------------------------------------------------------\n" == lines[i]
            ):
                match_end = i
                break
                
        if match_end is None:
            match_end = min(len(lines), match_summary_start + 50)  # Limit to reasonable size
            
        # Extract the complete match data
        match_data = "\n".join(lines[match_summary_start:match_end])
        return match_data
    
    def process_log_chunk(self, log_chunk):
        """Process a chunk of log content looking for high line values"""
        if not log_chunk:
            return
            
        # Reset activity timer since we got new content
        self.last_activity_time = time.time()
        
        # Split into lines for processing
        lines = log_chunk.splitlines()
        
        for i, line in enumerate(lines):
            # Check if this line contains a line value
            line_match = re.search(r'Time: \d+ min \| Over: .* \| Line: ([\d.]+) \| Under:', line)
            
            if line_match and self.is_in_over_under_section(lines, i):
                try:
                    line_value = float(line_match.group(1))
                    
                    # Check if the line value is within our target range
                    if MIN_LINE_VALUE <= line_value <= MAX_LINE_VALUE:
                        # Extract the match data and log it
                        match_data = self.extract_match_data(lines, i, line_value)
                        self.log_match_to_file(match_data)
                except ValueError:
                    # Skip if we can't parse the line value as a float
                    pass
    
    def check_main_log_status(self):
        """Check if the Main_Log.log is being actively updated"""
        current_time = time.time()
        seconds_since_update = current_time - self.last_activity_time
        
        if seconds_since_update > INACTIVITY_THRESHOLD:
            self.log_status_message(
                f"WARNING: Main log hasn't been updated in {int(seconds_since_update)} seconds. "
                "The live.py script may have stopped running.",
                "WARNING"
            )
            return False
        return True
    
    def run(self):
        """Main monitoring loop"""
        logger.info("Starting 3start line monitor...")
        logger.info(f"Monitoring {MAIN_LOG} for line values >= {MIN_LINE_VALUE}")
        
        if not os.path.exists(MAIN_LOG):
            logger.error(f"Main log file not found: {MAIN_LOG}")
            return
            
        try:
            # Create output log file if it doesn't exist
            if not os.path.exists(OUTPUT_LOG):
                with open(OUTPUT_LOG, 'w') as f:
                    f.write(f"=== 3START LINE MONITOR LOG CREATED {datetime.now()} ===\n\n")
            
            # Periodically check for new content
            while self.running:
                try:
                    pygtail = Pygtail(MAIN_LOG, offset_file=OFFSET_FILE)
                    content = ""
                    
                    for line in pygtail:
                        content += line
                        
                    if content:
                        self.process_log_chunk(content)
                    
                    # Check main log status
                    self.check_main_log_status()
                    
                except Exception as e:
                    logger.error(f"Error processing log: {e}")
                    
                # Wait before checking again
                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Shutting down...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            
        logger.info("3start line monitor stopped")

def main():
    """Main entry point"""
    try:
        monitor = LineMonitor()
        monitor.run()
    except Exception as e:
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
