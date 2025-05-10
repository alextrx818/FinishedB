import os
from supabase import create_client, Client

# ─── Supabase credentials configuration ────────────────────────────────
SUPABASE_URL = "https://pryhbrttsgamlqxvwiap.supabase.co"
# IMPORTANT: For security, this hard-coded key should be replaced with environment variable
# after testing is complete. This is temporarily hard-coded for testing purposes only.
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InByeWhicnR0c2dhbWxxeHZ3aWFwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjM4ODg2OCwiZXhwIjoyMDYxOTY0ODY4fQ.78rTwSlIzVsIFLS4MZSw2ca45f2Jm-BayFcs6A7NilE"
# ────────────────────────────────────────────────────────────────────────────

# Initialize the client with service key to bypass Row Level Security
if SERVICE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SERVICE_KEY)
    print("✅ Supabase connection established with SERVICE_KEY")
else:
    print("⚠️ SERVICE_KEY not found, database features will be limited")
    supabase = None

def ensure_logs_table():
    """
    Verify the logs table exists in the Supabase database.
    Uses a simple SELECT to test if the table is accessible.
    """
    if not supabase:
        print("⚠️ Cannot check logs table - Supabase client is None")
        return False
        
    try:
        # Test if logs table exists by attempting to read from it
        supabase.table("logs").select("id").limit(1).execute()
        print("✅ Logs table verification completed")
        return True
    except Exception as e:
        print(f"⚠️ logs table may not exist or is not accessible: {str(e)}")
        # Provide SQL to create the table in the Supabase SQL Editor
        print("Execute this SQL in the Supabase SQL Editor to create the logs table:")
        print("""
        CREATE TABLE IF NOT EXISTS logs (
          id SERIAL PRIMARY KEY,
          level TEXT,
          msg TEXT,
          time TIMESTAMPTZ
        );
        """)
        return False

# Ensure the required tables exist if connection is established
if supabase:
    # Verify the logs table exists
    ensure_logs_table()
    
    # Verify the archived_json table exists
    try:
        # Test if archived_json table exists by attempting to read from it
        supabase.table("archived_json").select("id").limit(1).execute()
        print("✅ archived_json table verification completed")
    except Exception as e:
        print(f"⚠️ archived_json table may not exist or is not accessible: {str(e)}")
        # Provide SQL to create the table in the Supabase SQL Editor
        print("Execute this SQL in the Supabase SQL Editor to create the archived_json table:")
        print("""
        CREATE TABLE IF NOT EXISTS archived_json (
          id SERIAL PRIMARY KEY, 
          raw_json JSONB, 
          created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """)
