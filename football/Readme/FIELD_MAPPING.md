# Field Mapping Documentation

This document maps the output fields shown in the match summary to their corresponding JSON fields from the API responses.

## Match Summary Section

```
Competition ID: v2y8m4zhydql074
Competition: Uruguay Primera Division (Uruguay)
Match: Montevideo City Torque vs Montevideo Wanderers FC
Score: 0 - 0 (HT: 0 - 0)
Status: Unknown
```

| Output Field | API JSON Path | Notes |
|--------------|--------------|-------|
| Competition ID | `match_data["competition_id"]` | Direct mapping |
| Competition | `competition_info["results"][0]["name"]` + `(country_map[competition_country_id])` | Combines competition name and country |
| Match | `home_team_name` + " vs " + `away_team_name` | Combines home and away team names from team API calls |
| Score | `match_data["home_score"]` + " - " + `match_data["away_score"]` | Current match score |
| HT Score | `match_data["home_score_half"]` + " - " + `match_data["away_score_half"]` | Half-time score |
| Status | `match_data["status_name"]` | Match status (e.g., "1st half", "2nd half") |

## Match Betting Odds Section

```
--- MATCH BETTING ODDS ---
DEBUG ML: Home: 160 | Draw: 210 | Away: 175
ML (Money Line):
Time: 4 min | Home: +160 | Draw: +210 | Away: +175

SPREAD (Asia Handicap):
Time: 4 min | Home: -122 | Handicap: 0.0 | Away: -104

Over/Under:
Time: 4 min | Over: -108 | Line: 2.25 | Under: -115
```

### Money Line (ML)

| Output Field | API JSON Path | Notes |
|--------------|--------------|-------|
| Time | `bookmaker_data["eu"][entry_index][1]` | Minutes of the match when odds were recorded |
| Home | Converted from `bookmaker_data["eu"][entry_index][2]` | Home win decimal odds converted to American odds |
| Draw | Converted from `bookmaker_data["eu"][entry_index][3]` | Draw decimal odds converted to American odds |
| Away | Converted from `bookmaker_data["eu"][entry_index][4]` | Away win decimal odds converted to American odds |

### SPREAD (Asia Handicap)

| Output Field | API JSON Path | Notes |
|--------------|--------------|-------|
| Time | `bookmaker_data["asia"][entry_index][1]` | Minutes of the match when odds were recorded |
| Home | Converted from `bookmaker_data["asia"][entry_index][2]` | Home handicap Hong Kong odds converted to American |
| Handicap | `bookmaker_data["asia"][entry_index][3]` | Handicap value (e.g., -0.5, 0, 1.5) |
| Away | Converted from `bookmaker_data["asia"][entry_index][4]` | Away handicap Hong Kong odds converted to American |

### Over/Under

| Output Field | API JSON Path | Notes |
|--------------|--------------|-------|
| Time | `bookmaker_data["bs"][entry_index][1]` | Minutes of the match when odds were recorded |
| Over | Converted from `bookmaker_data["bs"][entry_index][2]` | Over Hong Kong odds converted to American |
| Line | `bookmaker_data["bs"][entry_index][3]` | Total goals line (e.g., 2.5) |
| Under | Converted from `bookmaker_data["bs"][entry_index][4]` | Under Hong Kong odds converted to American |

## Match Environment Section

```
--- MATCH ENVIRONMENT ---
Weather: Partially cloudy
Wind: 1.8m/s
Humidity: 88%
```

| Output Field | API JSON Path | Notes |
|--------------|--------------|-------|
| Weather | `match_data["environment"]["weather"]` | Converted from weather code to text description |
| Wind | `match_data["environment"]["wind"]` | Wind speed in m/s (also converted to mph in display) |
| Humidity | `match_data["environment"]["humidity"]` | Humidity percentage |
| Temperature | `match_data["environment"]["temperature"]` | Temperature (not in example but available in API) |

## Odds Conversion Formulas

### Decimal to American Odds (for Money Line)
- For decimal odds ≥ 2.0: `(decimal - 1) * 100` (with + sign)
- For decimal odds < 2.0: `-100 / (decimal - 1)` (with - sign)

### Hong Kong to American Odds (for SPREAD and Over/Under)
- For Hong Kong odds ≥ 1.0: `odds * 100` (with + sign)
- For Hong Kong odds < 1.0: `-100 / odds` (with - sign)
