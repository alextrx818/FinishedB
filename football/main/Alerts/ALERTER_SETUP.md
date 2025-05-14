# Sports Bot Alert System Architecture

## Overview

The sports bot alert system follows a clean architecture that separates detection from orchestration, formatting, and notification. This document explains the system's architecture, components, and how to create new alerts.

## Architecture Components

### 1. Alert Modules

Alert modules (like `OU3.py`) are responsible **only** for detection:
- Monitor match data for specific conditions (e.g., O/U line ≥ 3.0)
- Return a notice string when criteria are met
- Do NOT handle formatting, logging, or notifications

Example alert module interface:
```python
class MyAlert:
    def check(self, match):
        # Return a notice string if criteria met, None otherwise
        return "Alert triggered: [reason]" if [criteria_met] else None
```

### 2. AlerterMain (Orchestrator)

`alerter_main.py` serves as the central orchestrator:
- Manages the lifecycle of all alerts
- Creates and maintains loggers for each alert
- Handles all formatting through formatting_utils.py
- Implements head-insertion logging (newest alerts appear at top of log files)
- Manages deduplication (prevents repeat alerts for same match)
- Sends Telegram notifications

### 3. Formatting Utilities

`formatting_utils.py` provides pure formatting functions:
- Standardized alert block formatting
- Consistent column alignment for betting odds
- Uniform section headers

## Alert System Flow

1. `alerter_main.py` fetches match data
2. For each match, all registered alerts are evaluated
3. If an alert is triggered:
   - Alert count is updated
   - Match summary is formatted
   - Alert block is formatted with standard header
   - Alert is logged using head-insertion (newest at top)
   - Telegram notification is sent
   - Match is marked as "seen" to prevent duplicate alerts

## Global Formatting Standards

All alerts conform to these standards:

1. **Alert Header Format**:
   ```
   ================================================================================
   #X of Y ALERT TRIGGERED: [ALERT_NAME] @ [TIMESTAMP]
   ================================================================================
   ```

2. **Section Headers**:
   ```
   ----- MATCH SUMMARY -----
   -------------------------
   
   --- MATCH BETTING ODDS ---
   --------------------------
   
   --- MATCH ENVIRONMENT ---
   -------------------------
   ```

3. **Betting Odds Alignment**:
   ```
   │ Home  : +140 │ Draw  : +290 │ Away  : +350 │ (@4')
   │ Home  : +125 │ Hcap  : -0.5 │ Away  : +180 │ (@4')
   │ Over  : +160 │ Line  :  4.5 │ Under : +240 │ (@4')
   ```

## Adding New Alerts

To create a new alert:

1. Create a new Python file in the Alerts directory (e.g., `OU4.py`)
2. Implement the alert class with a `check()` method
3. Register the alert in `alerter_main.py`:
   ```python
   alerts = [
       OverUnderAlert(threshold=3.0),  # O/U ≥ 3.00
       YourNewAlert(),                 # Your new alert
   ]
   ```

AlerterMain will automatically:
- Create a logger named after your file (e.g., "OU4")
- Generate a log file ("OU4.logger")
- Apply all global formatting standards
- Use head-insertion logging (newest alerts at top)
- Manage deduplication via "OU4.seen.json"
- Send Telegram notifications

## Advanced Features

### Head-Insertion Logging

The system implements "head-insertion" logging:
- New alerts appear at the TOP of the log file
- Makes it easy to see the most recent alerts first
- Implemented using custom file I/O rather than standard logging

### Alert Numbering System

Each alert has:
- A type-specific counter (e.g., "this is the 47th OU3 alert")
- A global counter (e.g., "out of 123 total alerts today")
- Counters reset at midnight

## Examples

Example of creating a new Over/Under alert with different threshold:

```python
# OU4.py
class OU4Alert:
    def __init__(self, threshold=4.0):
        self.threshold = threshold
        
    def check(self, match):
        # Check for Over/Under markets
        markets = match.get("odds", {}).get("markets", [])
        for market in markets:
            if market.get("type") == "OVER_UNDER":
                line = market.get("line")
                if line and line >= self.threshold:
                    return f"O/U line = {line:.1f} (threshold: {self.threshold:.1f})"
        return None
```

Then register in alerter_main.py:
```python
alerts = [
    OverUnderAlert(threshold=3.0),  # O/U ≥ 3.00
    OU4Alert(threshold=4.0),        # O/U ≥ 4.00
]
```
