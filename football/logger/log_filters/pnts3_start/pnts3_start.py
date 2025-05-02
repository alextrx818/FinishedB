from logger.main_logger import event_listeners, original_print
import re, os
from datetime import datetime

# where to write passing blocks
OUT_PATH = os.path.join(os.path.dirname(__file__), "pnts3_start.logger")
log_file = OUT_PATH

# Track seen IDs to avoid duplicates
seen_ids = set()

# Counter for total processed PNTS matches
pnts_count = 0

def get_eastern_time():
    import pytz
    from datetime import datetime
    return datetime.now(pytz.timezone('America/New_York'))

# Format matching the API timestamp format in the logs
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"

def handle_chunk(chunk: str):
    # 1) extract a unique ID
    m = re.search(r"Competition ID:\s*(\S+)", chunk)
    cid = m.group(1) if m else None
    if cid in seen_ids:
        print(f"[PNTS3_START] Skipping already seen Competition ID: {cid}")
        return
    # 2) find the Over/Under line's "Line: X" value
    m2 = re.search(r"Over/Under:[\s\S]*?Line:\s*([0-9]+(?:\.[0-9]+)?)", chunk)
    if not m2:
        print("[PNTS3_START] No Over/Under line found in chunk")
        return
    val = float(m2.group(1))
    # Debug print to verify filter is being invoked
    print(f"[PNTS3_START] saw Over/Under line: {val}")
    
    # 3) if it's 3.0 or above, emit it
    if 3.0 <= val <= 20.0:
        # Increment the counter
        global pnts_count
        pnts_count += 1
        print(f"[PNTS3_START] Processing match #{pnts_count} with line {val}")
        
        # Extract timestamp from the block
        ts_match = re.search(r"Timestamp:\s*([0-9/]{10}\s+[0-9:]{11}\s+[APM]{2}\s+ET)", chunk)
        timestamp = ts_match.group(1) if ts_match else get_eastern_time().strftime(API_DATETIME_FORMAT)
        
        # Build the header using the universal 50-equals format for proper buffering detection
        # Only prepend your PNTS3 header line (the chunk already has the Summary Set banner)
        header = f"\n\n{'='*50}\nPNTS3_START MATCH #{pnts_count} - {timestamp}\n{'='*50}\n\n"
        
        try:
            # Get existing content
            if os.path.exists(OUT_PATH):
                with open(OUT_PATH, 'r+') as f:
                    old = f.read()
                    f.seek(0)
                    # Only prepend the PNTS3 header + the chunk (which already has the summary banner)
                    f.write(header + chunk + "\n\n" + old)
                    f.truncate()
            else:
                # If file doesn't exist, create it
                with open(OUT_PATH, 'w') as f:
                    f.write(header + chunk + "\n")
        except Exception as e:
            print(f"[PNTS3_START] Logger write error: {e}")
            
        print(f"[PNTS3_START] Logged match with Competition ID: {cid}")
        seen_ids.add(cid)
    else:
        print(f"[PNTS3_START] Ignoring match with line {val} (below threshold)")

# 4) register your handler
print("[PNTS3_START] Filter initialized and registered with event listeners")
event_listeners.append(handle_chunk)
