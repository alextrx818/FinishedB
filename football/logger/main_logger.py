"""
# EDIT REPORT - 2025-05-09
# Impact of Resilience Enhancements on Logger System
#
# Changes impacting this file:
# 1. Combined failure test temporarily renames this file to test import error handling
# 2. Error handling in live.py now properly reports main_logger import failures
# 3. All send_system_alert() calls now use standardized alert severity levels
#
# See EDIT_REPORT_TEST.md for complete details.
#
================================================================
CRITICAL SYSTEM INDEPENDENCE NOTE:
================================================================
This main_logger.py system MUST function independently of Supabase.
Specifically:

1. The main.logger file MUST be created even if Supabase connection fails
2. This module MUST operate even without database connectivity
3. All logging to file MUST work regardless of external service status

IF YOU MODIFY THIS FILE: Ensure these principles are preserved!
================================================================

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
import json
from logging.handlers import TimedRotatingFileHandler

# Try to import supabase but make it optional
try:
    from supabase_config import supabase
    SUPABASE_AVAILABLE = bool(supabase)  # Will be True if supabase connection exists
except (ImportError, Exception) as e:
    original_print = builtins.print  # Save original print before we override it
    original_print(f"Supabase import error: {e}")
    supabase = None
    SUPABASE_AVAILABLE = False

class SupabaseHandler(logging.Handler):
    def emit(self, record):
        if SUPABASE_AVAILABLE and supabase:
            try:
                supabase.table("logs").insert({
                    "level": record.levelname,
                    "msg":   record.getMessage(),
                    "time":  record.created
                }).execute()
            except Exception as e:
                # Using original_print here to avoid circular reference with new_print
                if hasattr(builtins, 'original_print'):
                    builtins.original_print(f"Supabase logging error: {e}")

# Add threading lock for thread-safe file operations
_log_lock = threading.Lock()

# Add event listener list for callbacks
event_listeners = []

# Dictionary to track alert loggers
alert_loggers = {}

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
    from live import API_DATETIME_FORMAT
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

# Ensure smooth scrolling is enabled to prevent auto-scrolling while viewing log files
SMOOTH_SCROLLING = True  # This ensures the log file doesn't auto-scroll when viewed

# Define the database listener function using Supabase client
def send_to_db(chunk: str):
    """Send log chunk to Supabase database using Python client"""
    try:
        # If this is the JSON payload from live.py, send it to archived_json
        if chunk.startswith("▶️ PAYLOAD:"):
            # strip off the prefix and parse JSON
            json_str = chunk[len("▶️ PAYLOAD:"):].strip()
            try:
                data = json.loads(json_str)
            except Exception as e:
                original_print(f"⚠️ JSON parse error: {e}")
                return
            resp = supabase.table("archived_json").insert({"raw_json": data}).execute()
            if getattr(resp, "error", None):
                original_print("   ❌ INSERT FAILED:", resp.error)
            else:
                original_print("   ✅ Inserted, DB row id:", resp.data[0]["id"])
        else:
            # Insert the log chunk into main_logger_logs table
            original_print("▶️ PAYLOAD:", chunk, flush=True)
            response = supabase \
                .table("main_logger_logs") \
                .insert({"content": chunk}) \
                .execute()
            if getattr(response, "error", None):
                original_print("   ❌ INSERT FAILED:", response.error)
            else:
                original_print("   ✅ Inserted, DB row id:", response.data[0]["id"], flush=True)
    except Exception as e:
        original_print(f"⚠️ Supabase logging error: {str(e)}")

# Register the listener if supabase is available
if SUPABASE_AVAILABLE and supabase:
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
    if not buffering:
        return
    
    # Add a blank line after match to help readability
    buffer_lines.append("\n")
    
    try:
        with _log_lock:
            chunk = "".join(buffer_lines)
            
            # Don't replace the global print function - this causes processing interruptions
            # Just use direct tracking of listener output
            listener_output_buffer = []
            
            # Call each listener on the current buffer
            for listener in event_listeners:
                try:
                    # Capture any print output from the listener in a controlled way
                    # by redirecting sys.stdout temporarily
                    original_stdout = sys.stdout
                    try:
                        # Use StringIO to capture output instead of globally replacing print
                        from io import StringIO
                        captured_output = StringIO()
                        sys.stdout = captured_output
                        
                        # Call the listener with the log chunk
                        listener(chunk)
                        
                        # Get any output and add to our buffer
                        output = captured_output.getvalue()
                        if output:
                            listener_output_buffer.append(output)
                    finally:
                        # Always restore stdout even if there's an exception
                        sys.stdout = original_stdout
                except Exception as e:
                    error_msg = f"Listener error: {e}"
                    original_print(error_msg)
                    # Try to send alert about listener failure
                    try:
                        # Import these only when needed to avoid circular imports
                        import importlib
                        telegram_mod = importlib.import_module("football.telegram")
                        if hasattr(telegram_mod, "send_system_alert"):
                            telegram_mod.send_system_alert(
                                f"Logger listener failed during processing",
                                alert_type="warning",
                                error_details=error_msg
                            )
                    except Exception as alert_error:
                        original_print(f"Could not send alert about listener failure: {alert_error}")
        
        # Add any captured output from listeners to our chunk
        chunk += "".join(listener_output_buffer)
        
        # IMPORTANT: Actually write the data to the log file
        # This is the missing piece - we need to use the logger here
        if chunk.strip():  # Only log non-empty chunks
            try:
                logger = logging.getLogger("live")
                logger.info(chunk.strip())
            except Exception as log_error:
                error_msg = f"Failed to write to log file: {log_error}"
                original_print(f"CRITICAL ERROR: {error_msg}")
                # Try to send alert about log writing failure
                try:
                    # Import these only when needed to avoid circular imports
                    import importlib
                    telegram_mod = importlib.import_module("football.telegram")
                    if hasattr(telegram_mod, "send_system_alert"):
                        telegram_mod.send_system_alert(
                            "CRITICAL: Failed to write to main.logger file",
                            alert_type="error",
                            error_details=error_msg
                        )
                except Exception as alert_error:
                    original_print(f"Could not send alert about log writing failure: {alert_error}")
        
    except Exception as e:
        error_msg = f"Logger write error: {e}"
        original_print(error_msg)
        # Try to send alert about overall buffer handling failure
        try:
            # Import these only when needed to avoid circular imports
            import importlib
            telegram_mod = importlib.import_module("football.telegram")
            if hasattr(telegram_mod, "send_system_alert"):
                telegram_mod.send_system_alert(
                    "CRITICAL: Logger buffer processing failed",
                    alert_type="error",
                    error_details=error_msg
                )
        except Exception as alert_error:
            original_print(f"Could not send alert about buffer processing failure: {alert_error}")
    
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
def setup_module_logger(module_name, custom_log_file=None):
    """
    Set up a module-specific logger that integrates with the main logging system.
    
    Args:
        module_name: Name of the module (used for log identification)
        custom_log_file: Optional custom log file name (e.g., 'fetcher.logger')
        
    Returns:
        A configured logger instance for the module
    """
    logger = logging.getLogger(f"live.{module_name}")
    logger.setLevel(logging.INFO)
    
    # Check if handlers are already set up to avoid duplicates
    if not logger.handlers:
        try:
            # Determine log file path
            if custom_log_file:
                # Use a module-specific log file in the logger directory
                log_path = os.path.join(os.path.dirname(__file__), custom_log_file)
            else:
                # Default to the main logger file
                log_path = os.path.join(os.path.dirname(__file__), "main.logger")
                
            # Create the file handler for this module's logs
            file_handler = logging.FileHandler(log_path)
            
            # Use the same formatter as the main logger
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add the handler to the logger
            logger.addHandler(file_handler)
            
            # Add a console handler for terminal output
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # Success message identifying where logs will be written
            if custom_log_file:
                logger.info(f"Module logger for {module_name} initialized successfully (writing to {custom_log_file})")
            else:
                logger.info(f"Module logger for {module_name} initialized successfully (writing to main.logger)")
        except Exception as e:
            # If it fails, set up a basic console logger as fallback
            console_handler = logging.StreamHandler()
            logger.addHandler(console_handler)
            logger.warning(f"Error setting up file handler for {module_name}: {e}")
    
    return logger

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
        try:
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
        except Exception as file_error:
            original_print(f"CRITICAL ERROR: Could not set up log file: {file_error}")
            # Try to send alert about logging failure
            try:
                # Import these only when needed to avoid circular imports
                import importlib
                telegram_mod = importlib.import_module("football.telegram")
                if hasattr(telegram_mod, "send_system_alert"):
                    telegram_mod.send_system_alert(
                        "CRITICAL: Failed to create main.logger file",
                        alert_type="error",
                        error_details=str(file_error)
                    )
            except Exception as alert_error:
                original_print(f"Could not send alert about logger failure: {alert_error}")
            # Continue anyway - we'll operate without file logging
        
        # Add Supabase handler only if available
        if SUPABASE_AVAILABLE and supabase:
            try:
                supabase_handler = SupabaseHandler()
                supabase_handler.setLevel(logging.INFO)
                logger.addHandler(supabase_handler)
            except Exception as e:
                error_msg = f"Failed to add Supabase handler: {e}"
                original_print(error_msg)
                # Try to send alert about Supabase handler failure
                try:
                    # Import these only when needed to avoid circular imports
                    import importlib
                    telegram_mod = importlib.import_module("football.telegram")
                    if hasattr(telegram_mod, "send_system_alert"):
                        telegram_mod.send_system_alert(
                            "Failed to initialize Supabase logging handler",
                            alert_type="warning",
                            error_details=error_msg
                        )
                except Exception as alert_error:
                    original_print(f"Could not send alert about Supabase handler failure: {alert_error}")
        
        # REMOVED: Console handler causing duplication
        # The new_print() function already handles terminal output
        # No need for the logger to also send to console
        
    except Exception as e:
        error_msg = f"Logger setup error: {e}"
        original_print(error_msg)
        # Try to send alert about overall logger setup failure
        try:
            # Import these only when needed to avoid circular imports
            import importlib
            telegram_mod = importlib.import_module("football.telegram")
            if hasattr(telegram_mod, "send_system_alert"):
                telegram_mod.send_system_alert(
                    "CRITICAL: Logger setup failed completely",
                    alert_type="error",
                    error_details=error_msg
                )
        except Exception as alert_error:
            original_print(f"Could not send alert about logger setup failure: {alert_error}")

# Create a logger for an alert module
def create_alert_logger(module_name):
    """
    Create a dedicated logger for an alert module.
    
    Args:
        module_name: Name of the alert module (without .py extension)
        
    Returns:
        A configured logger instance for the specified alert module
    """
    if module_name in alert_loggers:
        return alert_loggers[module_name]
    
    # Skip creating log files for orchestrator/system modules
    orchestrator_modules = ['orchestrator', 'match_alerts', 'system']
    
    # Set up the logger
    alert_logger = logging.getLogger(f'sports_alerts.{module_name}')
    alert_logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in alert_logger.handlers[:]:  
        alert_logger.removeHandler(handler)
    
    # For orchestrator modules, only create a console handler (no file)
    if module_name.lower() in orchestrator_modules:
        console = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        alert_logger.addHandler(console)
        
        # Store in dictionary
        alert_loggers[module_name] = alert_logger
        return alert_logger
        
    # For actual alert modules, create a dedicated log file
    try:
        # Create alerts directory if it doesn't exist
        alerts_dir = os.path.join(os.path.dirname(LOG_FILE_PATH), 'alerts')
        os.makedirs(alerts_dir, exist_ok=True)
        
        # Create log file path
        log_file = os.path.join(alerts_dir, f'{module_name}.log')
        
        # Create a rotating file handler
        handler = TimedRotatingFileHandler(
            log_file,
            when="midnight",      # roll over at midnight
            interval=1,           # every 1 day
            backupCount=30,       # keep 30 days' worth of logs
            encoding="utf-8",     # use UTF-8 encoding
            utc=False             # use local time for rollover
        )
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        alert_logger.addHandler(handler)
        
        # Also add a console handler for debugging
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        alert_logger.addHandler(console)
        
        # Store in dictionary
        alert_loggers[module_name] = alert_logger
        
        original_print(f"✓ Created alert logger for {module_name} at {log_file}")
        return alert_logger
        
    except Exception as e:
        error_msg = f"Failed to create alert logger for {module_name}: {e}"
        original_print(error_msg)
        # Return a NullLogger that won't crash when used
        null_logger = logging.getLogger(f'null.{module_name}')
        null_logger.addHandler(logging.NullHandler())
        return null_logger

# Function to get or create an alert logger
def get_alert_logger(module_name):
    """
    Get an existing alert logger or create a new one.
    
    Args:
        module_name: Name of the alert module (without .py extension)
    
    Returns:
        A configured logger for the specified module
    """
    if module_name not in alert_loggers:
        return create_alert_logger(module_name)
    return alert_loggers[module_name]

# Immediately call setup_logger()
setup_logger()

# Assign builtins.print = new_print
builtins.print = new_print
