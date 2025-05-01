# Sports Bot Enhanced Logging System

This document outlines the enhanced logging system implemented for the Sports Bot application. The system provides comprehensive, structured logging while maintaining backward compatibility with existing components.

## Directory Structure

The logging system uses the following directory structure:

```
/root/CascadeProjects/sports_bot/football/logs/
├── Main_Log.log        - Primary match data in JSON format
├── Fetch_History.log   - API request history
├── Terminal_Output.log - Console output
└── analysis/
    ├── match_analysis.log  - Detailed match data analysis
    ├── odds_changes.log    - Betting line changes
    ├── errors.log          - Detailed error tracking
    └── daily_summary.log   - System performance reports
```

## Logging Components

### Standard Loggers (Original)

1. **match_logger**
   - Location: `logs/Main_Log.log`
   - Content: Match data in JSON format
   - Purpose: Main data source for match information
   - Used by: Various dependent components and analysis tools

2. **fetch_logger**
   - Location: `logs/Fetch_History.log`
   - Content: API request history
   - Purpose: Tracking API calls and responses

3. **terminal_logger**
   - Location: `logs/Terminal_Output.log`
   - Content: Console output
   - Purpose: Recording all terminal output

### Enhanced Loggers (New)

1. **match_analyzer**
   - Location: `logs/analysis/match_analysis.log`
   - Content: Detailed match data with event types
   - Format: JSON with timestamps and event categorization
   - Purpose: Deeper analysis of match progression

2. **odds_tracker**
   - Location: `logs/analysis/odds_changes.log`
   - Content: Betting line movements
   - Format: JSON with match details and odds data
   - Purpose: Tracking betting market changes

3. **error_logger**
   - Location: `logs/analysis/errors.log`
   - Content: Detailed error information
   - Format: Includes timestamp, level, file path, line number, and stack trace
   - Purpose: Comprehensive error tracking for debugging

4. **summary_logger**
   - Location: `logs/analysis/daily_summary.log`
   - Content: System performance metrics
   - Format: JSON with uptime and status information
   - Purpose: Regular system health reports
   - Rotation: Daily at midnight

## Implementation Details

All logging functionality has been integrated directly into `live.py` with the following components:

### Logger Initialization

```python
# Enhanced log file paths
match_analysis_log = os.path.join(analysis_dir, "match_analysis.log")
odds_changes_log = os.path.join(analysis_dir, "odds_changes.log")
errors_log = os.path.join(analysis_dir, "errors.log")
summary_log = os.path.join(analysis_dir, "daily_summary.log")

# Configure logging formatters
basic_formatter = logging.Formatter('%(asctime)s - %(message)s')
detailed_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s')

# Enhanced loggers
match_analyzer = logging.getLogger("match_analyzer")
match_analyzer.setLevel(logging.INFO)
match_analyzer_handler = RotatingFileHandler(match_analysis_log, maxBytes=10*1024*1024, backupCount=10)
match_analyzer_handler.setFormatter(detailed_formatter)
match_analyzer.addHandler(match_analyzer_handler)

# Additional loggers initialized similarly...
```

### Helper Functions

Three main helper functions manage the enhanced logging:

1. **log_match_analysis(match_data)**
   - Records structured match data with event type
   - Called whenever match information is processed

2. **log_odds_change(match_info, odds_data)**
   - Records betting line changes
   - Automatically tracks odds movements

3. **log_daily_summary()**
   - Creates system health snapshots
   - Called on status requests and every 6 hours

### Enhanced Error Handling

The `custom_print` function has been updated to automatically detect and log errors:

```python
def custom_print(*args, **kwargs):
    # Original functionality preserved
    original_print(*args, **kwargs)
    
    # Convert all arguments to strings and join them
    message = " ".join(str(arg) for arg in args)
    
    # Log the message to the terminal output file
    terminal_logger.info(message)
    
    # Also log ERROR and WARNING messages to the error log
    lower_msg = message.lower()
    if "error" in lower_msg or "exception" in lower_msg:
        error_logger.error(message)
    elif "warning" in lower_msg:
        error_logger.warning(message)
```

## How to Access Logs

### View Live Logs

To monitor logs in real-time:

```bash
# Main match data
tail -f /root/CascadeProjects/sports_bot/football/logs/Main_Log.log

# Match analysis
tail -f /root/CascadeProjects/sports_bot/football/logs/analysis/match_analysis.log

# Error tracking
tail -f /root/CascadeProjects/sports_bot/football/logs/analysis/errors.log
```

### Parse Structured Logs

Since all enhanced logs use JSON format, they can be easily parsed:

```bash
# Example: Extract all errors from today
grep "$(date +%Y-%m-%d)" /root/CascadeProjects/sports_bot/football/logs/analysis/errors.log | jq .

# Example: View daily summaries
cat /root/CascadeProjects/sports_bot/football/logs/analysis/daily_summary.log | jq .
```

## Extending the Logging System

To add new logging capabilities:

1. **Create a new logger** in the initialization section of `live.py`
2. **Define a helper function** to format and write to the log
3. **Call the helper function** where appropriate in the code

Example for adding a new logger:

```python
# Initialize new logger
new_logger = logging.getLogger("new_logger_name")
new_logger.setLevel(logging.INFO)
new_handler = RotatingFileHandler(
    os.path.join(analysis_dir, "new_log_name.log"), 
    maxBytes=10*1024*1024, 
    backupCount=10
)
new_handler.setFormatter(detailed_formatter)
new_logger.addHandler(new_handler)

# Create helper function
def log_new_event(data):
    try:
        # Add timestamp
        data["timestamp"] = get_eastern_time().strftime('%Y-%m-%d %H:%M:%S ET')
        # Log as JSON
        new_logger.info(json.dumps(data))
    except Exception as e:
        error_logger.error(f"Error logging new event: {e}", exc_info=True)
```

## Maintenance

The logging system includes automatic rotation to prevent excessive disk usage:

- **Size-based rotation** for most logs (10MB max with 5-10 backups)
- **Time-based rotation** for summary logs (daily at midnight with 30 backups)

No additional maintenance is required beyond occasional disk space monitoring.

## Backward Compatibility

This enhanced logging system maintains full compatibility with existing components that depend on the standard log files. All original logging functionality remains unchanged.

## Benefits of the Enhanced System

1. **Structured data** - All logs use JSON format for easier parsing and analysis
2. **Categorized information** - Different log files for different types of data
3. **Better error tracking** - Line numbers and stack traces for debugging
4. **Automatic rotation** - Prevents logs from consuming too much disk space
5. **Time-zone aware** - All timestamps use Eastern Time (ET) for consistency
