# Sports Bot Telegram Alert System

## Overview

The Telegram Alert System is a comprehensive monitoring and notification system integrated throughout the Sports Bot. It ensures that critical errors and system events are reported via Telegram while allowing the application to continue running regardless of component failures.

## File Organization

**Main Location: `/root/CascadeProjects/sports_bot/football/telegram/alerts.py`**: Core alert sending functionality (renamed from `notifier.py`)
- `/football/telegram/__init__.py`: Package exports
- `/football/live.py`: Alert integration for main app
- `/football/logger/main_logger.py`: Alert integration for logger

**Note:** The original `alerts.py` file in the football directory has been removed to avoid confusion with the Telegram alert system.

## Core Design Principles

1. **Resilience First**: The system continues running even if components fail
2. **Comprehensive Monitoring**: All critical modules are verified at startup and monitored during runtime
3. **Error Isolation**: Errors in one subsystem don't crash the entire application
4. **Real-time Alerts**: All significant failures generate immediate Telegram notifications
5. **Graceful Degradation**: Features disable independently when dependencies aren't available

## Alert Types

| Type | Priority | Description |
|------|----------|-------------|
| Error | High | Critical issues that severely impact functionality |
| Warning | Medium | Non-critical issues that may affect some features |
| Info | Low | Informational messages about system status |

## Monitored Components

### 1. Database Connection
- **Monitors**: Supabase connectivity
- **Alert Triggers**: Connection failures, authentication errors
- **Recovery**: Operates without database functionality when unavailable

### 2. Logging System
- **Monitors**: File creation/writing, log rotation, event listeners
- **Alert Triggers**: File system errors, listener failures, buffer processing issues
- **Recovery**: Continues with console logging if file logging fails

### 3. Critical Modules
- **Monitors**: All essential modules via startup verification
- **Alert Triggers**: Missing or broken modules
- **Coverage**:
  - Logger components (`main_logger.py`, filters, handlers)
  - Alert components (`telegram`, `telegram/alerts.py`)
  - Core functionality (`live.py`, analyzers)
  - Database components

## Implementation Details

### Error Handling Architecture

All critical operations are wrapped in appropriate error handling:

```python
try:
    # Critical operation
    perform_operation()
except Exception as e:
    # Log error locally
    print(f"Error: {e}")
    
    # Continue operation in degraded mode
    handle_degraded_mode()
    
    # Send alert
    try:
        send_system_alert("Operation failed", 
                         alert_type="error", 
                         error_details=str(e))
    except Exception as alert_error:
        # Even alert failures won't stop the program
        print(f"Could not send alert: {alert_error}")
```

### Module Verification System

- The module verification system has been integrated directly into `live.py`
- Performs checks of all critical modules at startup
- Sends alerts for verification failures

### Supabase Error Handling

- Located in both `live.py` and `main_logger.py`
- All Supabase operations wrapped in try/except blocks
- `SUPABASE_AVAILABLE` flag tracks connection status
- All database operations only execute when flag is `True`

### Logger Failure Handling

- Multiple points of error handling in `main_logger.py`
- File operations in setup_logger() and handle_buffer_end()
- Event listener calls protected from failures
- Careful import management to avoid circular dependencies

## Testing

The alert system can be tested using the included `test_alerts.py` script which:

1. Tests module verification alerts
2. Simulates Supabase connection failures
3. Creates controlled logger failures

Run the test with:
```
python3 test_alerts.py
```

## Alert Messages Format

Alert messages include:
- Alert type icon (⚠️ for warnings, 🔴 for errors, etc.)
- Bold title indicating the subsystem and issue
- Detailed error message
- Timestamp in Eastern timezone (ET)

## Design Notes

1. **Circular Import Prevention**:
   - Alert sending code imports modules dynamically to avoid circular import issues
   - Uses importlib when necessary in error handlers

2. **Prioritized Output**:
   - Critical errors always generate console output regardless of alert status
   - Alert failures are logged but don't prevent continued operation

3. **Independence**:
   - System is designed to work even without Telegram connectivity
   - All components function independently where possible

## Maintenance Guidelines

When extending the system:

1. Always preserve the "continue running" principle
2. Add try/except around all new critical operations
3. Add Telegram alerts for any new failure modes
4. Test failure scenarios to ensure the system continues running
5. Use proper import patterns to avoid circular dependencies

## Commands

- `python3 alerts.py --verify`: Run module verification separately
- `python3 test_alerts.py`: Test the alert system components

---

*This system ensures that failures are both visible (via Telegram) and survivable (via error handling), providing maximum uptime for the sports bot while keeping operators informed of any issues.*
