#!/usr/bin/env python3
"""
Trace imports when running live.py
"""
import sys
import os
from importlib.util import find_spec
from types import ModuleType

# Store original import
original_import = __import__

# Files that get imported
imported_files = set()

def custom_import(name, globals=None, locals=None, fromlist=(), level=0):
    """Custom import function that tracks imported modules"""
    module = original_import(name, globals, locals, fromlist, level)
    
    if hasattr(module, "__file__") and module.__file__:
        if module.__file__.startswith('/root/CascadeProjects/sports_bot'):
            imported_files.add(module.__file__)
    
    return module

# Replace built-in import with our custom one
sys.__import__ = custom_import
sys.meta_path.insert(0, sys)

# Run live.py
try:
    # Change to the directory of this script
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Import live module without executing it
    with open("live.py") as f:
        code = compile(f.read(), "live.py", 'exec')
        exec(code)
    
    # Print all imported files from the project
    print("\n\n=== Files imported when running live.py ===")
    for file in sorted(imported_files):
        print(file)
    
except Exception as e:
    print(f"Error tracing imports: {e}")
