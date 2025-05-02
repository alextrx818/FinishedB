import os
import builtins
import datetime
import pytz

# Build LOG_FILE_PATH pointing to main.logger in the same folder
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.logger")

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
    # Call the original print function
    original_print(*args, **kwargs)
    
    # Get the separator and end values from kwargs, or use defaults
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    
    # Convert all args to strings and join with separator
    text = sep.join(str(arg) for arg in args) + end
    
    # BEFORE anything else in new_print, insert:
    global buffering, buffer_lines, last_log_date, daily_summary_count
    
    # Detect live.py's MATCH header
    if not buffering and text.strip().startswith("MATCH #"):
        # determine current ET date for summary counter
        current_date_obj = get_eastern_time()
        current_date_iso = current_date_obj.strftime("%Y-%m-%d")
        current_date_std = format_date(current_date_obj)
        current_time = current_date_obj.strftime("%I:%M:%S %p ET")
        
        # handle date rollover
        if current_date_iso != last_log_date:
            last_log_date = current_date_iso
            daily_summary_count = 0
            # prepend a big date banner
            date_banner = (
                "\n" + "="*60 + "\n"
                f"  NEW LOG DATE: {current_date_std}\n"
                + "="*60 + "\n\n"
            )
        else:
            date_banner = ""
            
        # increment your daily counter
        daily_summary_count += 1
        summary_banner = f"--- Summary Set #{daily_summary_count} for {current_date_std} --- {current_time}\n"
        
        # build block header using live.py's MATCH line
        block_header = date_banner
        block_header += "="*50 + "\n"
        block_header += text                # <-- this is the exact MATCH #x OF y line
        block_header += "="*50 + "\n\n"
        
        # start buffering the rest of the block
        buffering = True
        buffer_lines.clear()
        buffer_lines.append(summary_banner + block_header)
        return
    
    if buffering:
        buffer_lines.append(text)
        # the very first blank line after environment signals block end:
        if text.strip() == "":
            chunk = "".join(buffer_lines)
            try:
                with open(LOG_FILE_PATH, "r+") as f:
                    old = f.read()
                    f.seek(0)
                    f.write(chunk + old)
                    f.truncate()
            except Exception as e:
                original_print("Logger write error:", e)
            buffering = False
            buffer_lines.clear()
        return
    
    # FALL BACK to normal per-line prepend for anything outside a match block
    try:
        # Open file for read/write
        if os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, 'r+') as log_file:
                # Read existing contents
                existing_content = log_file.read()
                # Seek back to start
                log_file.seek(0)
                # Write new text first, then old content
                log_file.write(text + existing_content)
                # Truncate the file to remove any potential leftover bytes
                log_file.truncate()
        else:
            # If file doesn't exist, create it and write the text
            with open(LOG_FILE_PATH, 'w') as log_file:
                log_file.write(text)
    except Exception as e:
        original_print("Logger write error:", e)

# Assign builtins.print = new_print
builtins.print = new_print

# Define and immediately call setup_logger() 
def setup_logger():
    """Set up and configure the logger"""
    try:
        header = "\n" + "="*50 + "\n"
        header += f"LOGGER STARTED AT: {get_eastern_time().strftime(API_DATETIME_FORMAT)}\n"
        header += "="*50 + "\n\n"
        
        # Use our new print which will properly prepend
        print(header)
    except Exception as e:
        original_print("Logger setup error:", e)

# Immediately call setup_logger()
setup_logger()
