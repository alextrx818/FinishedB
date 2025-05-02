# 📋 Official Logger Filter Standards

**EFFECTIVE DATE: May 2, 2025**

This document establishes the **MANDATORY STANDARD** for all logger filters in the sports_bot system.

## Compliance Requirements

1. **Mandatory Compliance**: All logger filters MUST comply with these standards.
2. **No Exceptions**: Deviations are not permitted without explicit approval.

## Implementation Standards

### 1. Auto-Create Blank .logger
At the very top of your filter module (before anything else):

```python
import os

OUT_PATH = os.path.join(os.path.dirname(__file__), "<your_filter>.logger")
if not os.path.exists(OUT_PATH):
    open(OUT_PATH, "w").close()
```

### 2. Imports & Globals

```python
from logger.main_logger import event_listeners, original_print, get_eastern_time
import re, os

# per-day rollover counting
last_filter_date   = None
daily_filter_count = 0

seen_ids = set()    # to dedupe by Competition ID
```

### 3. Timezone & Formatting

- **Timezone**: America/New_York (ET)
- **Date Format**: MM/DD/YYYY
- **Time Format**: HH:MM:SS AM/PM ET

Use:

```python
ts = get_eastern_time().strftime("%m/%d/%Y %I:%M:%S %p ET")
```

### 4. Daily Counter Rollover
At the top of your handle_chunk:

```python
current_dt = get_eastern_time()
today_iso  = current_dt.strftime("%Y-%m-%d")
today_std  = current_dt.strftime("%m/%d/%Y")
now_time   = current_dt.strftime("%I:%M:%S %p ET")

global last_filter_date, daily_filter_count
if today_iso != last_filter_date:
    last_filter_date   = today_iso
    daily_filter_count = 0
daily_filter_count += 1
header_count = daily_filter_count
```

### 5. Build Your Header
Prepend this line above the chunk (which already includes --- Summary Set…):

```
--- <FILTER_NAME> MATCH #<header_count> for <today_std> <now_time> ---
```

### 6. Filtering Logic

- Extract a unique key (e.g. Competition ID) and skip if already seen.
- Parse your criterion (e.g. Over/Under ≥ 3.0).
- Only on pass do you emit.

### 7. Universal Prepend Rule
Always write new entries by prepending to the top of <your_filter>.logger:

```python
with open(OUT_PATH, "r+") as f:
    old = f.read()
    f.seek(0)
    f.write(header + chunk + "\n\n" + old)
    f.truncate()
```

### 8. Register Your Handler

```python
def handle_chunk(chunk: str):
    # … your filter logic …
event_listeners.append(handle_chunk)
```

### 9. Bootstrap in live.py
In one line (near the top, after the main‐logger import), add:

```python
import logger.log_filters.<your_filter_folder>.<your_filter_module>
```

That single import ensures your filter auto-loads and its event_listeners hook runs on every startup—no other changes needed in live.py.

## Benefits of Standardization

With these standards in place, every logger filter will automatically:

- Create its blank .logger file if missing
- Reset its daily counter at midnight ET
- Use consistent MM/DD/YYYY and US-NY timestamps
- Prepend new entries correctly
- Register itself via a single import in live.py

## Rationale

These standards ensure:
- Consistency across all logger filters
- Robustness against missing files
- Seamless testing and development workflow
- Proper formatting and organization of match data
- Ease of maintenance and future development

---

**IMPORTANT**: All developers working on the sports_bot codebase must review this document before implementing any new logger filters.
