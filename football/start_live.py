#!/usr/bin/env python3
"""
Startup script for live.py that ensures the Supabase client is available
This does NOT modify live.py itself, but sets up the environment correctly
"""
import os
import sys
import subprocess

# Add the virtual environment site-packages to Python path
venv_path = '/root/CascadeProjects/sports_bot/venv/lib/python3.12/site-packages'
if os.path.exists(venv_path) and venv_path not in sys.path:
    sys.path.insert(0, venv_path)

# Make the virtual environment available for live.py
os.environ['PYTHONPATH'] = venv_path + ':' + os.environ.get('PYTHONPATH', '')

# Execute live.py directly (as required)
live_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live.py")
print(f"Starting sports bot with proper environment setup...")
print(f"Executing: python3 {live_script}")
print(f"PYTHONPATH set to include: {venv_path}")
print("-" * 80)

# Use execv to replace current process with live.py
os.execv("/usr/bin/python3", ["python3", live_script])
