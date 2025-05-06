"""
=====================================================================
IMPORTANT: TERMINAL OUTPUT AND LOGGER FILE SYSTEMS DOCUMENTATION
=====================================================================

These two output systems (terminal display and logger file) are inherently 
separate but intentionally coupled through the code in this file:

1. OUTPUT INDEPENDENCE:
   - Terminal output: Controlled by Python's built-in print() function
   - Logger file output: Written to main.logger through file operations
   - These systems don't naturally stay in sync without explicit code

2. HOW THEY'RE COUPLED:
   - This file (main_logger.py) intercepts EVERY print() call in the application
   - It simultaneously formats the output for both terminal AND logger file
   - Any change to formatting must be done in main_logger.py, NOT in live.py

3. MODIFYING OUTPUT FORMAT:
   - DO NOT modify print statements in live.py expecting format changes
   - DO modify the formatting logic in main_logger.py (especially handle_match_header)
   - Always test both terminal AND logger output after changes

4. COMMON PITFALLS:
   - Adding separators in live.py will cause duplicates
   - Changing print formats in live.py won't affect logger output
   - Editing logger file operations without matching terminal output creates inconsistency

5. BEST PRACTICE:
   - Keep all formatting logic in main_logger.py
   - Make live.py print simple content that main_logger.py will intercept and format
   - Always check both outputs after changes

6. DATABASE CONNECTION:
   - This file sends log entries to Supabase 'main_logger_logs' table
   - Each log chunk is captured by an event listener and sent via Supabase client
   - Uses SUPABASE_KEY environment variable for authentication (fallback to SUPABASE_SERVICE_KEY)
   - No modification to the logging behavior is required to use this feature
   - UPDATED CONNECTION: This system now uses the Supabase Python client
     rather than direct REST API calls for better maintainability

NOTE: This coupling approach (overriding builtins.print) is not generally
recommended in production systems, but works for this specific use case.
A better long-term solution would be a proper logging framework with
formatters and handlers.
"""

import os
import builtins
import datetime
import pytz
import threading
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from football.logger.db_api import supabase

# Add threading lock for thread-safe file operations
_log_lock = threading.Lock()

# Add event listener list for callbacks
event_listeners = []

# Build LOG_FILE_PATH pointing to main.logger in the same folder
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.logger")

# ensure main.logger always exists
if not os.path.exists(LOG_FILE_PATH): open(LOG_FILE_PATH,'w').close()

# Add module-level variables for buffering and tracking
buffering = False
buffer_lines = []
last_log_date = None
daily_summary_count = 0

# Add a flag to control terminal output behavior
SMOOTH_SCROLLING = True  # Set to True to allow free scrolling without jumps

# Import constants if possible, otherwise define locally
try:
    from football.live import API_DATETIME_FORMAT
except ImportError:
    API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"

def get_eastern_time():
    """Get current time in Eastern timezone"""
    utc_now = datetime.datetime.now(pytz.utc)
    eastern = pytz.timezone('America/New_York')
    eastern_time = utc_now.astimezone(eastern)
    return eastern_time

# Format date according to standardized format (MM/DD/YYYY)
def format_date(date_obj):
    """Format date in standardized MM/DD/YYYY format"""
    return date_obj.strftime("%m/%d/%Y")

# Save builtins.print as original_print
original_print = builtins.print

# Add a one-time debug print to show the LOG_FILE_PATH
original_print("LOG FILE PATH →", LOG_FILE_PATH)

# Define the database listener function using Supabase client
def send_to_db(chunk: str):
    """Send log chunk to Supabase database using Python client"""
    try:
        # Insert the log chunk into main_logger_logs table
        print("▶️ PAYLOAD:", chunk, flush=True)
        response = supabase \
            .table("main_logger_logs") \
            .insert({"content": chunk}) \
            .execute()
        if getattr(response, "error", None):
            print("   ❌ INSERT FAILED:", response.error, flush=True)
        else:
            print("   ✅ Inserted, DB row id:", response.data[0]["id"], flush=True)
    except Exception as e:
        original_print(f"⚠️ Supabase logging error: {str(e)}")

