# Sports Bot - RAM Usage Analysis

## Memory Usage Overview

This document provides an analysis of memory usage in the sports bot system, identifying components that consume the most RAM and providing optimization recommendations.

## High Memory Usage Components

### 1. JSON Data Processing and Buffering
- **Match data JSON objects**: The `match_data` objects stored in memory could be substantial, especially if many matches are processed simultaneously
- **Impact**: Medium to High (depends on number of concurrent matches and JSON size)
- **Location**: Primarily in `live.py` within `process_live_matches_async`

### 2. Log Buffering System
- **Buffer accumulation**: The `buffer_lines` list in `main_logger.py` accumulates log data before writing to file
- **Impact**: Medium (particularly during large match summaries)
- **Location**: `main_logger.py` via global variables `buffering` and `buffer_lines`
- **Memory concern**: If many matches generate large outputs before a buffer flush occurs

### 3. Print Interception Mechanism
- **Function redefinition**: Redefining `builtins.print` creates overhead for every print call
- **Temporary buffers**: Each print generates temporary string objects for dual output
- **Impact**: Medium (due to high frequency of calls)
- **Location**: `main_logger.py` function `new_print()`

### 4. TimedRotatingFileHandler
- **File handles**: Maintains open file handles for log rotation
- **Buffering**: May buffer content before writing to disk
- **Impact**: Low to Medium
- **Location**: `main_logger.py` in `setup_logger()`

### 5. Supabase Client
- **Connection pool**: Maintains database connections
- **Request/response objects**: Creates temporary objects for API calls
- **Impact**: Low (unless making many concurrent DB calls)
- **Location**: `db_api.py` when initializing `supabase`

## Memory Optimization Recommendations

1. **Implement batch processing**:
   - Process matches in smaller batches rather than all at once
   - Reduce the number of concurrent match objects in memory

2. **Optimize buffer flushing**:
   - Add size limits to `buffer_lines` to prevent excessive memory use
   - Implement forced flushing when buffer exceeds certain size

3. **Optimize JSON handling**:
   - Consider using streaming JSON processing for large payloads
   - Implement cleanup of JSON objects after database insertion

4. **Review memory profiling**:
   - Use Python's memory_profiler to identify specific hotspots
   - Add targeted memory tracking around suspicious functions

5. **Consider database connection pooling**:
   - Review Supabase client configuration to ensure efficient connection reuse
   - Close connections when not in use

The most likely culprits for high memory usage would be the JSON data processing in `live.py` combined with the log buffering system in `main_logger.py`. The former because JSON objects can grow quite large with match data, and the latter because it accumulates text in memory before writing to disk or database.
