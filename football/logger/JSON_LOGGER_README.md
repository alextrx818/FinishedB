# JSON Logger System

## Overview

The JSON Logger is a specialized logging component for the Sports Bot system that captures raw JSON match data with consistent formatting and organization. This modular logging system ensures that all JSON data is properly timestamped, formatted, and archived for future reference.

## Key Features

### 1. Modular Design
- Implemented as a separate module (`json_logger.py`) rather than inline code
- Centralized configuration and standardized access through import
- Consistent interface: `json_logger.debug()` for all JSON logging needs

### 2. Eastern Timezone Formatting
- All timestamps use America/New_York timezone (US Eastern Time)
- Date format: MM/DD/YYYY (e.g., 05/06/2025)
- Time format: 12-hour with AM/PM (e.g., 12:38:18 PM ET)
- Consistent with the system's operational requirements

### 3. Universal Buffering and Prepending Rule
- "Newest-First" log ordering (most recent entries at the top)
- Block-based buffering preserves the structure of match data
- Detects block boundaries using 50-character separator lines (`==========`)
- Preserves intra-block formatting while maintaining chronological order

### 4. Midnight Rotation
- Daily log rotation at midnight (Eastern Time)
- Creates dated backup files: `json.log.YYYY-MM-DD`
- Starts with a fresh, empty log file each day
- Retains 7 days of historical logs (configurable)
- Clean rotation ensures no data loss during rollover

## Implementation Details

### File Structure
- **json_logger.py**: Core implementation with all logging logic
- **json.log**: Current day's JSON log (newest entries at top)
- **json.log.YYYY-MM-DD**: Historical logs from previous days

### Custom Components

#### MidnightRotatingFileHandler
Extends TimedRotatingFileHandler with custom behavior:
- Creates clean rotation with proper date-based filenames
- Ensures complete backup of all data before rotation
- Manages historical file retention based on backupCount

#### Custom Debug Methods
- `custom_debug()`: Primary logging method with buffering support
- `log_json()`: Specialized method for handling JSON data
- `log_block()`: Handles block-based logging with proper structure

#### Eastern Timezone Formatting
- Uses pytz for reliable timezone conversion
- Fallback mechanism if timezone conversion fails

## Usage Example

```python
# Import the JSON logger
from logger.json_logger import json_logger

# Log JSON data (automatically formatted with indent=2)
json_logger.debug(json.dumps(match_data, indent=2))
```

## Testing

The system includes test scripts to verify proper functionality:
- **test_json_logger.py**: Tests basic logging functionality and block structure
- **test_rotation.py**: Tests midnight rotation and backup file creation

## Integration

The JSON logger is integrated with the Sports Bot system:
1. Imported in `live.py` with: `from logger.json_logger import json_logger`
2. Used to log match data before database insertion
3. Preserves all raw JSON for debugging and archival purposes

## Universal Rules Applied

This module follows the universal logging rules defined in `PREPENDING_UNIVERSAL_RULE.md`:
- Buffering logic for block detection
- Preservation of intra-block structure
- Newest-first prepending approach
- Consistent formatting across all log types

## Maintenance

When making changes to the logging system:
1. Maintain the Eastern timezone format (America/New_York)
2. Preserve the block-based buffering for structured data
3. Ensure the prepending mechanism for newest-first ordering
4. Test both normal logging and midnight rotation

## Troubleshooting

- If timestamp errors occur, check for "Listener error: 'America/New_York'" in logs
- If log rotation doesn't occur, verify system time and timezone settings
- For manual testing, use the `force_rotation()` function to simulate midnight
