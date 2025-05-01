import os
import builtins
import datetime
import pytz

# Build LOG_FILE_PATH pointing to main.logger in the same folder
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "main.logger")

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

# Save builtins.print as original_print
original_print = builtins.print

# Define new_print(*args, **kwargs) that calls original_print(*args, **kwargs)
# and then appends the exact same text (honoring sep/end) to main.logger
def new_print(*args, **kwargs):
    # Call the original print function
    original_print(*args, **kwargs)
    
    # Get the separator and end values from kwargs, or use defaults
    sep = kwargs.get('sep', ' ')
    end = kwargs.get('end', '\n')
    
    # Convert all args to strings and join with separator
    text = sep.join(str(arg) for arg in args) + end
    
    # Append to the log file
    with open(LOG_FILE_PATH, 'a') as log_file:
        log_file.write(text)

# Assign builtins.print = new_print
builtins.print = new_print

# Define and immediately call setup_logger() 
def setup_logger():
    """Set up and configure the logger"""
    with open(LOG_FILE_PATH, 'a') as log_file:
        log_file.write("\n" + "="*50 + "\n")
        eastern_time = get_eastern_time()
        log_file.write(f"LOGGER STARTED AT: {eastern_time.strftime(API_DATETIME_FORMAT)}\n")
        log_file.write("="*50 + "\n\n")
    print("Logger started...")

# Immediately call setup_logger()
setup_logger()
