# Sports Bot Formatting Standards

## Alert Logger Formatting Guidelines

This document outlines the standardized formatting rules for alert logs in the sports bot system. Consistent formatting is critical for readability and professional appearance across all alert types.

### Match Betting Odds Display Format

The betting odds display must follow these exact formatting rules:

```
--- MATCH BETTING ODDS ---
│ Home  : +140 │ Draw  : +290 │ Away  : +350 │ (@52')
│ Home  : +125 │ Hcap  : -0.5 │ Away  : +180 │ (@52')
│ Over  : +160 │ Line  : 4.5  │ Under : +240 │ (@52')
```

#### Formatting Rules:

1. **Label Padding**:
   - All labels must have consistent width alignment
   - Shorter labels (4 characters: Home, Draw, Away, Hcap, Line, Over) must be padded with an extra space
   - "Under" (5 characters) sets the standard width - all other labels must match this width

2. **Colon Spacing**:
   - A space must appear after every colon (`: `)
   - This ensures consistent separator width

3. **Box Drawing Characters**:
   - Use the vertical bar character (`│`) for column separators
   - This creates a clean table-like visual structure

4. **Odds Format**:
   - American odds format with explicit + sign (e.g., `+140`)
   - Handicap and line values with one decimal place (e.g., `-0.5`, `4.5`)
   - Minute indicator in parentheses at end of line (e.g., `(@52')`)

5. **Label Order**:
   - Moneyline: `Home`, `Draw`, `Away`
   - Spread/Handicap: `Home`, `Hcap`, `Away`
   - Totals: `Over`, `Line`, `Under`

6. **Alignment**:
   - All values must align vertically in each column
   - The odds section must be centered under the "MATCH BETTING ODDS" header

### Match Summary Section Format

```
----- MATCH SUMMARY -----
Timestamp: 05/14/2025 12:31:45 PM EDT
Match ID: TEST-45678
Competition ID: comp-laliga
Competition: LaLiga (Spain)
Match: Barcelona vs Real Madrid
Score: 1 - 1 (HT: 0 - 0)
Status: Second Half (Status ID: 4)
```

### Environment Section Format

```
--- MATCH ENVIRONMENT ---
Temperature: 74.0°F
Humidity: 55%
Wind: 6.2 mph
```

## Implementation Details

The formatting standards are implemented in:
- `alerter_main.py` - Main alert processing
- `combined_match_summary.py` - Match summary display

### String Formatting Code Example

```python
# Format betting odds display with proper column alignment
ml_line = f"│ Home  : {home_str} │ Draw  : {draw_str} │ Away  : {away_str} │ (@{minute}')"
spread_line = f"│ Home  : {home_str} │ Hcap  : {handicap_str} │ Away  : {away_str} │ (@{minute}')"
ou_line = f"│ Over  : {over_str} │ Line  : {line_str} │ Under : {under_str} │ (@{minute}')"
```

## Alert Prepending Rule (GLOBAL STANDARD)

This is a mandatory global formatting rule that must be applied to all alerts without exception:

```
================================================================================
#5 of 9 ALERT TRIGGERED: OU3 @ 04:41:41 PM 05/14/2025
================================================================================
```

1. **Alert Numbering**:
   - Each alert header must be prepended with alert count information in format: `#X of Y`
   - `X` = The sequential number for this specific alert type today
   - `Y` = The total number of alerts (all types) triggered today

2. **Alert Identification**:
   - Must use the exact format: `ALERT TRIGGERED: [ALERT_NAME]`
   - Alert name must be uppercase and match the base logger name

3. **Timestamp Format**:
   - Must appear after the alert name with format: `@ HH:MM:SS AM/PM MM/DD/YYYY`
   - Must include both time and date
   
4. **Application Rules**:
   - Only applied AFTER an alert is triggered and confirmed by independent alerters
   - Managed by alerter_main.py in the alert processing flow
   - Daily counter resets at midnight
   - Each alert type has its own counter

## Timestamp Handling in Logger Files

1. **Alert Notifications**:
   - Include timestamp: `2025-05-14 16:31:45,000 - Alert triggered for match TEST-45678: OU3 Alert with line 4.5!`

2. **Match Summary Format**:
   - No timestamps on individual summary lines
   - Must use clean formatter: `logging.Formatter("%(message)s")`

3. **File Creation**:
   - Logger files are automatically created when an alert is triggered
   - Base filename matches the alert module name (e.g., `OU3.py` -> `OU3.logger`)

## Compliance Requirements

All code that generates alert logs must comply with these formatting standards. Any modifications to the formatting logic must maintain this exact visual appearance to ensure consistency across the system.

_Last updated: May 14, 2025_
