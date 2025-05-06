#!/usr/bin/env python3
"""
Script to list all tables in the Supabase database
"""
import os
import sys
import requests
import json

# Add venv's site-packages to path to ensure we use the installed supabase
venv_path = '/root/CascadeProjects/sports_bot/venv/lib/python3.12/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

# Get authentication details from environment
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pryhbrttsgamlqxvwiap.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_KEY:
    print("❌ No Supabase API key found in environment variables")
    sys.exit(1)

# Direct PostgreSQL query to list all tables
SQL_QUERY = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"

# Make a direct request to the Supabase PostgreSQL REST API
headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

try:
    # First try using the Supabase REST API to execute SQL
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/rpc/execute_sql",
        headers=headers,
        json={"query": SQL_QUERY}
    )
    
    # If that fails, try the PostgreSQL REST endpoint
    if response.status_code != 200:
        print("First attempt failed, trying alternative method...\n")
        
        # Try importing and using the supabase client
        try:
            from supabase import create_client
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            # Use a system table query via REST API
            print("Checking tables using Supabase client...")
            response = supabase.table("archived_json").select("*").limit(1).execute()
            print(f"✅ 'archived_json' table exists and is accessible")
            
            response = supabase.table("main_logger_logs").select("*").limit(1).execute()
            print(f"✅ 'main_logger_logs' table exists and is accessible")
            
            print("\nIf you're not seeing data in the Supabase dashboard, check the following:")
            print("1. You're looking at the correct project (pryhbrttsgamlqxvwiap)")
            print("2. You have appropriate permissions to view the data")
            print("3. The tables have not been deleted or renamed")
            print("4. There is no Row Level Security (RLS) preventing dashboard access")
            
            sys.exit(0)
            
        except Exception as e:
            print(f"❌ Error using Supabase client: {str(e)}")
            sys.exit(1)
    
    result = response.json()
    
    if isinstance(result, list):
        print(f"Found {len(result)} tables in your Supabase database:\n")
        for idx, table in enumerate(result, 1):
            table_name = table.get('table_name', 'unknown')
            print(f"{idx}. {table_name}")
        
        # Check specifically for our tables
        table_names = [t.get('table_name', '') for t in result]
        if 'archived_json' in table_names:
            print("\n✅ 'archived_json' table exists")
        else:
            print("\n❌ 'archived_json' table DOES NOT exist")
            
        if 'main_logger_logs' in table_names:
            print("✅ 'main_logger_logs' table exists")
        else:
            print("❌ 'main_logger_logs' table DOES NOT exist")
    else:
        print("❌ Unexpected response format")
        print(result)
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    
print("\nIf tables are missing, they need to be created. The expected CREATE TABLE statements are:")
print("\nCREATE TABLE archived_json (")
print("    id SERIAL PRIMARY KEY,")
print("    raw_json JSONB,")
print("    created_at TIMESTAMPTZ DEFAULT NOW()")
print(");")
print("\nCREATE TABLE main_logger_logs (")
print("    id SERIAL PRIMARY KEY,")
print("    content TEXT,")
print("    created_at TIMESTAMPTZ DEFAULT NOW()")
print(");")
