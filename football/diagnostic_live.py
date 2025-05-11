#!/usr/bin/env python3
"""
Diagnostic version of live.py to safely identify issues
"""
import os
import sys
import traceback

# Record original stdout for error reports
original_stdout = sys.stdout

# Create log file for diagnostics
DIAGNOSTIC_LOG = "/root/CascadeProjects/sports_bot/football/diagnostic_crash.log"

# Initialize with process info
with open(DIAGNOSTIC_LOG, "w") as f:
    f.write(f"Diagnostic started at: {os.popen('date').read().strip()}\n")
    f.write(f"Process ID: {os.getpid()}\n")
    f.write("=== Environment Info ===\n")
    f.write(f"Python version: {sys.version}\n")
    f.write(f"Working directory: {os.getcwd()}\n\n")
    f.write("=== Starting Import Phase ===\n\n")

try:
    # Redirect stdout to our diagnostic file temporarily
    diagnostic_file = open(DIAGNOSTIC_LOG, "a")
    sys.stdout = diagnostic_file
    
    print("Importing core libraries...")
    import time
    import json
    import datetime
    import asyncio
    import pytz
    from typing import Dict, List, Tuple, Optional, Any, Union
    
    print("Attempting to import alert system...")
    try:
        from all_alerts.live_match_alerts import main_match_alerts
        print("✓ Successfully imported main_match_alerts")
    except Exception as e:
        print(f"⚠️ Failed to import main_match_alerts: {e}")
        print(traceback.format_exc())
    
    print("\n=== Import Phase Complete ===\n")
    print("=== Starting Main Execution ===\n")
    
    # Restore stdout for normal output
    sys.stdout = original_stdout
    
    print("Diagnostic mode: About to run in live.py...")
    print(f"Check {DIAGNOSTIC_LOG} for detailed logs")
    
    # Import the live module for inspection but don't run it
    import live
    
    # Output module structure to help diagnose
    with open(DIAGNOSTIC_LOG, "a") as f:
        f.write("\n=== Module Structure ===\n")
        # Get all attributes of the live module
        for attr in dir(live):
            # Skip built-in attributes and private attributes
            if not attr.startswith('__'):
                try:
                    f.write(f"{attr}: {type(getattr(live, attr))}\n")
                except:
                    f.write(f"{attr}: <Error accessing attribute>\n")
    
    print("Diagnostic complete without errors.")
    print(f"Check {DIAGNOSTIC_LOG} for detailed information.")
    
except Exception as e:
    # Restore stdout in case of exception
    sys.stdout = original_stdout
    
    print(f"DIAGNOSTIC ERROR: {e}")
    
    # Log the error to our diagnostic file
    with open(DIAGNOSTIC_LOG, "a") as f:
        f.write(f"\n\n=== CRASH DETECTED ===\n")
        f.write(f"Error: {e}\n\n")
        f.write("Traceback:\n")
        f.write(traceback.format_exc())
    
    print(f"Error details have been written to {DIAGNOSTIC_LOG}")
    
finally:
    # Make sure we clean up our file descriptor
    if 'diagnostic_file' in locals() and not diagnostic_file.closed:
        sys.stdout = original_stdout
        diagnostic_file.close()
