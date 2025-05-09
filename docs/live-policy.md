# Live.py Policy & Documentation Requirements

This document contains critical information about the live.py system, its error handling architecture, 
and mandatory documentation requirements for any modifications.

## Edit Report - 2025-05-09

### Resilience Enhancements to live.py

Changes made:
1. Consolidated asyncio exception handler (set up once at startup)
2. Removed unnecessary import delays (time.sleep calls)
3. Hardened PYTHONPATH bootstrap with try/except
4. Normalized alert severities across the system
5. Enhanced critical error reporting

See EDIT_REPORT_TEST.md for complete details.

## Error Handling Architecture

This file implements a multi-level approach to error handling:

1. **GLOBAL HOOKS** catch any unhandled exceptions (in main thread, worker threads, 
   and asyncio tasks) and send critical alerts before terminating

2. **OPTIONAL MODULE WRAPPING** protects against missing external dependencies
   (Supabase, Telegram) but allows the system to run with reduced functionality

3. **LOCAL TRY/EXCEPT blocks** around specific operations catch and handle
   non-fatal errors without crashing the entire system

### Alert Levels
- **CRITICAL**: Fatal errors that render the system non-functional
- **ERROR**: Significant but non-fatal issues that require attention
- **WARNING**: Minor issues or missing optional components
- **INFO**: Normal operational messages and status updates

## Change Documentation Requirement

**CRITICAL: ANY changes to live.py MUST include detailed documentation:**

1. Line-by-line report of ALL changes (added, modified, replaced, deleted)
2. Rationale explaining why each change was necessary
3. Potential system impact assessment 
4. Simple natural language summary of all changes

live.py is the FOUNDATION of the entire sports bot system and 
all changes must be thoroughly documented, justified, and tested.

## Critical System Initialization Note

This file (live.py) is the foundation of the sports bot system and 
must work regardless of external dependencies. Specifically:

1. This system MUST run even if Supabase connection fails
2. The main.logger file MUST be created independent of Supabase
3. All core functionality MUST work even if DB functionality is unavailable

IF YOU MODIFY THIS FILE: Ensure these principles are preserved!

## Output Formatting System Documentation

This file (live.py) produces output that appears in two places:
1. Terminal - where it's displayed in real-time
2. main.logger file - where it's stored for later reference

### Critical Formatting Warning

**DO NOT** attempt to modify output formatting by changing print statements 
in this file. Here's why:

1. **FORMATTING RESPONSIBILITY**:
   - ALL formatting is handled by main_logger.py, not this file
   - This file should only print raw content without formatting concerns
   - Adding separators or formatting here will cause duplicates

2. **HOW THE SYSTEM WORKS**:
   - main_logger.py intercepts all print() calls from this file
   - It formats both terminal and logger output simultaneously
   - Any formatting changes must be made in main_logger.py

3. **CORRECT APPROACH**:
   - To change output format: modify main_logger.py
   - To change content: modify the print statements here
   - Always test both terminal AND logger output after any changes

This intercept-and-format approach allows consistency between outputs
but is brittle - any changes to print format in this file will likely
break the logger system in unexpected ways.

## Execution Requirements

1. **EXECUTION METHOD**: This script MUST be executed directly as 'python3 live.py'.
   DO NOT attempt to run as a module (-m flag). The Telegram notification system
   depends on direct execution to function properly.

2. **SUPERVISOR CONFIGURATION**: Must use direct path execution in supervisor config:
   command=/usr/bin/python3 /root/CascadeProjects/sports_bot/football/live.py
   
3. **TIMEZONE REQUIREMENT**: Always set TZ="America/New_York" in the environment
