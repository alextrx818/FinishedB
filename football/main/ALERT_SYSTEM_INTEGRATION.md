# Sports Bot Alert System Integration

## Overview

This document outlines the integration of the Sports Bot Alert System. The system follows a clean architecture with proper separation of concerns, ensuring that alert detection, formatting, and notification are managed by distinct components.

## Core Components

### 1. Alert Modules (e.g., OU3.py)

Alert modules are responsible solely for **detection**:
- Monitor match data for specific conditions (e.g., O/U line ≥ 3.0)
- Return notice strings when criteria are met
- Do NOT handle formatting, logging, or notifications

Example:
```python
class OverUnderAlert:
    def __init__(self, threshold=3.0):
        self.threshold = threshold
        
    def check(self, match):
        # Check for over/under markets
        for market in match.get("odds", {}).get("markets", []):
            if market.get("type") == "OVER_UNDER":
                line = market.get("line")
                if line and line >= self.threshold:
                    return f"O/U line = {line:.1f} (threshold: {self.threshold:.1f})"
        return None
```

### 2. AlerterMain (Orchestrator)

`alerter_main.py` serves as the central orchestrator:
- Manages the lifecycle of all alerts
- Creates and maintains loggers for each alert
- Handles formatting through formatting_utils.py
- Implements head-insertion logging (newest alerts at top)
- Manages deduplication (prevents repeat alerts for same match)
- Sends Telegram notifications

### 3. Formatting Utilities

`formatting_utils.py` provides pure formatting functions:
- `format_alert_block()`: Formats alert blocks with standardized headers
- Ensures consistent column alignment for betting odds
- Maintains uniform section headers
- Contains no I/O operations (pure formatting logic)

## Global Formatting Standards

### Alert Header Format
```
================================================================================
#X of Y ALERT TRIGGERED: [ALERT_NAME] @ [TIMESTAMP]
================================================================================
```

### Section Headers
```
----- MATCH SUMMARY -----
-------------------------

--- MATCH BETTING ODDS ---
--------------------------

--- MATCH ENVIRONMENT ---
-------------------------
```

### Betting Odds Column Alignment
```
│ Home  : +140 │ Draw  : +290 │ Away  : +350 │ (@4')
│ Home  : +125 │ Hcap  : -0.5 │ Away  : +180 │ (@4')
│ Over  : +160 │ Line  :  4.5 │ Under : +240 │ (@4')
```

## Integration with orchestrate_complete.py

The main orchestration script (`orchestrate_complete.py`) uses `alerter_main.py` directly:

1. Creates alert instances
2. Initializes AlerterMain with those instances
3. For each match in the pipeline:
   - Checks if any alerts are triggered
   - If triggered, processes the alert through AlerterMain
   - AlerterMain handles formatting, logging, and notification

```python
# Create alert instances
alerts = [
    OverUnderAlert(threshold=3.0),  # O/U ≥ 3.00
]

# Create AlerterMain instance
alerter = AlerterMain(alerts=alerts)

# Process matches
for match in merged:
    # ... processing logic ...
```

## Head-Insertion Logging

Unlike standard logging that appends to the end of files, our system implements "head-insertion" logging:
- New alerts appear at the TOP of the log file
- Makes it easy to see the most recent alerts first
- Achieved by:
  1. Reading the existing log file content
  2. Writing the new alert
  3. Appending the old content

## Alert Numbering System

Each alert has:
- A type-specific counter (e.g., "this is the 47th OU3 alert")
- A global counter (e.g., "out of 123 total alerts today")
- Counters reset at midnight

## Adding New Alerts

To create a new alert:

1. Create a new Python file in the Alerts directory (e.g., `OU4.py`)
2. Implement the alert class with a `check()` method
3. Register the alert in `alerter_main.py` and/or `orchestrate_complete.py`:

```python
alerts = [
    OverUnderAlert(threshold=3.0),  # O/U ≥ 3.00
    NewAlert(),                     # Your new alert
]
```

AlerterMain will automatically:
- Create a logger named after your file (e.g., "OU4")
- Generate a log file ("OU4.logger")
- Apply all global formatting standards
- Use head-insertion logging (newest alerts at top)
- Manage deduplication via "OU4.seen.json"
- Send Telegram notifications

## Design Principles

The alert system follows these key principles:

1. **Separation of Concerns**:
   - Detection logic in alert modules
   - Orchestration in AlerterMain
   - Formatting in formatting_utils.py

2. **Consistent Formatting**:
   - All alerts follow the same global standards
   - Perfect column alignment for betting odds
   - Standardized section headers

3. **User-Friendly Logging**:
   - Newest alerts at the top (head-insertion)
   - Clear numbering system (#X of Y)
   - Organized log structure

## Alert Flow Diagram

```
Match Data → Alert Module Detection → AlerterMain Orchestration
                                       ↓
                                  Is Triggered?
                                  ↙         ↘
                                No           Yes
                                ↓             ↓
                             (Skip)    1. Get/update alert count
                                       2. Format using formatting_utils.py
                                       3. Apply head-insertion logging
                                       4. Send Telegram notification
                                       5. Mark as seen (deduplication)
```

## Environment Data Integration

The system integrates environment data from matches:
- Weather codes (1=Sunny, etc.)
- Temperature with units
- Wind speed with Beaufort scale descriptors
- Humidity percentages

This data appears in the Match Environment section of alerts.

## Testing and Verification

The alert system includes test scripts to verify:
- Head-insertion logging (test_prepend_logging.py)
- Alert numbering (alert_counter_test.py)
- Betting odds alignment (final_alignment_test.py)

Run these tests to ensure the system is functioning correctly after any modifications.