# Register the listener if supabase is available
if supabase:
    event_listeners.append(send_to_db)
    original_print("✓ Supabase logger initialized and listener registered for main_logger_logs table")
else:
    original_print("⚠️ Supabase logging not initialized - client not available")

# Define new_print(*args, **kwargs) that calls original_print(*args, **kwargs)
# and then prepends the exact same text to main.logger
def new_print(*args, **kwargs):
    # Get the text being printed
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    text = sep.join(str(arg) for arg in args) + end
    
    # ————————————————————————————————————————————
    # 1) If this is your raw JSON payload, dump it only to stdout
    #    so alerts.py (or your console-based watcher) still sees it,
    #    but never hand it off to the FileHandler:
    if args and str(args[0]).startswith("__MATCH_JSON__"):
        # write to the real terminal
        original_print(*args, **kwargs)
        return
    # ————————————————————————————————————————————
    
    # UNIVERSAL RULE: Detect start of a block with the 50-character header
    global buffering, buffer_lines
    if text.startswith("="*50):
        buffering = True
        buffer_lines.clear()
        buffer_lines.append(text)
        # Still print to terminal
        if SMOOTH_SCROLLING:
            kwargs['flush'] = True
        original_print(*args, **kwargs)
        return
    
    # UNIVERSAL RULE: Handle buffering logic for the entire block
    if buffering:
        buffer_lines.append(text)
        # Still print to terminal
        if SMOOTH_SCROLLING:
            kwargs['flush'] = True
        original_print(*args, **kwargs)
        
        # End of block is indicated by a blank line
        if text.strip() == "":
            # Flush the whole chunk in one prepend
            chunk = "".join(buffer_lines)
            try:
                with open(LOG_FILE_PATH, 'r+') as f:
                    old = f.read()
                    f.seek(0)
                    f.write(chunk + old)
                    f.truncate()
            except Exception as e:
                original_print("Logger write error:", e)
            buffering = False
            buffer_lines.clear()
        return
    
    # Check if this is a MATCH line
    if text.strip().startswith("MATCH #") and " OF " in text:
        # This is a match header, we'll handle it specially and suppress normal printing
        handle_match_header(text)
        return
    
    # For all other lines, call the original print function with flush=True if smooth scrolling enabled
    if SMOOTH_SCROLLING:
        kwargs['flush'] = True
    original_print(*args, **kwargs)
    
    # Log the content using the configured logger system
    # This will use the TimedRotatingFileHandler for automatic midnight rotation
    if text.strip():  # Only log non-empty lines
        logger = logging.getLogger("live")
        logger.info(text.strip())

# Function to handle a match header
def handle_match_header(text):
    global buffering, buffer_lines, last_log_date, daily_summary_count
    
    # Reset date if needed
    current_date = get_eastern_time().date()
    current_date_std = format_date(current_date)
    current_time = get_eastern_time().strftime("%I:%M:%S %p ET")
        
    # Handle date transition
    if last_log_date is None or current_date != last_log_date:
        last_log_date = current_date
        daily_summary_count = 0
        date_banner = f"\n\n{'-' * 50}\nDate: {current_date_std}\n{'-' * 50}\n\n"
    else:
        date_banner = ""
        
    # Increment counter and create summary banner
    daily_summary_count += 1
    summary_banner = f"--- Summary Set #{daily_summary_count} for {current_date_std} --- {current_time}\n"
    
    # Build formatted block header exactly as it should appear in both terminal and log
    formatted_header = date_banner
    formatted_header += summary_banner
    formatted_header += "="*50 + "\n"
    formatted_header += text
    formatted_header += "="*50 + "\n\n"
    formatted_header += "="*50 + "\n\n"
    
    # Print to terminal using end="" to avoid extra newlines
    # Use flush=True to ensure output appears immediately but without forcing a scroll
    original_print(formatted_header, end="", flush=True)
    
    # Start buffering for the log file
    buffering = True
    buffer_lines = [formatted_header]

