# Betting Odds Format Investigation

## Current Issue
When examining the log entries (example from May 2nd, 2025), we noticed that the betting odds display appears incomplete:

```
--- MATCH BETTING ODDS ---
ML (Money Line):
Time: 6 min | Home: -120 | Draw: +300 | Away: +260

SPREAD (Asia Handicap):

```

The issue is that:
1. ML (Money Line) data appears correctly
2. SPREAD (Asia Handicap) shows only the header without any data
3. Over/Under section is missing entirely

## Investigation Findings

After investigating the code in `live.py`, we discovered:

1. The betting odds formatting is handled by `format_odds_display()` function (lines 585-787)
2. Each section (ML, SPREAD, Over/Under) is only added if valid data exists
3. The system appears to be working as designed - it's showing headers for sections where data was requested but not available

The likely cause is that for this particular match:
- ML data was available 
- SPREAD data was requested but unavailable
- Over/Under data was unavailable

## Next Steps for Tomorrow

1. **Data Availability Analysis**:
   - Check multiple log entries to confirm if this pattern is consistent for certain matches/competitions
   - Verify if the API always returns all odds types or if some are conditionally available

2. **Format Improvement Options**:
   - Consider modifying `format_odds_display()` to include placeholder text when data is missing
   - Example: Change "SPREAD (Asia Handicap):" to "SPREAD (Asia Handicap): [No data available]"

3. **Error Handling Enhancement**:
   - Review error handling in the odds data collection process
   - Ensure that partial data situations are properly documented in logs

4. **Odds API Verification**:
   - Check API documentation to understand when/why certain odds types might be unavailable
   - Verify if there are any rate limits or other constraints affecting data retrieval

## Where We Left Off

We identified that the betting odds display issue is likely not a bug but a data availability problem. The system correctly displays headers for requested data sections, but doesn't provide clear indication when data is missing.

The most promising starting point tomorrow would be to:
1. Modify `format_odds_display()` to make missing data more obvious in the output
2. Implement conditional formatting that clearly indicates when data was requested but unavailable

**Key Files to Focus On**:
- `/root/CascadeProjects/sports_bot/football/live.py` - specifically the `format_odds_display()` function
- Check the log entries for various matches to compare data availability patterns
