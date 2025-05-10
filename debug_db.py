#!/usr/bin/env python3
"""
Debug Supabase Connection State

This script displays the current status of all Supabase connection variables
to diagnose why the database connection status is being reported incorrectly.
"""
import os
import sys

# Add venv's site-packages to path if needed
venv_path = '/root/CascadeProjects/sports_bot/venv/lib/python3.12/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

print("="*60)
print("SUPABASE CONNECTION DEBUG")
print("="*60)

# First check the main configuration
print("\nTesting supabase_config.py:")
try:
    from supabase_config import supabase as config_supabase, SERVICE_KEY, SUPABASE_URL
    print(f"✅ supabase_config import successful")
    print(f"supabase object is None? {config_supabase is None}")
    print(f"SERVICE_KEY present? {'Yes' if SERVICE_KEY else 'No'}")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
except Exception as e:
    print(f"❌ Error importing from supabase_config: {str(e)}")

# Next check the db_api module
print("\nTesting logger/db_api.py:")
try:
    sys.path.append('/root/CascadeProjects/sports_bot')
    from football.logger.db_api import supabase as api_supabase
    print(f"✅ db_api import successful")
    print(f"db_api supabase object is None? {api_supabase is None}")
    print(f"Is it the same object as config_supabase? {api_supabase is config_supabase}")
except Exception as e:
    print(f"❌ Error importing from db_api: {str(e)}")

# Finally, let's see what live.py would see
print("\nTesting how live.py imports:")
try:
    # This is how live.py would import supabase
    import supabase_config
    
    # Check initial SUPABASE_AVAILABLE determination
    supabase_from_import = supabase_config.supabase
    SUPABASE_AVAILABLE = (supabase_from_import is not None)
    
    print(f"✅ Direct module import successful")
    print(f"supabase_config.supabase is None? {supabase_from_import is None}")
    print(f"SUPABASE_AVAILABLE would be set to: {SUPABASE_AVAILABLE}")
    
    # Test a actual DB operation to confirm working connection
    if supabase_from_import:
        try:
            response = supabase_from_import.table("archived_json").select("id").limit(1).execute()
            print(f"✅ Database query successful: {response}")
        except Exception as e:
            print(f"❌ Error executing database query: {str(e)}")
            
except Exception as e:
    print(f"❌ Error directly importing supabase_config: {str(e)}")

print("\n" + "="*60)
print("DEBUG COMPLETE")
print("="*60)
