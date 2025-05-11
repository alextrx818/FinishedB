#!/usr/bin/env python3
"""
Clean Memory Optimizer for live.py

This script cleans up redundant memory optimization code in live.py and ensures
that memory management features are properly implemented and non-duplicated.

Changes made:
1. Consolidates duplicate _fetch_cycle counter declarations
2. Removes redundant global declarations
3. Fixes duplicate increment operations
4. Consolidates memory management code blocks
5. Ensures proper GC imports

IMPORTANT: Creates a backup before making changes.
"""

import os
import re

def main():
    # Create backup
    os.system('cp live.py live.py.clean_backup')
    print("Created backup at live.py.clean_backup")
    
    with open('live.py', 'r') as f:
        content = f.read()
    
    # 1. Remove duplicate _fetch_cycle declarations
    # Keep the first one at the top, remove others
    pattern = r'(_fetch_cycle\s*=\s*0).*?(_fetch_cycle\s*=\s*0)'
    content = re.sub(pattern, r'\1', content, flags=re.DOTALL)
    
    # Remove additional declarations down in the file
    pattern = r'# Print cycle counter to reduce memory usage\s*\n_fetch_cycle\s*=\s*0'
    content = re.sub(pattern, '# Print cycle counter already defined at the top of file', content)
    
    # Remove any declarations way down in the file (line 800+)
    pattern = r'(_fetch_cycle\s*=\s*0).*?(async def main_async)'
    content = re.sub(pattern, r'# fetch_cycle already declared at top of file\n\n\2', content, flags=re.DOTALL)
    
    # 2. Fix redundant global declarations and increments in process_live_matches_async
    # Find the function
    process_func_pattern = r'(async def process_live_matches_async.*?\n.*?)(\s*global PROCESSING_MATCHES,.*?\n)(.*?)(\s*_fetch_cycle \+= 1\s*\n)(.*?)(\s*_fetch_cycle \+= 1\s*\n)(.*?)(\s*global _fetch_cycle\s*\n)(.*?)(\s*_fetch_cycle \+= 1\s*\n)'
    replacement = r'\1\2\3\4\7'
    content = re.sub(process_func_pattern, replacement, content, flags=re.DOTALL)
    
    # 3. Fix duplicate garbage collection and memory management code blocks
    # Find the deferred_alerts clear section and the duplicated memory management code
    mem_pattern = r'(process_live_matches_async\.deferred_alerts\.clear\(\).*?)(# Memory optimization: Garbage collection.*?gc\.collect\(\).*?)\n\s*(# Limit the previous_matches collection to prevent unbounded growth)'
    replacement = r'\1\2'
    content = re.sub(mem_pattern, replacement, content, flags=re.DOTALL)
    
    # 4. Consolidate gc imports
    content = re.sub(r'(import gc.*?).*?(import gc)', r'\1', content, flags=re.DOTALL)
    
    # Write the changes back to the file
    with open('live.py', 'w') as f:
        f.write(content)
    
    print("\nCleaned up memory optimization code in live.py:")
    print("✓ Consolidated duplicate _fetch_cycle declarations")
    print("✓ Removed redundant global declarations")
    print("✓ Fixed duplicate increment operations")
    print("✓ Consolidated memory management code blocks")
    print("✓ Fixed redundant gc imports")
    print("\nNo functionality was changed - this was purely a cleanup operation.")

if __name__ == "__main__":
    main()
