import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import json as json_lib
import traceback
import datetime
import pytz
import time
import shutil

# Define the log file path
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "json.log")

# Custom midnight rotating file handler with clean restart
class MidnightRotatingFileHandler(TimedRotatingFileHandler):
    """Custom file handler that rotates at midnight and ensures a clean json.log"""
    
    def __init__(self, filename, backupCount=0, encoding=None):
        # Initialize with midnight rotation
        super().__init__(
            filename=filename,
            when="midnight",
            interval=1,
            backupCount=backupCount,
            encoding=encoding
        )
        # Use date-based suffix for rotated files
        self.suffix = "%Y-%m-%d"
        
    def doRollover(self):
        """
        Override the standard rollover to ensure we have a clean json.log after rotation
        and the backups use the date-based naming convention
        """
        # Close the current file if it's open
        if self.stream:
            self.stream.close()
            self.stream = None
            
        # Get current time for the backup filename
        current_time = int(time.time())
        dst_now = time.localtime(current_time)[-1]
        eastern = pytz.timezone('America/New_York')
        now = datetime.datetime.now(eastern)
        
        # Create the backup filename with date (json.log.YYYY-MM-DD)
        backup_filename = f"{self.baseFilename}.{now.strftime('%Y-%m-%d')}"
        
        # If backup file already exists, remove it first
        if os.path.exists(backup_filename):
            os.remove(backup_filename)
            
        # Copy the current log to the backup file
        if os.path.exists(self.baseFilename):
            shutil.copy2(self.baseFilename, backup_filename)
            
        # Create a fresh, empty log file
        with open(self.baseFilename, 'w') as f:
            f.write("")
            
        # Process old backup files based on backupCount
        if self.backupCount > 0:
            # Get list of all backup files
            dir_name, base_name = os.path.split(self.baseFilename)
            backup_files = []
            
            for filename in os.listdir(dir_name):
                if filename.startswith(base_name) and filename != base_name:
                    backup_files.append(os.path.join(dir_name, filename))
                    
            # If we have more backups than allowed, delete the oldest ones
            if len(backup_files) > self.backupCount:
                backup_files.sort() # Sort by name (which has date in it)
                for old_file in backup_files[:len(backup_files) - self.backupCount]:
                    os.remove(old_file)
        
        # Reopen the file
        if not self.delay:
            self.stream = self._open()

# Create a standard logger for regular usage
json_logger = logging.getLogger("json_dump")
json_logger.setLevel(logging.DEBUG)
json_logger.propagate = False

# Create the custom midnight rotating handler
handler = MidnightRotatingFileHandler(
    filename=LOG_FILE_PATH,
    backupCount=7,  # Keep 7 days worth of logs
    encoding="utf-8"
)

# Use the standard formatter
handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
json_logger.addHandler(handler)

# Eastern timezone formatter function
def get_eastern_timestamp():
    """Get current timestamp in US Eastern timezone with mm/dd/yyyy format"""
    try:
        eastern = pytz.timezone('America/New_York')
        now = datetime.datetime.now(eastern)
        return now.strftime("%m/%d/%Y %I:%M:%S %p ET")
    except Exception as e:
        # Fallback to standard time if there's an issue
        print(f"Error getting Eastern time: {e}", file=sys.stderr)
        return datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")

# Custom logger functions
def _prepend_to_file(content):
    """Prepend content to the log file with error handling"""
    try:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)
        
        # Check if file exists and has content
        if os.path.exists(LOG_FILE_PATH) and os.path.getsize(LOG_FILE_PATH) > 0:
            with open(LOG_FILE_PATH, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(content + existing_content)
        else:
            with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
                f.write(content)
        return True
    except Exception as e:
        print(f"Error prepending to JSON log: {e}", file=sys.stderr)
        traceback.print_exc()
        return False

# Buffer state for blocks
_buffer_active = False
_buffer_lines = []

def log_block(text):
    """Log a text block with buffering for blocks"""
    global _buffer_active, _buffer_lines
    
    # Check for block start marker
    if "="*50 in text and not _buffer_active:
        _buffer_active = True
        _buffer_lines = [f"{text}\n"]
        return
    
    # Add to buffer during buffering mode
    if _buffer_active:
        _buffer_lines.append(f"{text}\n")
        
        # Check for end of block (empty line)
        if text.strip() == "":
            # Flush buffer to file with Eastern timestamp
            eastern_timestamp = get_eastern_timestamp()
            full_content = f"[{eastern_timestamp}] {''.join(_buffer_lines)}"
            _prepend_to_file(full_content)
            _buffer_active = False
            _buffer_lines = []
        return
    
    # For non-block content, just prepend directly with Eastern timestamp
    eastern_timestamp = get_eastern_timestamp()
    _prepend_to_file(f"[{eastern_timestamp}] {text}\n")

# Save the original debug method
_original_debug = json_logger.debug

def custom_debug(message):
    """Custom debug implementation with prepending behavior"""
    # First handle our custom prepending logic
    log_block(message)
    
    # Then call the original handler (avoid recursion)
    _original_debug(message)

# Special function for JSON data
def log_json(data):
    """Log JSON data with timestamp and proper formatting"""
    if isinstance(data, str):
        try:
            # Try to parse as JSON string first
            parsed = json_lib.loads(data)
            custom_debug(json_lib.dumps(parsed, indent=2))
        except:
            # Just log as regular string
            custom_debug(data)
    else:
        # Convert to formatted JSON
        custom_debug(json_lib.dumps(data, indent=2))

# Replace the debug method with our custom implementation
json_logger.debug = custom_debug

# Create an empty log file if it doesn't exist
if not os.path.exists(LOG_FILE_PATH):
    with open(LOG_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write("")

# Function to manually trigger rotation (for testing purposes)
def force_rotation():
    """Force log rotation for testing purposes"""
    handler.doRollover()
    print(f"Manually rotated log file to {LOG_FILE_PATH}.{datetime.datetime.now().strftime('%Y-%m-%d')}")

# Add a console handler for debugging when running directly
if __name__ == "__main__" or "JSON_LOGGER_DEBUG" in os.environ:
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("JSON_LOG: %(message)s"))
    json_logger.addHandler(console)
    print("JSON Logger initialized with console debugging")
