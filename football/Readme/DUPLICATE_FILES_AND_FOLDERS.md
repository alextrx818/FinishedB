# Project Organization: Avoiding Duplicate Files and Components

This document establishes critical rules for maintaining a clean and manageable project structure by avoiding duplicate functionality.

## The Single Component Rule

**Centralized functionality is the backbone of sustainable project architecture.**

### Key Components and Their Canonical Locations

| Component | Canonical Location | Purpose |
|-----------|-------------------|---------|
| **Telegram** | `football/telegram/` | All Telegram notification functionality |
| **Start Scripts** | `football/Start_sh/` | All scripts related to starting/stopping the system |
| **Logs** | `football/logs/` | All log files and logging functionality |
| **Documentation** | `football/Readme/` | All documentation and README files |
| **Alerts** | `football/alerts/` | All alert conditions and processing |

## The Rule

1. **Never duplicate functionality across the project**
   - If adding Telegram functionality, use/extend what's in the `telegram` folder
   - If adding startup/process management, use/extend what's in the `Start_sh` folder
   - If adding logging functionality, use/extend what's in the `logs` folder

2. **Always use the canonical import paths**
   - Use `from football.telegram import ...` for all Telegram functionality
   - Use the dedicated module for each component

3. **Extend, don't duplicate**
   - If new functionality is needed, extend the existing modules
   - Add new methods or classes to existing files when possible
   - Only create new files when introducing truly new concepts

## Why This Matters

Duplicated code and functionality are the source of many bugs and maintenance challenges:

1. **Bug propagation**: Fix in one place, miss it in another
2. **Inconsistent behavior**: Different implementations behave differently
3. **Maintenance burden**: Changes need to be applied in multiple places
4. **Cognitive load**: Developers need to remember multiple implementations

## Examples of Proper Use

### Telegram Example
```python
# CORRECT: Using the centralized Telegram system
from football.telegram import send_message
send_message("Match update received")

# INCORRECT: Direct implementation in other modules
# Don't do this!
def send_telegram_alert(message):
    # Custom implementation...
```

### Startup Example
```bash
# CORRECT: Using the centralized startup script
./Start_sh/start_monitor.sh --terminal

# INCORRECT: Creating additional scripts with similar functionality
# Don't create run_football.sh or start_live.sh with overlapping functionality
```

### Logging Example
```python
# CORRECT: Using the centralized logging system
from football.logger import get_logger
logger = get_logger(__name__)
logger.info("Process started")

# INCORRECT: Creating custom logging setups in individual modules
# Don't do this!
def setup_custom_logging():
    # Custom implementation...
```

## Enforcement

This rule should be strictly enforced during code reviews and development to maintain code quality and project maintainability.

When in doubt about where new functionality should go, consult this document or extend it to cover new categories as they emerge.

## Legacy Code

While this rule may not have been strictly followed in the past, all new development and refactoring should adhere to these principles to gradually improve the project structure.
