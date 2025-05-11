import datetime
import pytz
from typing import Any, Dict, List, Optional

# ======= Time & Formatting Constants =======
EASTERN = pytz.timezone('America/New_York')
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"
DATE_FORMAT = "%m/%d/%Y"
TIME_FORMAT = "%I:%M:%S %p"

# ======= Conversion Functions =======
def decimal_to_american(decimal_odds: float) -> int:
    """
    Convert European decimal odds to American format.
    """
    try:
        d = float(decimal_odds)
        if d >= 2.0:
            return int(round((d - 1) * 100))
        else:
            return int(round(-100 / (d - 1)))
    except Exception:
        return 0


def hk_to_american(hk_odds: float) -> int:
    """
    Convert Hong Kong odds to American format.
    """
    try:
        h = float(hk_odds)
        if h >= 1.0:
            return int(round(h * 100))
        else:
            return int(round(-100 / h))
    except Exception:
        return 0

# ======= Utility Functions =======
def get_eastern_time() -> datetime.datetime:
    """Return current time in Eastern Time (ET)."""
    return datetime.datetime.now(pytz.utc).astimezone(EASTERN)


def pick_latest(entries: List[Dict[str, Any]]):
    """Pick entry from minute 4-6 or fallback to last."""
    if not entries:
        return None
    for e in entries:
        if e.get('time_of_match') in ['4','5','6']:
            return e
    return entries[-1]

# ======= Normalization =======
def normalize_match_data(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Unpack raw JSON into named fields and convert odds to American.
    """
    data = raw.copy()
    # Score unpacking
    score_arr = raw.get('score', [])
    try:
        home, away = score_arr[2], score_arr[3]
        data['home_score']    = home[0]
        data['home_ht_score'] = home[1]
        data['away_score']    = away[0]
        data['away_ht_score'] = away[1]
    except Exception:
        pass
    # Odds conversion
    odds = raw.get('odds', {})
    # ML
    ml = pick_latest(odds.get('ML', [])) or {}
    if 'home_win' in ml:
        data['ml_home_american'] = decimal_to_american(ml['home_win'])
        data['ml_draw_american'] = decimal_to_american(ml['draw'])
        data['ml_away_american'] = decimal_to_american(ml['away_win'])
    # Spread
    sp = pick_latest(odds.get('SPREAD', [])) or {}
    if 'home_win' in sp:
        data['spread_home_american'] = hk_to_american(sp['home_win'])
        data['spread_handicap']      = sp.get('handicap')
        data['spread_away_american'] = hk_to_american(sp['away_win'])
    # Over/Under
    ou = pick_latest(odds.get('Over/Under', [])) or {}
    if 'over' in ou:
        data['ou_over_american']  = hk_to_american(ou['over'])
        data['ou_handicap']       = ou.get('handicap')
        data['ou_under_american'] = hk_to_american(ou['under'])
    return data

# ======= Formatting =======
def format_odds_display(formatted_odds: Dict[str, Any]) -> str:
    """Render ML, Spread, and Over/Under blocks."""
    lines: List[str] = []
    tm = ['4','5','6']
    # ML
    if 'ML' in formatted_odds and formatted_odds['ML']:
        ml = sorted(formatted_odds['ML'], key=lambda e: int(e.get('time_of_match', 1000)) if str(e.get('time_of_match', '')).isdigit() else 1000)
        e = next((x for x in ml if x['time_of_match'] in tm), ml[0])
        t = e['time_of_match']; note = '' if t in tm else f" (Closest: {t})"
        lines.append('ML (Money Line):')
        lines.append(f"Time: {t} min | Home: {e['home_win']:+d} | Draw: {e['draw']:+d} | Away: {e['away_win']:+d}{note}")
    # Spread
    if 'SPREAD' in formatted_odds and formatted_odds['SPREAD']:
        sp = sorted(formatted_odds['SPREAD'], key=lambda e: int(e.get('time_of_match', 1000)) if str(e.get('time_of_match', '')).isdigit() else 1000)
        e = next((x for x in sp if x['time_of_match'] in tm), sp[0])
        t = e['time_of_match']; note = '' if t in tm else f" (Closest: {t})"
        lines.append('\nSPREAD (Asia Handicap):')
        lines.append(f"Time: {t} min | Home: {e['home_win']:+d} | Handicap: {e['handicap']} | Away: {e['away_win']:+d}{note}")
    # Over/Under
    if 'Over/Under' in formatted_odds and formatted_odds['Over/Under']:
        ou = sorted(formatted_odds['Over/Under'], key=lambda e: int(e.get('time_of_match', 1000)) if str(e.get('time_of_match', '')).isdigit() else 1000)
        e = next((x for x in ou if x['time_of_match'] in tm), ou[0])
        t = e['time_of_match']; note = '' if t in tm else f" (Closest: {t})"
        lines.append('\nOver/Under:')
        lines.append(f"Time: {t} min | Over: {e['over']:+d} | Line: {e['handicap']} | Under: {e['under']:+d}{note}")
    return '\n'.join(lines) or 'No odds data available'


def generate_match_summary_text(match: Dict[str, Any]) -> str:
    """Build the core summary block from normalized data."""
    parts: List[str] = []
    i, tot = match.get('_loop_index'), match.get('_total_matches')
    parts.append(f"MATCH #{i} OF {tot}")
    parts.append("\n----- MATCH SUMMARY -----")
    parts.append(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
    parts.append(f"Match ID: {match.get('id')}")
    parts.append(f"Competition ID: {match.get('competition_id')}")
    parts.append(f"Competition: {match.get('competition')} ({match.get('country')})")
    parts.append(f"Match: {match.get('home_team')} vs {match.get('away_team')}")
    parts.append(f"Score: {match.get('home_score')} - {match.get('away_score')} (HT: {match.get('home_ht_score')} - {match.get('away_ht_score')})")
    status = match.get('status_description') or match.get('status', {}).get('description', 'Unknown')
    parts.append(f"Status: {status}")
    odds = format_odds_display(match.get('odds', {}))
    parts.append("\n--- MATCH BETTING ODDS ---")
    parts.append(odds)
    parts.append("\n--- MATCH ENVIRONMENT ---")
    env = []
    for k in ('weather','temperature','humidity','wind'):
        v = match.get(k)
        if v:
            env.append(f"{k.capitalize()}: {v}")
    parts.append('\n'.join(env) if env else "No environment data available")
    return '\n'.join(parts)


def format_full_match_block(raw: Dict[str, Any], set_number: Optional[int] = None) -> str:
    """
    Full framed block: Summary Set + separators + summary text.
    """
    match = normalize_match_data(raw)
    header = f"-- Summary Set #{set_number} for {get_eastern_time().strftime(DATE_FORMAT)} --- {get_eastern_time().strftime(TIME_FORMAT)}" if set_number else ''
    sep = '=' * 50
    core = generate_match_summary_text(match)
    return '\n'.join([header, sep, core, sep])
