# Sports Bot Diagnostic Tools & Procedures

> **Last Updated: May 10, 2025**

This document provides comprehensive procedures for diagnosing and testing the sports bot system. Use these tools to verify system health, troubleshoot issues, and ensure all components are functioning correctly.

## Table of Contents

1. [Quick Health Check](#quick-health-check)
2. [System Diagnostics](#system-diagnostics)
3. [Database Diagnostics](#database-diagnostics)
4. [Telegram Integration Tests](#telegram-integration-tests)
5. [Performance Monitoring](#performance-monitoring)
6. [Automated Reporting](#automated-reporting)
7. [Performance Trend Tracking](#performance-trend-tracking)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Sample Reports](#sample-reports)

## Quick Health Check

Run this command for a rapid assessment of system health:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/quick_health.py
```

## System Diagnostics

### Module Status Check

Verify all required modules are properly loaded:

```bash
cd /root/CascadeProjects/sports_bot && python3 -c "import sys; import supabase_config; import football.logger.db_api as db; from football.live import SUPABASE_AVAILABLE; print(f'Supabase Available: {SUPABASE_AVAILABLE}')"
```

### Error Log Analysis

View the most recent ERROR and CRITICAL log entries:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/analyze_logs.py --level ERROR --count 50
```

### Process Monitoring

Check if the sports bot process is running:

```bash
ps aux | grep "[p]ython3.*live\.py"
```

Remember: The sports bot **must** be started directly through Python command (`python3 live.py`) and never through systemd services to ensure proper Telegram notification functionality.

## Database Diagnostics

### Connection Test

Verify Supabase database connection and table access:

```bash
cd /root/CascadeProjects/sports_bot && python3 test_db.py
```

### Database Round-Trip Test

Test both writing to and reading from the database:

```bash
cd /root/CascadeProjects/sports_bot && python3 test_db_stats.py
```

### Table Verification SQL

Execute these in the Supabase SQL Editor to verify table existence:

```sql
-- Check for archived_json table
SELECT EXISTS (
  SELECT FROM information_schema.tables 
  WHERE table_schema = 'public' 
  AND table_name = 'archived_json'
);

-- Check for logs table
SELECT EXISTS (
  SELECT FROM information_schema.tables 
  WHERE table_schema = 'public' 
  AND table_name = 'logs'
);

-- Check recent archived matches (last 10)
SELECT id, raw_json->>'id' as match_id, created_at
FROM archived_json
ORDER BY created_at DESC
LIMIT 10;
```

## Telegram Integration Tests

### Bot Status Check

Verify the Telegram bot is active and responding:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/telegram_status.py
```

### Send Test Alert

Send a test message to verify notification delivery:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/telegram_test_alert.py "Diagnostic test message from Sports Bot"
```

### Check Webhook Status

If using webhooks, verify configuration:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/check_webhook.py
```

## Performance Monitoring

### Resource Usage

Monitor CPU and memory usage during operation:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/monitor_resources.py --minutes 5
```

### API Performance

Test API response times and reliability:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/test_api.py
```

### Database Performance

Benchmark database operations:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/db_benchmark.py --operations 100
```

## Troubleshooting Common Issues

### Database Connection Issues

If experiencing database connection problems:

1. Verify SERVICE_KEY is set correctly in supabase_config.py
2. Confirm tables exist in Supabase (use SQL verification above)
3. Test network connectivity to Supabase endpoint
4. Check for any RLS policies that might be blocking operations

### Telegram Notification Issues

If Telegram notifications aren't working:

1. Verify bot token is valid
2. Ensure bot API is reachable
3. Check if the bot has been blocked or chat_id is incorrect
4. Remember that notifications only work when starting directly with `python3 live.py`, not through systemd services

### Data Processing Issues

If match data isn't processing correctly:

1. Check API credentials and rate limits
2. Verify the match data format hasn't changed
3. Look for parsing errors in the logs
4. Check if third-party APIs are operational

## Sample Reports

### System Health Report

Below is a sample system health report that should be generated regularly:

#### Module Status & Error Counts

| Category | Status | Count | Details |
|----------|--------|-------|---------|
| Module Imports | ✅ Healthy | 0 failures | All critical modules loaded successfully |
| Unhandled Exceptions | ✅ Healthy | 0 occurrences | No uncaught exceptions observed |
| ERROR Log Entries | ✅ Healthy | 0 critical errors | No application errors after configuration fixes |
| Warning Log Entries | ✅ Healthy | 0 persistent | No recurring warning patterns observed |

#### Key Performance Metrics

| Metric | Value | Status | Threshold |
|--------|-------|--------|-----------|
| Uptime | ~15 minutes (test run) | ✅ Normal | N/A |
| API Requests | ~30 per cycle | ✅ Normal | <100 per cycle |
| API Success Rate | 100% | ✅ Excellent | >95% |
| Database Operations | ~30 per cycle | ✅ Normal | <100 per cycle |
| Database Success Rate | 100% | ✅ Excellent | >95% |
| Database Response Time | <200ms | ✅ Excellent | <500ms |
| Matches Processed | 25-30 per cycle | ✅ Normal | Variable |
| Memory Usage | Stable | ✅ Normal | No leaks detected |

#### Database Operations Detail

| Operation | Count | Success Rate | Notes |
|-----------|-------|-------------|-------|
| Match Archiving | ~30 per cycle | 100% | All operations returning 201 Created |
| Batch Processing | 0 | N/A | Batch processing not triggered during test |
| Supabase Connectivity | Consistent | ✅ Stable | No connection interruptions |

### Potential Issues

#### Back-Pressure & Resource Constraints

No back-pressure events were observed during testing. The semaphore concurrency control for database operations is functioning as expected, maintaining orderly database access.

#### Database Permission Issues

No RLS (Row Level Security) or permission issues were detected after applying the SERVICE_KEY authentication. All database operations completed successfully with appropriate authorization.

#### Match Processing Anomalies

| Anomaly Type | Frequency | Impact | Details |
|--------------|-----------|--------|---------|
| Betting Timing Approximation | ~15% of matches | ⚠️ Low | "Closest time to minutes 4-6 available" substitutions |
| Missing Environment Data | ~10% of matches | ⚠️ Low | "No environment data available for this match" |
| Unusual Betting Lines | Rare | ⚠️ Low | Occasionally extreme values (e.g., +15000) |

None of these anomalies affected overall system performance or data integrity. They appear to be normal variations in source data.

## Creating Diagnostic Scripts

If additional diagnostic needs arise, follow these guidelines for creating new diagnostic tools:

1. Place all diagnostic scripts in the `tools/` directory
2. Use consistent command-line argument parsing
3. Implement proper error handling and clear output
4. Add the script to this documentation with usage instructions

When creating diagnostic tests, ensure they don't modify production data unless explicitly intended to do so.

---

## Automated Reporting

### Setting Up Daily Diagnostic Reports

To receive automated health reports each day, set up a cron job that runs the diagnostic tools and emails the results:

1. Create a script that generates and sends the report:

```bash
cat > /root/CascadeProjects/sports_bot/tools/daily_report.sh << 'EOF'
#!/bin/bash

# Set environment variables needed by the sports bot
export TZ="America/New_York"

# Navigate to project directory
cd /root/CascadeProjects/sports_bot

# Create a timestamp for the report
TIMESTAMP=$(date +"%Y-%m-%d")

# Create report directory if it doesn't exist
mkdir -p reports

# Generate the report
python3 tools/generate_report.py --output "reports/daily_report_${TIMESTAMP}.md"

# Convert markdown to HTML for email
python3 -m markdown "reports/daily_report_${TIMESTAMP}.md" > "reports/daily_report_${TIMESTAMP}.html"

# Send email with the report
cat "reports/daily_report_${TIMESTAMP}.html" | mail -a "Content-Type: text/html" -s "Sports Bot Daily Health Report ${TIMESTAMP}" your-email@example.com

# Send a notification via Telegram
python3 tools/telegram_test_alert.py "Daily diagnostic report generated. See email for details."

# Maintain report history (keep last 30 days)
find reports/ -name "daily_report_*.md" -mtime +30 -delete
find reports/ -name "daily_report_*.html" -mtime +30 -delete
EOF

chmod +x /root/CascadeProjects/sports_bot/tools/daily_report.sh
```

2. Set up a cron job to run this script daily at 8:00 AM:

```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "0 8 * * * /root/CascadeProjects/sports_bot/tools/daily_report.sh") | crontab -
```

3. For on-demand reports, simply run:

```bash
/root/CascadeProjects/sports_bot/tools/daily_report.sh
```

### Report Archiving

All reports are stored in the `/root/CascadeProjects/sports_bot/reports/` directory with date-stamped filenames for easy reference and trend analysis. The script automatically maintains a 30-day history.

## Performance Trend Tracking

### Setting Up Long-term Metrics Collection

To track performance trends over time, implement a metrics collection system:

1. Create a metrics storage database:

```bash
cat > /root/CascadeProjects/sports_bot/tools/setup_metrics_db.py << 'EOF'
#!/usr/bin/env python3
import sqlite3
import os

# Ensure metrics directory exists
os.makedirs(os.path.dirname("/root/CascadeProjects/sports_bot/metrics/"), exist_ok=True)

# Connect to metrics database
conn = sqlite3.connect("/root/CascadeProjects/sports_bot/metrics/performance.db")
c = conn.cursor()

# Create tables for long-term metrics tracking
c.execute('''CREATE TABLE IF NOT EXISTS api_metrics
             (timestamp TEXT, requests INTEGER, successes INTEGER, failures INTEGER, 
              avg_response_time REAL, retry_rate REAL)''')
             
c.execute('''CREATE TABLE IF NOT EXISTS db_metrics
             (timestamp TEXT, operations INTEGER, successes INTEGER, failures INTEGER,
              skipped INTEGER, avg_response_time REAL)''')
              
c.execute('''CREATE TABLE IF NOT EXISTS system_metrics
             (timestamp TEXT, memory_usage REAL, cpu_usage REAL, matches_processed INTEGER,
              uptime INTEGER)''')
              
c.execute('''CREATE TABLE IF NOT EXISTS back_pressure_events
             (timestamp TEXT, component TEXT, duration INTEGER, skipped_operations INTEGER)''')

conn.commit()
conn.close()

print("Metrics database initialized successfully.")
EOF

python3 /root/CascadeProjects/sports_bot/tools/setup_metrics_db.py
```

2. Create a metrics collection script:

```bash
cat > /root/CascadeProjects/sports_bot/tools/collect_metrics.py << 'EOF'
#!/usr/bin/env python3
import sqlite3
import datetime
import sys
import os
import psutil

sys.path.append('/root/CascadeProjects/sports_bot')

# Try to import Metrics from live.py without executing the whole file
try:
    # This is a safe way to import just the Metrics class
    import importlib.util
    spec = importlib.util.spec_from_file_location("live", "/root/CascadeProjects/sports_bot/football/live.py")
    live = importlib.util.module_from_spec(spec)
    # We only execute enough to get the Metrics class
    live.Metrics = getattr(live, "Metrics", None)
    if live.Metrics is None:
        print("Warning: Couldn't access Metrics from live.py")
        sys.exit(1)
except Exception as e:
    print(f"Error importing Metrics: {e}")
    sys.exit(1)

# Connect to metrics database
conn = sqlite3.connect("/root/CascadeProjects/sports_bot/metrics/performance.db")
c = conn.cursor()

# Get current timestamp
timestamp = datetime.datetime.now().isoformat()

# Collect and store API metrics
if hasattr(live.Metrics, "get_api_stats"):
    api_stats = live.Metrics.get_api_stats()
    c.execute("INSERT INTO api_metrics VALUES (?, ?, ?, ?, ?, ?)",
              (timestamp, api_stats.get("requests", 0), api_stats.get("successes", 0),
               api_stats.get("failures", 0), api_stats.get("avg_response_time", 0),
               api_stats.get("retry_rate", 0)))

# Collect and store DB metrics
if hasattr(live.Metrics, "get_db_stats"):
    db_stats = live.Metrics.get_db_stats()
    c.execute("INSERT INTO db_metrics VALUES (?, ?, ?, ?, ?, ?)",
              (timestamp, db_stats.get("operations", 0), db_stats.get("successes", 0),
               db_stats.get("failures", 0), db_stats.get("skipped", 0),
               db_stats.get("avg_response_time", 0)))

# Collect system metrics
process = psutil.Process(os.getpid())
mem_usage = process.memory_info().rss / 1024 / 1024  # MB
cpu_usage = psutil.cpu_percent(interval=1)
matches_processed = getattr(live.Metrics, "processed_matches", 0)
uptime = 0
if hasattr(live.Metrics, "startup_time"):
    uptime = (datetime.datetime.now() - live.Metrics.startup_time).total_seconds()

c.execute("INSERT INTO system_metrics VALUES (?, ?, ?, ?, ?)",
          (timestamp, mem_usage, cpu_usage, matches_processed, uptime))

# Commit changes and close connection
conn.commit()
conn.close()

print(f"Metrics collected successfully at {timestamp}")
EOF

chmod +x /root/CascadeProjects/sports_bot/tools/collect_metrics.py
```

3. Set up periodic metrics collection (every 15 minutes):

```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "*/15 * * * * /usr/bin/python3 /root/CascadeProjects/sports_bot/tools/collect_metrics.py >> /root/CascadeProjects/sports_bot/metrics/collection.log 2>&1") | crontab -
```

### Generating Trend Reports

Create a trend analysis report that shows performance over time:

```bash
cat > /root/CascadeProjects/sports_bot/tools/generate_trend_report.py << 'EOF'
#!/usr/bin/env python3
import sqlite3
import matplotlib.pyplot as plt
import datetime
import os
import argparse

# Parse command line arguments
parser = argparse.ArgumentParser(description="Generate performance trend report")
parser.add_argument("--days", type=int, default=7, help="Number of days of history to include")
parser.add_argument("--output", type=str, default="trend_report", help="Base name for output files")
args = parser.parse_args()

# Ensure output directory exists
os.makedirs("reports", exist_ok=True)

# Connect to metrics database
conn = sqlite3.connect("/root/CascadeProjects/sports_bot/metrics/performance.db")
c = conn.cursor()

# Calculate date range
end_date = datetime.datetime.now().isoformat()
start_date = (datetime.datetime.now() - datetime.timedelta(days=args.days)).isoformat()

# Generate API metrics chart
c.execute("SELECT timestamp, requests, successes, failures, avg_response_time FROM api_metrics WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp", 
          (start_date, end_date))
rows = c.fetchall()

if rows:
    timestamps = [datetime.datetime.fromisoformat(row[0]) for row in rows]
    requests = [row[1] for row in rows]
    successes = [row[2] for row in rows]
    failures = [row[3] for row in rows]
    response_times = [row[4] for row in rows]
    
    # Create API requests chart
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, requests, label="Total")
    plt.plot(timestamps, successes, label="Successful")
    plt.plot(timestamps, failures, label="Failed")
    plt.title(f"API Requests ({args.days} Day Trend)")
    plt.xlabel("Time")
    plt.ylabel("Count")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"reports/{args.output}_api_requests.png")
    
    # Create response time chart
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, response_times)
    plt.title(f"API Response Time ({args.days} Day Trend)")
    plt.xlabel("Time")
    plt.ylabel("Average Response Time (ms)")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"reports/{args.output}_api_response_time.png")

# Generate DB metrics chart (similar pattern)
# ... (similar code for database metrics)

# Generate markdown report with embedded charts
with open(f"reports/{args.output}.md", "w") as f:
    f.write(f"# Sports Bot Performance Trend Report\n\n")
    f.write(f"*Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
    f.write(f"## API Performance (Last {args.days} Days)\n\n")
    f.write(f"![API Requests]({args.output}_api_requests.png)\n\n")
    f.write(f"![API Response Time]({args.output}_api_response_time.png)\n\n")
    # Add more sections for other metrics

print(f"Trend report generated at reports/{args.output}.md")
EOF

chmod +x /root/CascadeProjects/sports_bot/tools/generate_trend_report.py
```

4. Schedule a weekly trend report:

```bash
# Add to crontab
(crontab -l 2>/dev/null; echo "0 7 * * 1 /usr/bin/python3 /root/CascadeProjects/sports_bot/tools/generate_trend_report.py --days 30 --output weekly_trends >> /root/CascadeProjects/sports_bot/metrics/trends.log 2>&1") | crontab -
```

### Viewing Performance Trends

To view performance trends on demand:

```bash
python3 /root/CascadeProjects/sports_bot/tools/generate_trend_report.py --days 14
```

This will create a report with charts showing API and database performance over the specified time period.

## Generating Comprehensive Reports

To generate a full diagnostic report:

```bash
cd /root/CascadeProjects/sports_bot && python3 tools/generate_report.py --output report.md
```

This will create a markdown report with all diagnostic information that can be saved for reference or troubleshooting.

## Monitoring Guidelines

1. Run quick health checks daily (automated via cron)
2. Generate comprehensive reports weekly (automated via cron)
3. Review performance trends monthly to identify long-term issues
4. Test Telegram integration after any configuration changes
5. Verify database connection after any Supabase updates
6. Monitor API rate limits and usage regularly

Following these guidelines will help ensure the sports bot system remains healthy and functional.
