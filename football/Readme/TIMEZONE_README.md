# Timestamp Standardization for Football Monitoring System

All timestamps across the football monitoring system have been standardized to use MM/DD/YYYY format with US Eastern Time (ET). This ensures consistency across all components and makes timestamps more readable for US-based users.

## Standardized Format

The following timestamp formats are now used consistently across the entire system:

- **Date Format**: MM/DD/YYYY (e.g., "05/01/2025")
- **Time Format**: HH:MM:SS AM/PM ET (e.g., "07:42:50 PM ET")
- **Combined Format**: MM/DD/YYYY HH:MM:SS AM/PM ET (e.g., "05/01/2025 07:42:50 PM ET")

## Components Affected

The following components have been updated to use the standardized timestamp format:

1. **Main Application (live.py)**
   - All console output timestamps
   - Match timestamps in detailed match information
   - "Waiting for update" messages
   - Status reports

2. **Telegram Notifications**
   - Alert timestamps
   - Status message timestamps
   - System alerts

3. **Logging System**
   - Logger startup messages
   - All logged timestamps

## Implementation Details

The timestamp standardization is implemented using constants and helper functions:

```python
import datetime
import pytz

# Define standard datetime formats as constants
DATE_FORMAT = "%m/%d/%Y"
TIME_FORMAT = "%I:%M:%S %p ET"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
CONSOLE_TIME_FORMAT = "%I:%M:%S %p ET"  # For console output only
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"  # For APIs and data

def get_eastern_time():
    """Get current time in Eastern timezone"""
    utc_now = datetime.datetime.now(pytz.utc)
    eastern = pytz.timezone('America/New_York')
    eastern_time = utc_now.astimezone(eastern)
    return eastern_time

# Example usage:
eastern_time = get_eastern_time()
formatted_date = eastern_time.strftime(DATE_FORMAT)
formatted_time = eastern_time.strftime(TIME_FORMAT)
formatted_datetime = eastern_time.strftime(API_DATETIME_FORMAT)
# Output examples: 
# - Date: "05/01/2025"
# - Time: "07:42:50 PM ET"
# - DateTime: "05/01/2025 07:42:50 PM ET"
```

## Benefits

Using standardized timestamp formats provides several benefits:

1. **Improved Readability**
   - MM/DD/YYYY is familiar to US-based users
   - AM/PM format is more intuitive than 24-hour format for many users
   - The "ET" suffix clearly indicates the timezone

2. **Consistent User Experience**
   - Same format used everywhere across the application
   - No confusion when comparing timestamps from different parts of the system

3. **Easier Debugging and Monitoring**
   - Timestamps in logs and console output match exactly
   - More natural format for verbal communication about timestamps

## Notes

- The system automatically handles Daylight Saving Time transitions
- The 'America/New_York' timezone identifier is used instead of 'US/Eastern' for better compatibility
- All raw timestamp data from API responses remains in the format provided by the source
- All timestamp constants are defined in live.py and imported by other modules to ensure consistency
