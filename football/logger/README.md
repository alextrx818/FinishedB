# Main Logger System

## Overview

The Main Logger system is a critical component of the Sports Bot that captures all console output (stdout) from the application. It ensures that every piece of information printed to the console is simultaneously recorded in a log file for future reference, debugging, and data analysis.

## Components

### 1. `main_logger.py`

This is the core engine of the logging system. It works by:

- Overriding Python's built-in `print()` function to capture all console output
- Writing identical output to both the console and the log file
- Preserving all formatting, including separator characters and line endings
- Initializing automatically when imported

### 2. `main.logger`

This is the log file that contains all captured output. It:

- Preserves a complete record of everything printed to the console
- Is structured in append mode to maintain historical data
- Contains timestamps and session markers for easier log analysis
- Serves as a comprehensive audit trail of the application's runtime behavior

## How It Works

The logging mechanism uses a clever technique to intercept all `print()` calls:

1. The original `print()` function is saved as `original_print`
2. A new `print()` function is defined that:
   - Calls the original function to display output normally
   - Also writes the exact same text to the log file
3. Python's built-in `print()` is replaced with this new version
4. A banner is written to the log file when the logger starts

## Usage

To use the Main Logger system, simply:

1. Import the logger module at the top of your main script:
   ```python
   import logger.main_logger
   ```

2. Use `print()` as normal throughout your code - all output will be automatically logged to `main.logger`

There's no need to make any other code changes or call any initialization functions, as the logger is set up automatically when imported.

## Logger Filters

### Logger Filter Standards

All new logger filters **MUST** follow the official standards defined in the unified documentation:

- **[UNIFIED_LOGGER_STANDARDS.md](./UNIFIED_LOGGER_STANDARDS.md)**: The official, mandatory standard for all new logger filters

These standards ensure:
- Automatic creation of missing logger files
- Consistent formatting and timezone handling
- Daily counter rollover
- Universal prepend rule for entries
- Single-import bootstrapping in live.py

### Creating a New Logger Filter

When creating a new logger filter:

1. **Review the standards document** thoroughly
2. Follow the template provided in the standards
3. Implement the auto-creation of logger files
4. Use the universal prepend rule
5. Bootstrap in live.py using a single import:
   ```python
   import logger.log_filters.<your_filter_folder>.<your_filter_module>
   ```

**IMPORTANT**: Never modify live.py beyond adding a single import line for your filter.

## Important Notes

- The logger is designed to capture exactly what would appear in the console, including all formatting
- Never modify `main_logger.py` unless absolutely necessary, as it's a critical component of the system
- The log file (`main.logger`) is created in append mode, so it will grow over time
- Consider implementing log rotation if the file becomes too large
- The log file is stored in the same directory as `main_logger.py`

## Troubleshooting

If you encounter issues with the logging system:

1. Verify that `logger.main_logger` is imported at the top of your main script
2. Check that the log file (`main.logger`) is writable by the application
3. Confirm that the `print()` function is not being overridden elsewhere in the code
4. Verify that the path to the log file is correctly set in `main_logger.py`
