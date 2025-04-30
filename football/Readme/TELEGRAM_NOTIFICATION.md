# Telegram Notification System

This document explains how to use the centralized Telegram notification system in the Football Monitor project.

## Overview

The Telegram notification system provides a unified interface for all Telegram communications in the project. Any module that needs to send Telegram alerts should use this system rather than implementing its own notification logic.

## Features

- **Centralized Configuration**: All Telegram credentials stored in one place
- **Rate Limiting**: Prevents flooding the Telegram API
- **Duplicate Detection**: Avoids sending the same message repeatedly
- **Message Formatting**: Consistent message formatting with appropriate icons
- **Different Alert Types**: Specialized functions for different kinds of alerts

## Usage

### Basic Import

```python
from football.telegram import send_message, send_alert, send_match_alert, send_system_alert
```

### Sending a Simple Message

```python
from football.telegram import send_message

# Send a basic message
send_message("Match data successfully updated")

# Send a silent notification (no sound)
send_message("Background process completed", silent=True)
```

### Sending an Alert

```python
from football.telegram import send_alert

# Send an important alert
send_alert("API rate limit reached. Waiting 5 minutes before retry.")

# Send with custom icon
send_alert("Database backup completed", icon="💾")
```

### Sending Match Alerts

```python
from football.telegram import send_match_alert

# Basic match alert
send_match_alert("Match starting soon", 
                teams="Team A vs Team B",
                competition="Premier League")

# Goal alert
send_match_alert("GOAL! Team A scores!", 
                teams="Team A vs Team B",
                score="1-0",
                match_id="abc123",
                alert_type="goal")

# Odds alert
send_match_alert("Significant odds movement detected",
                teams="Team A vs Team B",
                alert_type="odds")
```

### System Status Alerts

```python
from football.telegram import send_system_alert

# Startup notification
send_system_alert("Football monitor started successfully", alert_type="startup")

# Error notification
send_system_alert("Failed to connect to API", 
                alert_type="error",
                error_details="Connection timeout after 30 seconds")

# System warning
send_system_alert("Low disk space detected", alert_type="warning")
```

### Convenience Functions

```python
from football.telegram.notifier import notify_startup, notify_shutdown, notify_error

# Starting up
notify_startup()

# Error occurred
notify_error("Database connection failed", "Could not connect to MySQL")

# Shutting down
notify_shutdown()
```

## Alert Types and Icons

The system uses consistent icons for different alert types:

| Alert Type | Icon | Description |
|------------|------|-------------|
| startup    | 🟢   | System starting |
| shutdown   | 🔴   | System stopping |
| error      | ⚠️   | Error condition |
| match      | ⚽   | General match alert |
| goal       | 🥅   | Goal scored |
| odds       | 📊   | Odds update |
| weather    | 🌤️   | Weather/environment |
| status     | 📡   | Status update |
| heartbeat  | 💓   | System heartbeat |
| warning    | ⚠️   | Warning condition |
| info       | ℹ️    | Information |
| default    | 🔔   | Default alert |

## Implementation Details

### Rate Limiting

The system implements rate limiting to prevent flooding Telegram:

- Minimum 1 second between individual messages
- Maximum 5 messages in a 60-second window
- Automatic waiting if limits are exceeded

### Error Handling

All Telegram API errors are caught and logged. If the Telegram API is unavailable,
the system will log the error but won't crash the application.

### Message Deduplication

The system keeps track of recent messages and avoids sending the exact same 
message within a 5-minute window to prevent notification spam.

## Credentials

The system uses the existing project credentials:

- **Token**: 7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko
- **Chat ID**: 6128359776

## Integration with the Monitoring System

The Telegram notification system is fully integrated with the monitoring wrapper:

1. System startup/shutdown events send Telegram notifications
2. Uncaught exceptions are reported via Telegram
3. The heartbeat monitoring can report failures via Telegram
4. Watchdog inactivity detection alerts through Telegram
