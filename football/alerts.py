#!/usr/bin/env python3
import sys, json, re
from telegram import send_match_alert
# If you extracted the generator to core.py, import it:
from live import generate_match_summary_text

# Track which match+rule combinations have already fired
ALERTED = {
    "no_goals_ht_ou_3_5": set(),
    # add more rule-names here as you need...
}

def rule_no_goals_ht_ou_3_5(m):
    # Example criterion:
    if m["status_id"] != "3":            return False
    if m["ou_line"] != 3.5:              return False
    if int(m["home_score"])+int(m["away_score"]) != 0: return False
    key = m["competition_id"] + ":" + m["id"]
    if key in ALERTED["no_goals_ht_ou_3_5"]: return False
    ALERTED["no_goals_ht_ou_3_5"].add(key)
    return True

def main():
    for raw in sys.stdin:
        if not raw.startswith("__MATCH_JSON__ "):
            continue
        _, blob = raw.split(" ", 1)
        match = json.loads(blob)
        # Check each alert rule in turn:
        if rule_no_goals_ht_ou_3_5(match):
            # Using the summary generator from live.py
            text = generate_match_summary_text(match, match["odds"])
            send_match_alert(text)

if __name__ == "__main__":
    main()
