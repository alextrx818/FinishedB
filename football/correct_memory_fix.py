#!/usr/bin/env python3
"""
Correctly structured memory optimization for live.py
"""

# First add the module-level counter
with open('live.py', 'r') as f:
    content = f.readlines()

# Add the counter declaration at the top
counter_added = False
for i, line in enumerate(content):
    if line.startswith('# Initialize availability flags'):
        content.insert(i, '# Counter for memory optimization\n_fetch_cycle = 0\n\n')
        counter_added = True
        break

if not counter_added:
    content.insert(3, '# Counter for memory optimization\n_fetch_cycle = 0\n\n')

# Fix the function declaration to have the global at the top
func_fixed = False
for i, line in enumerate(content):
    if line.strip().startswith('async def process_live_matches_async'):
        # Find the line with the PROCESSING_MATCHES = True
        for j in range(i, i+10):
            if j < len(content) and 'PROCESSING_MATCHES = True' in content[j]:
                # Replace with proper global declaration and increment
                content[j-1] = '    global PROCESSING_MATCHES, _fetch_cycle\n'
                content[j+1] = '    \n    # Increment cycle counter for memory optimization\n    _fetch_cycle += 1\n'
                func_fixed = True
                break
        if func_fixed:
            break

# Remove any duplicate declarations
for i in range(len(content)-1, -1, -1):
    if i < len(content) and 'global _fetch_cycle' in content[i] and i > 2000:
        content.pop(i)
        # Also remove the increment line that follows
        if i < len(content) and '_fetch_cycle += 1' in content[i]:
            content.pop(i)

# Find the deferred_alerts.clear() line to add our memory optimizations
for i, line in enumerate(content):
    if 'process_live_matches_async.deferred_alerts.clear()' in line:
        # Add garbage collection and collection size limiting
        memory_code = """        # reset for next round
        process_live_matches_async.deferred_alerts.clear()
        
        # Memory optimization: Garbage collection
        import gc
        gc.collect()
        
        # Memory optimization: Limit collection size
        if len(process_live_matches_async.previous_matches) > 100:
            # Get list of entries and limit to most recent 100
            entries = list(process_live_matches_async.previous_matches.items())
            for match_id, _ in entries[:-100]:
                del process_live_matches_async.previous_matches[match_id]
            print(f"Trimmed previous_matches from {len(entries)} to 100 entries")
"""
        # Replace the original line with our optimized version
        content[i] = memory_code
        break

# Add memory monitoring before refresh message
for i, line in enumerate(content):
    if 'Refreshing in 30 seconds' in line:
        # Add memory stats
        stats_code = """    # Memory usage monitoring
    print(f"\\n----- MEMORY STATS -----")
    print(f"Previous matches: {len(process_live_matches_async.previous_matches)}")
    print(f"Deferred alerts: {len(process_live_matches_async.deferred_alerts)}")
    print("-" * 30)
    
"""
        content.insert(i, stats_code)
        break

# Write the updated content back to the file
with open('live.py', 'w') as f:
    f.writelines(content)

print("Memory optimizations successfully implemented:")
print("1. Added _fetch_cycle counter at module level")
print("2. Properly added global declaration at the top of the function")
print("3. Added garbage collection")
print("4. Limited collection size to 100 entries")
print("5. Added memory usage monitoring")
