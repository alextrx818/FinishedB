import asyncio
import json
import logging
import sys
import time
import subprocess
from datetime import datetime
import pytz
from pathlib import Path

# Import fetch and merge modules
sys.path.append(Path(__file__).parent.as_posix())
import pure_json_fetch_cache
from merge_logic import merge_all_matches

# Constants
BASE_DIR = Path(__file__).parent
FULL_CACHE_FILE = BASE_DIR / "full_match_cache.json"
OUTPUT_FILE = BASE_DIR / "complete_cache_output.json"
MERGE_OUTPUT_FILE = BASE_DIR / "merge_logic.json"
SUMMARY_SCRIPT = BASE_DIR / "combined_match_summary.py"

# Logger setup
def setup_logger():
    log = logging.getLogger("orchestrator")
    log.setLevel(logging.DEBUG)
    fh = logging.FileHandler(BASE_DIR / "orchestrator.log")
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(ch)
    return log

logger = setup_logger()

def get_eastern_time():
    tz = pytz.timezone("US/Eastern")
    now = datetime.now(tz)
    return now.strftime("%m/%d/%Y %I:%M:%S %p %Z")

def unpack_full_cache(full_cache: dict):
    live = {"results": []}
    details = {}
    odds = {}
    team_cache = {}
    comp_cache = {}
    country_map = {}

    for m in full_cache.get("matches", []):
        mid = m.get("match_id")
        basic = m.get("basic_info", {})
        live["results"].append(basic)
        details[mid] = m.get("details", {})
        odds[mid] = m.get("odds", {})

        # teams
        for role in ("home_team", "away_team"):
            t = m.get("enriched", {}).get(role, {})
            tid = t.get("id")
            if tid:
                team_cache[tid] = t

        # competition
        comp = m.get("enriched", {}).get("competition", {})
        cid = comp.get("id")
        if cid:
            comp_cache[cid] = comp

        # country
        country_id = comp.get("country_id")
        country_name = m.get("metadata", {}).get("country_name")
        if country_id and country_name:
            country_map[country_id] = country_name

    return live, details, odds, team_cache, comp_cache, country_map

async def run_complete_pipeline():
    logger.info("=== STARTING COMPLETE DATA PIPELINE ===")
    logger.info(f"Start time: {get_eastern_time()}")
    start_ts = time.time()

    # STEP 1: Fetch JSON data
    logger.info("STEP 1: JSON fetch")
    try:
        await pure_json_fetch_cache.main()
        logger.info("JSON fetch completed")
    except Exception as e:
        logger.error(f"JSON fetch failed: {e}")
        return

    # STEP 2: Prepare data for merge
    logger.info("STEP 2: Preparing data for merge")
    if not FULL_CACHE_FILE.exists():
        logger.error(f"Cache file missing: {FULL_CACHE_FILE}")
        return

    full_cache = json.loads(FULL_CACHE_FILE.read_text())
    live_data, details_by_id, odds_by_id, team_cache, comp_cache, country_map = unpack_full_cache(full_cache)

    logger.info(f"Prepared {len(live_data['results'])} matches")
    logger.info(f"Team cache size: {len(team_cache)}")
    logger.info(f"Competition cache size: {len(comp_cache)}")
    logger.info(f"Country map size: {len(country_map)}")

    # STEP 3: Merge logic
    logger.info("STEP 3: Running merge logic")
    try:
        merged = merge_all_matches(
            live_data, details_by_id, odds_by_id,
            team_cache, comp_cache, country_map
        )
        merged = [{"created_at": get_eastern_time(), **m} for m in merged]
        logger.info(f"Merged {len(merged)} records")
    except Exception as e:
        logger.error(f"Merge logic failed: {e}")
        return

    # STEP 4: Save output
    logger.info("STEP 4: Saving output files")
    complete_output = {
        "matches": merged,
        "metadata": {
            "total_matches": len(merged),
            "fetch_time": get_eastern_time(),
            "pipeline_duration_sec": round(time.time() - start_ts, 2),
            "cache_stats": full_cache.get("metadata", {}).get("cache_stats", {}),
            "cache_metrics": full_cache.get("metadata", {}).get("cache_metrics", {})
        }
    }

    OUTPUT_FILE.write_text(json.dumps(complete_output, indent=2))
    MERGE_OUTPUT_FILE.write_text(json.dumps(merged, indent=2))
    logger.info(f"Wrote complete output to {OUTPUT_FILE}")
    logger.info(f"Wrote merge-only output to {MERGE_OUTPUT_FILE}")

    # STEP 5: Run summary script
    logger.info("STEP 5: Printing match summaries")
    try:
        subprocess.run([sys.executable, str(SUMMARY_SCRIPT)], check=True)
        logger.info("Match summaries printed successfully")
    except subprocess.CalledProcessError as e:
        logger.error(f"Summary script failed: {e}")

    logger.info("=== PIPELINE COMPLETE ===")
    logger.info(f"End time: {get_eastern_time()}")
    logger.info(f"Total duration: {round(time.time() - start_ts, 2)}s")

def print_instructions():
    """Print instructions for scheduling the pipeline using cron"""
    logger.info("""
=== SCHEDULING INSTRUCTIONS ===

To run this pipeline every 30 seconds using cron:

1. Create a shell script wrapper (run_pipeline.sh):
   #!/bin/bash
   cd /root/CascadeProjects/sports_bot/football/main
   python orchestrate_complete.py

2. Make it executable: chmod +x run_pipeline.sh

3. Add to crontab (every minute, it will handle its own rate limiting):
   * * * * * /root/CascadeProjects/sports_bot/football/main/run_pipeline.sh

Alternatively, use a simple while loop in a shell script:
   while true; do
     python orchestrate_complete.py
     sleep 30
   done
""")

if __name__ == "__main__":
    # Print scheduling instructions
    print_instructions()
    
    # Run the pipeline once directly
    logger.info("Running pipeline once...")
    asyncio.run(run_complete_pipeline())
    
    logger.info("Pipeline run complete! Use scheduling instructions above for recurring execution.")
