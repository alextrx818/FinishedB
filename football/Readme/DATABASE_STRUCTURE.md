# Sports Bot - Database Structure Documentation

## Overview
The sports bot system uses [Supabase](https://supabase.com/) as its database provider to store both match data and log information. This document explains the database architecture, connection methods, and data flows.

## Connection Method
- **Provider**: Supabase cloud database
- **Connection Library**: Supabase Python client library
- **Authentication**: Uses service role key stored in `SUPABASE_KEY` environment variable
  - Fallback to `SUPABASE_SERVICE_KEY` if the primary variable isn't set
- **URL**: Configured via `SUPABASE_URL` environment variable (default: "https://pryhbrttsgamlqxvwiap.supabase.co")

## Tables and Data Structure

### 1. `archived_json` Table
Stores the full match data JSON for every processed match.

**Schema:**
```sql
CREATE TABLE archived_json (
    id SERIAL PRIMARY KEY,
    raw_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Data Flow:**
- Match data is generated in `live.py` within the `process_live_matches_async` function
- When a match is processed, its data is printed with the marker `__MATCH_JSON__`
- This marker triggers the archiving process
- Data is inserted into the `archived_json` table via `archive_match_json()` function in `logger/db_api.py`

### 2. `main_logger_logs` Table
Stores log chunks from the main.logger file for redundancy and easier querying.

**Data Flow:**
- The `send_to_db()` function in `main_logger.py` is registered as an event listener
- When log chunks are generated, they're sent to this table via the Supabase client
- This creates a database backup of all logs in addition to the file-based logs

## Implementation Details

### Database API Module
Located at `/root/CascadeProjects/sports_bot/football/logger/db_api.py`

This module:
- Initializes the Supabase client connection
- Provides the `archive_match_json()` function to store match data
- Includes error handling and troubleshooting guidance

### Logger Integration
Located at `/root/CascadeProjects/sports_bot/football/logger/main_logger.py`

This module:
- Intercepts all `print()` calls
- Sends log chunks to both file and database
- Specifically excludes JSON data from log files (but ensures it goes to the database)
- Uses event listeners to handle database operations

## Configuration and Maintenance

### Environment Variables
- `SUPABASE_URL`: The URL of your Supabase instance
- `SUPABASE_KEY`: Your service role key (preferred)
- `SUPABASE_SERVICE_KEY`: Alternative location for service role key (fallback)

### Common Troubleshooting
- Permission denied errors usually indicate an issue with the service role key
- "Table does not exist" errors require creating the appropriate tables in Supabase

## Recent Changes
- Migrated from direct REST API calls to the official Supabase Python client library for better maintainability and features
- Added fallback mechanism to check both `SUPABASE_KEY` and `SUPABASE_SERVICE_KEY` environment variables
- Improved error handling and logging for database operations