# Function to handle the end of a buffer
def handle_buffer_end():
    global buffering, buffer_lines
    chunk = "".join(buffer_lines)
    
    try:
        # Before writing to the log file, call all event listeners
        # Create a temporary buffer to capture output from listeners
        listener_output_buffer = []
        
        # Only execute if there are listeners
        if event_listeners:
            # Temporarily swap print function to capture any diagnostic output
            # from event listeners and ensure it's included in both terminal
            # and log file outputs
            old_print = builtins.print
            
            # Define a temporary print interceptor that captures output
            # and prints it to the terminal
            def capture_print(*args, **kwargs):
                # Get the text being captured
                sep = kwargs.get('sep', ' ')
                end = kwargs.get('end', '\n')
                text = sep.join(str(arg) for arg in args) + end
                
                # Print to terminal using flush parameter if smooth scrolling is enabled
                if SMOOTH_SCROLLING:
                    kwargs['flush'] = True
                original_print(*args, **kwargs)
                
                # Add to our listener output buffer
                listener_output_buffer.append(text)
            
            # Replace system print with our capture function
            builtins.print = capture_print
            
            # Call each listener on the current buffer
            for listener in event_listeners:
                try:
                    listener(chunk)
                except Exception as e:
                    original_print("Listener error:", e)
            
            # Restore original print function
            builtins.print = old_print
        
        # Add any captured output from listeners to our chunk
        if listener_output_buffer:
            chunk += "".join(listener_output_buffer)
        
        # IMPORTANT: Actually write the data to the log file
        # This is the missing piece - we need to use the logger here
        if chunk.strip():  # Only log non-empty chunks
            logger = logging.getLogger("live")
            logger.info(chunk.strip())
        
    except Exception as e:
        original_print("Logger write error:", e)
    
    # Reset buffering state
    buffering = False
    buffer_lines = []

# Add a function to toggle smooth scrolling mode
def toggle_smooth_scrolling(enabled=None):
    """
    Toggle or set the smooth scrolling mode.
    When enabled, terminal output uses flush=True to prevent scroll jumping.
    
    Args:
        enabled: If None, toggle the current setting. Otherwise, set to this value.
    
    Returns:
        The new setting (True or False)
    """
    global SMOOTH_SCROLLING
    if enabled is None:
        SMOOTH_SCROLLING = not SMOOTH_SCROLLING
    else:
        SMOOTH_SCROLLING = bool(enabled)
    
    original_print(f"Smooth scrolling is now {'ENABLED' if SMOOTH_SCROLLING else 'DISABLED'}")
    return SMOOTH_SCROLLING

# Define and immediately call setup_logger() 
def setup_logger():
    """Set up and configure the logger"""
    try:
        header = "\n" + "="*50 + "\n"
        header += f"LOGGER STARTED AT: {get_eastern_time().strftime(API_DATETIME_FORMAT)}\n"
        header += "="*50 + "\n\n"
        
        # Use our new print which will properly prepend
        print(header)
        
        # Set up Python logging with TimedRotatingFileHandler
        # Create a logger
        logger = logging.getLogger("live")
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(message)s')
        
        # Create a rotating file handler that rolls over at midnight, keeps 30 days
        rotating_handler = TimedRotatingFileHandler(
            LOG_FILE_PATH,
            when="midnight",      # roll over at midnight
            interval=1,           # every 1 day
            backupCount=30,       # keep 30 days' worth of logs
            encoding="utf-8",     # use UTF-8 encoding
            utc=False             # use local time for rollover
        )
        rotating_handler.setLevel(logging.INFO)
        rotating_handler.setFormatter(formatter)
        
        # append the date suffix (so your files become main.logger.2025-05-04, etc.)
        rotating_handler.suffix = "%Y-%m-%d"
        
        logger.addHandler(rotating_handler)
        
        # REMOVED: Console handler causing duplication
        # The new_print() function already handles terminal output
        # No need for the logger to also send to console
        
    except Exception as e:
        original_print("Logger setup error:", e)

# Immediately call setup_logger()
setup_logger()

# Assign builtins.print = new_print
builtins.print = new_print
