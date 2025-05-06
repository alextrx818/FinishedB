# Sports Bot Database Configuration

## Overview

This document details the database architecture, connection methods, and configuration required for the Sports Bot system. The system uses Supabase as its backend database service, connecting via the REST API to archive match data during live processing.

## Database Architecture

### Service Provider
- **Platform:** Supabase
- **Project URL:** https://pryhbrttsgamlqxvwiap.supabase.co
- **Connection Method:** REST API (not direct PostgreSQL)

### Table Structure
- **Main Table:** `archived_json`
- **Schema:**
  ```sql
  CREATE TABLE archived_json (
      id SERIAL PRIMARY KEY,
      payload JSONB NOT NULL,
      created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
  );
  ```

## Connection Configuration

### Environment Variables
Two critical environment variables must be set for the database connection to function:

1. **SUPABASE_URL**
   - Value: `https://pryhbrttsgamlqxvwiap.supabase.co`
   - Purpose: Defines the base URL for the Supabase REST API

2. **SUPABASE_SERVICE_KEY**
   - Value: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByeWhicnR0c2dhbWxxeHZ3aWFwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjM4ODg2OCwiZXhwIjoyMDYxOTY0ODY4fQ.78rTwSlIzVsIFLS4MZSw2ca45f2Jm-BayFcs6A7NilE`
   - Purpose: Service role JWT token that bypasses RLS policies and grants direct write access
   - Note: This is a service role key with elevated privileges - **DO NOT SHARE**

### Setting Environment Variables
```bash
# Set these variables before starting the sports bot
export SUPABASE_URL="https://pryhbrttsgamlqxvwiap.supabase.co"
export SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByeWhicnR0c2dhbWxxeHZ3aWFwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjM4ODg2OCwiZXhwIjoyMDYxOTY0ODY4fQ.78rTwSlIzVsIFLS4MZSw2ca45f2Jm-BayFcs6A7NilE"
```

### Making Environment Variables Persistent
To ensure these variables persist across system restarts, add them to your `.bashrc` or create a startup wrapper script.

**Option 1: Add to .bashrc**
```bash
echo 'export SUPABASE_URL="https://pryhbrttsgamlqxvwiap.supabase.co"' >> ~/.bashrc
echo 'export SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByeWhicnR0c2dhbWxxeHZ3aWFwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjM4ODg2OCwiZXhwIjoyMDYxOTY0ODY4fQ.78rTwSlIzVsIFLS4MZSw2ca45f2Jm-BayFcs6A7NilE"' >> ~/.bashrc
source ~/.bashrc
```

**Option 2: Create a startup wrapper script**
Create a file named `start_sports_bot.sh`:
```bash
#!/bin/bash
export SUPABASE_URL="https://pryhbrttsgamlqxvwiap.supabase.co"
export SUPABASE_SERVICE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByeWhicnR0c2dhbWxxeHZ3aWFwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjM4ODg2OCwiZXhwIjoyMDYxOTY0ODY4fQ.78rTwSlIzVsIFLS4MZSw2ca45f2Jm-BayFcs6A7NilE"
cd /root/CascadeProjects/sports_bot/football
TZ="America/New_York" python3 live.py
```

Make it executable:
```bash
chmod +x start_sports_bot.sh
```

## Code Structure and Integration

### File Structure
- `/root/CascadeProjects/sports_bot/football/logger/db_api.py` - The database API module used by live.py
- `/root/CascadeProjects/sports_bot/football/live.py` - The main application that imports and uses the database API
- `/root/CascadeProjects/sports_bot/football/test_db_connection.py` - A testing utility for direct PostgreSQL connection (separate from the REST API method)

### Import Structure
In `live.py`, the database module is imported:
```python
from football.logger.db_api import archive_match_json
```

### DB API Implementation
The `db_api.py` module:
1. Retrieves environment variables for Supabase connection
2. Sets up proper headers for REST API authentication
3. Provides the `archive_match_json()` function that:
   - Takes a match data dictionary
   - Converts it to JSON
   - Posts it to the Supabase REST endpoint
   - Logs success or failure

### Integration with live.py
In the main processing loop of `live.py`, after processing each match:
```python
# Emit a one-line JSON blob for alerts, flushing immediately to ensure prompt processing
archive_match_json(match_data)
```

## Testing and Verification

### Testing the DB API Directly
```bash
cd /root/CascadeProjects/sports_bot/football
python3 -c "from football.logger.db_api import archive_match_json; test_data = {'match_id': 'TEST456', 'test': 'connection'}; archive_match_json(test_data); print('Test completed')"
```

Successful output:
```
INFO:db_api:✅ Match data archived successfully with ID: unknown
Test completed
```

### Testing via db_api.py's Self-Test
```bash
cd /root/CascadeProjects/sports_bot/football/logger
python3 db_api.py
```

Successful output:
```
INFO:db_api:✅ Match data archived successfully with ID: unknown
Test complete - check logs for results
```

### Verifying in Supabase
After running tests:
1. Login to the Supabase dashboard
2. Navigate to Table Editor → archived_json
3. Verify new rows with the test data were inserted

## Troubleshooting

### Common Issues and Solutions

#### "Skipping database archiving - Supabase service key not properly configured"
**Cause:** The `SUPABASE_SERVICE_KEY` environment variable isn't set or is invalid.
**Solution:** Re-export the correct service key.

#### "Failed to archive via REST: 401 - Invalid API key"
**Cause:** The service key has expired or is incorrect.
**Solution:** 
1. Regenerate a new service key from the Supabase dashboard
2. Update the environment variable

#### "Connection refused" (Direct PostgreSQL connection)
**Cause:** 
- Database server is down
- Connection details are incorrect
- Network restrictions are preventing the connection
**Solution:**
1. Verify the database is operational in Supabase dashboard
2. Check IP allow-listing in Supabase configuration
3. Verify connection string parameters

#### "The 'archived_json' table might not exist"
**Cause:** The required table hasn't been created in the database.
**Solution:** Execute the table creation SQL provided in this document via the Supabase SQL Editor.

## Security Considerations

### API Key Security
- The service key has elevated privileges and should be treated as a sensitive credential
- Never commit this key to version control
- Consider using a secrets management solution for production environments
- Rotate keys periodically (update environment variables when rotating)

### Data Security
- All match data is stored in the `payload` JSONB column
- Consider implementing RLS policies if multi-user access is required
- Data is transmitted via HTTPS, ensuring encryption in transit

## Background and Notes

### REST API vs Direct Connection
The Sports Bot system uses Supabase's REST API for database operations rather than direct PostgreSQL connections for several reasons:
1. Simplifies connection management (no need to handle connection pooling)
2. Works through firewalls more reliably (standard HTTPS on port 443)
3. Can leverage Supabase's Row Level Security policies if needed
4. Reduces dependency on PostgreSQL client libraries

### Database Monitoring
To monitor the growth of your database:
1. Execute `SELECT COUNT(*) FROM archived_json;` in the Supabase SQL Editor
2. Check the "Storage" tab in Supabase dashboard to monitor overall database size

---

Document last updated: May 4, 2025
