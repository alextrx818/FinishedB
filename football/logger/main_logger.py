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

# Define new_print(*args, **kwargs) that calls original_print(*args, **kwargs)
# and then prepends the exact same text to main.logger
def new_print(*args, **kwargs):
    # Get the text being printed
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    text = sep.join(str(arg) for arg in args) + end
    
    # Check if this is a MATCH line
    if text.strip().startswith("MATCH #") and " OF " in text:
        # This is a match header, we'll handle it specially and suppress normal printing
        handle_match_header(text)
        return
    
    # For all other lines, call the original print function
    original_print(*args, **kwargs)
    
    # Add to buffer if we're in buffering mode
    global buffering, buffer_lines
    if buffering:
        buffer_lines.append(text)
        # the very first blank line after environment signals block end
        if text.strip() == "":
            handle_buffer_end()
    else:
        # We're not buffering, so write directly to the log file.
        # Previously we did an inefficient read-modify-write operation.
        # Now we use thread-safe append-only writes for non-buffered content.
        try:
            with _log_lock:
                with open(LOG_FILE_PATH, 'a') as log_file:
                    log_file.write(text)
        except Exception as e:
            original_print("Logger write error:", e)

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
    
    # Print the formatted header to terminal
    original_print(formatted_header, end="")
    
    # Start buffering for the log file
    buffering = True
    buffer_lines = [formatted_header]

# Function to handle the end of a buffer
def handle_buffer_end():
    global buffering, buffer_lines
    chunk = "".join(buffer_lines)
    try:
        # Call all registered event listeners with the chunk BEFORE writing to file
        # Create a temporary buffer to capture output from listeners
        listener_output_buffer = []
        
        # Save the original print function temporarily
        __temp_print = builtins.print
        
        # Define a temporary print function to capture listener output
        def capture_print(*args, **kwargs):
            # Call the original print function for terminal output
            original_print(*args, **kwargs)
            
            # Get the separator and end values from kwargs, or use defaults
            sep = kwargs.get('sep', ' ')
            end = kwargs.get('end', '\n')
            
            # Convert all args to strings and join with separator
            text = sep.join(str(arg) for arg in args) + end
            
            # Add to our listener output buffer
            listener_output_buffer.append(text)
        
        # Replace the print function to capture listener output
        builtins.print = capture_print
        
        # Call all event listeners
        for listener in event_listeners:
            try:
                listener(chunk)
            except Exception as e:
                original_print("Listener error:", e)
        
        # Restore the original print function
        builtins.print = __temp_print
        
        # Append any captured listener output to the chunk
        if listener_output_buffer:
            chunk += "".join(listener_output_buffer)
        
        # Now write the combined chunk (original + listener output) to the file
        # Using a lock for thread safety and append instead of read+write+truncate
        with _log_lock:
            with open(LOG_FILE_PATH, "r+") as f:
                old = f.read()
                f.seek(0)
                f.write(chunk + old)
                f.truncate()
    except Exception as e:
        original_print("Logger write error:", e)
    
    # Reset buffering state
    buffering = False
    buffer_lines = []

# Define and immediately call setup_logger() 
def setup_logger():
    """Set up and configure the logger"""
    try:
        header = "\n" + "="*50 + "\n"
        header += f"LOGGER STARTED AT: {get_eastern_time().strftime(API_DATETIME_FORMAT)}\n"
        header += "="*50 + "\n\n"
        
        # Use our new print which will properly prepend
        print(header)
        
        # Optional but recommended: Add proper Python logging with console handler
        import sys
        import logging
        
        # Create a logger
        logger = logging.getLogger("live")
        logger.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Create console handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)
        
        # Add the handler to the logger
        logger.addHandler(console)
        
        # This sets up the Python logging system but doesn't actually use it yet
        # This is groundwork for future migration from print() to logger.info() etc.
        
    except Exception as e:
        original_print("Logger setup error:", e)

# Immediately call setup_logger()
setup_logger()

# Assign builtins.print = new_print
builtins.print = new_print
