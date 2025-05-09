from supabase import create_client, Client

# ─── Hard-coded credentials ────────────────────────────────────────────────
SUPABASE_URL         = "https://pryhbrttsgamlqxvwiap.supabase.co"
SUPABASE_ANON_KEY    = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.…"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.…"
# ────────────────────────────────────────────────────────────────────────────

# Initialize the default client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

def ensure_logs_table():
    """
    Ensure the logs table exists in the Supabase database.
    Creates the table if it doesn't exist.
    """
    try:
        # Execute SQL to create the logs table if it doesn't exist
        supabase.rpc(
            'execute_sql', 
            {
                'sql_query': '''
                CREATE TABLE IF NOT EXISTS logs (
                  id SERIAL PRIMARY KEY,
                  level TEXT,
                  msg TEXT,
                  time TIMESTAMPTZ
                );
                '''
            }
        ).execute()
        print("✅ Logs table check completed")
        return True
    except Exception as e:
        print(f"❌ Error ensuring logs table exists: {str(e)}")
        return False
