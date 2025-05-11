# Sports Bot Memory Optimization Guide

## Overview

This document describes the memory optimization improvements made to the sports bot system, specifically to `live.py`, which is the foundation of the sports bot project. These optimizations were implemented to reduce memory usage, prevent memory leaks, and improve overall system performance.

## Memory Optimization Features

The following memory optimization features have been implemented in `live.py`:

1. **Fetch Cycle Counter**
   - Module-level `_fetch_cycle` counter tracks processing cycles
   - Used for conditional operations like garbage collection and output formatting
   - Incremented with each iteration of the main processing loop

2. **Garbage Collection**
   - Python's garbage collector (`gc.collect()`) is called periodically
   - Helps free memory that Python's automatic memory management might not immediately reclaim
   - Runs automatically after match processing completes

3. **Collection Size Limiting**
   - The `previous_matches` collection is limited to a maximum of 100 entries
   - When the limit is exceeded, oldest entries are removed
   - Prevents unbounded memory growth over time

4. **Memory Usage Monitoring**
   - Memory statistics are displayed at the end of each processing cycle
   - Shows the size of important collections like `previous_matches` and `deferred_alerts`
   - Helps identify potential memory issues during runtime

## Implementation Details

The memory optimizations were implemented through several phases:

1. Initial implementation of memory management with `memory_optimizer.py`
2. Cleanup of redundant code with `clean_memory_optimizer.py`
3. Verification that all memory optimizations function correctly

### Code Changes

The following key code changes were made to `live.py`:

```python
# Top of file - Module level counter
_fetch_cycle = 0

# Inside process_live_matches_async function
global PROCESSING_MATCHES, _fetch_cycle
PROCESSING_MATCHES = True
_fetch_cycle += 1

# At the end of processing, cleanup and memory management
process_live_matches_async.deferred_alerts.clear()

# Memory optimization: Garbage collection
import gc
gc.collect()
print(f"Garbage collection performed on cycle {_fetch_cycle}")

# Collection size limiting
if len(process_live_matches_async.previous_matches) > 100:
    print(f"Trimming previous_matches from {len(process_live_matches_async.previous_matches)} to 100 entries")
    
    # Sort matches by timestamp (oldest first)
    entries = sorted(
        process_live_matches_async.previous_matches.items(),
        key=lambda x: x[1].get('timestamp', 0) if isinstance(x[1], dict) else 0
    )
    
    # Remove oldest entries beyond the 100 limit
    for match_id, _ in entries[:-100]:
        del process_live_matches_async.previous_matches[match_id]

# Memory usage reporting
print(f"\n----- MEMORY STATS -----")
print(f"Previous matches: {len(process_live_matches_async.previous_matches)}")
print(f"Deferred alerts: {len(process_live_matches_async.deferred_alerts)}")
print("-" * 30)
```

## Running the Sports Bot

**IMPORTANT**: The sports bot system must ONLY be started directly through the Python command:
```
python3 live.py
```

Do NOT use systemd services (like sportsbot.service) to manage this application, even though they exist. Using systemd services causes notification issues with Telegram.

## Performance Impact

These memory optimizations provide the following benefits:

1. **Reduced Memory Footprint**: By limiting collection sizes and triggering garbage collection
2. **Prevention of Memory Leaks**: Through proper cleanup of temporary data
3. **Better Performance**: Less memory pressure leads to more responsive processing
4. **Improved Stability**: Prevents crashes due to memory exhaustion
5. **Monitoring Capabilities**: Memory usage statistics help identify issues early

## Backup Files

The following backup files were created during the optimization process:

- `live.py.memory_backup`: Original backup created by memory_optimizer.py
- `live.py.memory_optimization_backup`: Secondary backup from another optimization attempt
- `live.py.pre_cleanup_backup`: Backup created before cleaning up redundant optimizations
- `live.py.clean_backup`: Backup created during the final cleanup process

These files can be used to restore previous versions if needed.

## Maintenance Notes

When making future changes to `live.py`, be cautious not to disrupt the memory optimization features. In particular:

1. Keep the `_fetch_cycle` counter and its increment in `process_live_matches_async`
2. Maintain the collection size limiting code for `previous_matches`
3. Preserve the garbage collection calls
4. Keep the memory statistics reporting

These features are critical for maintaining the performance and stability of the sports bot system.

## Last Updated

May 11, 2025
