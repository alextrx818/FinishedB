#!/usr/bin/env python3
"""
Simple memory optimization script for live.py

This script makes targeted changes to reduce memory usage:
1. Ensures fetch cycle counter is properly implemented 
2. Implements collection size limiting
3. Adds garbage collection
4. Adds memory usage monitoring
"""

import os
import re

def main():
    # Make a backup if one doesn't already exist
    if not os.path.exists('live.py.memory_backup'):
        os.system('cp live.py live.py.memory_backup')
        print("Created backup at live.py.memory_backup")
    
    with open('live.py', 'r') as f:
        content = f.readlines()
    
    # 1. First ensure we have the fetch counter
    has_counter = False
    for i, line in enumerate(content):
        if re.search(r'_fetch_cycle\s*=\s*0', line):
            has_counter = True
            break
    
    if not has_counter:
        # Add counter near the top after other globals
        for i, line in enumerate(content):
            if 'VERBOSE_OUTPUT = False' in line:
                content.insert(i+2, "\n# Counter for memory optimization cycles\n_fetch_cycle = 0\n\n")
                break
    
    # 2. Add increment in process_live_matches_async
    increment_added = False
    for i, line in enumerate(content):
        if 'def process_live_matches_async' in line:
            # Look for global declaration
            for j in range(i, i+10):
                if j < len(content) and 'global PROCESSING_MATCHES' in content[j]:
                    if '_fetch_cycle' not in content[j]:
                        content[j] = content[j].replace('global PROCESSING_MATCHES', 'global PROCESSING_MATCHES, _fetch_cycle')
                    break
            
            # Look for place to add increment
            for j in range(i, i+15):
                if j < len(content) and 'PROCESSING_MATCHES = True' in content[j]:
                    # Add fetch cycle increment after this line
                    if not any('_fetch_cycle += 1' in content[k] for k in range(j+1, j+5)):
                        content.insert(j+1, "    # Increment memory optimization cycle counter\n    _fetch_cycle += 1\n\n")
                        increment_added = True
                    break
            break
    
    # 3. Add/ensure deferred alerts cleanup and GC
    gc_added = False
    for i, line in enumerate(content):
        if 'process_live_matches_async.deferred_alerts.clear()' in line:
            # Check if GC is already present
            has_gc = False
            for j in range(i+1, i+10):
                if j < len(content) and 'gc.collect()' in content[j]:
                    has_gc = True
                    break
            
            if not has_gc:
                content.insert(i+1, "\n        # Force garbage collection every few cycles\n        if _fetch_cycle % 3 == 0:  # Every 3 cycles\n            import gc\n            gc.collect()\n            print(f\"Garbage collection performed on cycle {_fetch_cycle}\")\n")
                gc_added = True
            break
    
    # 4. Add collection size limiting if not present
    limit_added = False
    if gc_added:
        # Find where we added GC
        for i, line in enumerate(content):
            if 'gc.collect()' in line and '_fetch_cycle' in content[i+1]:
                # Add after this block
                content.insert(i+3, "\n        # Limit the previous_matches collection to prevent unbounded growth\n        if len(process_live_matches_async.previous_matches) > 100:\n            print(f\"Trimming previous_matches from {len(process_live_matches_async.previous_matches)} to 100 entries\")\n            \n            # Get a list of entries (keep most recent by default)\n            entries = list(process_live_matches_async.previous_matches.items())\n            \n            # Remove oldest entries beyond the 100 limit\n            for match_id, _ in entries[:-100]:\n                del process_live_matches_async.previous_matches[match_id]\n")
                limit_added = True
                break
    else:
        # Find deferred_alerts.clear()
        for i, line in enumerate(content):
            if 'process_live_matches_async.deferred_alerts.clear()' in line:
                # Check if limiting is already present
                has_limit = False
                for j in range(i+1, i+15):
                    if j < len(content) and 'len(process_live_matches_async.previous_matches) > 100' in content[j]:
                        has_limit = True
                        break
                
                if not has_limit:
                    content.insert(i+1, "\n        # Limit the previous_matches collection to prevent unbounded growth\n        if len(process_live_matches_async.previous_matches) > 100:\n            print(f\"Trimming previous_matches from {len(process_live_matches_async.previous_matches)} to 100 entries\")\n            \n            # Get a list of entries (keep most recent by default)\n            entries = list(process_live_matches_async.previous_matches.items())\n            \n            # Remove oldest entries beyond the 100 limit\n            for match_id, _ in entries[:-100]:\n                del process_live_matches_async.previous_matches[match_id]\n")
                    limit_added = True
                break
    
    # 5. Add memory monitoring before refresh message
    monitoring_added = False
    for i, line in enumerate(content):
        if 'Refreshing in 30 seconds... (Press Ctrl+C to exit)' in line:
            # Check if monitoring is already present
            has_monitoring = False
            for j in range(i-5, i):
                if j >= 0 and 'MEMORY STATS' in content[j]:
                    has_monitoring = True
                    break
            
            if not has_monitoring:
                content.insert(i-1, "\n    # Print memory usage statistics\n    if hasattr(process_live_matches_async, 'previous_matches'):\n        print(f\"\\n----- MEMORY STATS -----\")\n        print(f\"Previous matches: {len(process_live_matches_async.previous_matches)}\")\n        if hasattr(process_live_matches_async, 'deferred_alerts'):\n            print(f\"Deferred alerts: {len(process_live_matches_async.deferred_alerts)}\")\n        print(\"-\" * 30)\n")
                monitoring_added = True
            break
    
    # Write the changes back to the file
    with open('live.py', 'w') as f:
        f.writelines(content)
    
    # Report on changes
    print("\nMemory optimization changes applied:")
    if has_counter:
        print("✓ Fetch cycle counter already present")
    else:
        print("+ Added fetch cycle counter")
    
    if increment_added:
        print("+ Added fetch cycle incrementing")
    else:
        print("✓ Fetch cycle incrementing already present")
    
    if gc_added:
        print("+ Added garbage collection every 3 cycles")
    else:
        print("✓ Garbage collection already present")
    
    if limit_added:
        print("+ Added collection size limiting (max 100 entries)")
    else:
        print("✓ Collection size limiting already present")
    
    if monitoring_added:
        print("+ Added memory usage monitoring")
    else:
        print("✓ Memory usage monitoring already present")
    
    print("\nThese changes will help reduce memory usage and prevent VS Code from bogging down.")

if __name__ == "__main__":
    main()
