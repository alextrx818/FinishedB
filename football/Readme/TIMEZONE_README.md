# Timezone Configuration for Football Monitoring System

All timestamps across the football monitoring system have been configured to use US Eastern Standard Time (EST/EDT) instead of UTC. This ensures that all logs, alerts, and timestamps are displayed in the timezone most relevant for US sports betting and monitoring.

## Components Affected

The following components have been updated to use US Eastern Time:

1. **Daily Log Fetcher**
   - Log file names (format: `football_fetches_YYYY-MM-DD.log`)
   - Timestamps within log entries

2. **Log Alerts System**
   - Alert timestamps
   - Log entry timestamps in `log_alerts.log`

3. **Football Alerts**
   - All Telegram alert timestamps
   - Alert logging timestamps

## Implementation Details

The timezone conversion is implemented using Python's `pytz` library:

```python
import datetime
import pytz

def get_eastern_time():
    """Get current time in US Eastern timezone (handles DST automatically)"""
    utc_now = datetime.datetime.now(pytz.utc)
    eastern = pytz.timezone('US/Eastern')
    return utc_now.astimezone(eastern)

# Example usage:
eastern_time = get_eastern_time()
formatted_time = eastern_time.strftime("%Y-%m-%d %H:%M:%S %Z")
# Output example: "2025-04-29 19:49:25 EDT"
```

## Benefits

Using Eastern Time provides several benefits:

1. **Better Alignment with US Betting Markets**
   - Most major US sportsbooks operate on Eastern Time
   - Game schedules are typically listed in Eastern Time 

2. **Improved Log Analysis**
   - All timestamps align with typical US business hours
   - Easier to correlate match times with betting activity

3. **Clearer Communication**
   - Alert times immediately recognizable without conversion
   - Reduced confusion when reviewing historical data

## Notes

- The system automatically handles Daylight Saving Time transitions
- All raw timestamp data from API responses remains in the format provided by the source
- Internal timestamp processing still uses UTC for calculations before converting to Eastern Time for display
