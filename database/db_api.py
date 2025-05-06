import os
import logging
import json

# ========== DATABASE CONNECTION METHODS ==========
# NOTE: This system now uses the Supabase Python client library
# instead of direct REST API calls. The previous implementation used
# direct REST API calls for minimal dependencies, but we've switched
# to the official client for better maintainability and features.
# ================================================

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_api")

# Import Supabase client
try:
    from supabase import create_client
except ImportError:
    logger.error("⚠️ Supabase Python client not installed. Please install with:")
    logger.error("pip install supabase")
    create_client = None

# Supabase API configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pryhbrttsgamlqxvwiap.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY")

# Initialize client if possible
supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY and len(SUPABASE_KEY) >= 20:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("✅ Supabase client initialized successfully")
    except Exception as e:
        logger.error(f"⚠️ Error initializing Supabase client: {str(e)}")
else:
    if not create_client:
        logger.error("⚠️ Supabase Python client library not available")
    if not SUPABASE_KEY or len(SUPABASE_KEY) < 20:
        logger.error("⚠️ SUPABASE_KEY is invalid or not set properly")
        logger.error("Please make sure to set it with: export SUPABASE_KEY='your-service-key'")
        logger.error("(The old SUPABASE_SERVICE_KEY is also checked as a fallback)")

def archive_match_json(match_data: dict) -> None:
    """
    Inserts the full match_data JSON into archived_json table via Supabase client
    using the service role key to bypass RLS policies.
    """
    if not supabase:
        logger.warning("Skipping database archiving - Supabase client not properly initialized")
        return
        
    try:
        # Insert the match data into the archived_json table
        response = supabase.table("archived_json").insert({"raw_json": match_data}).execute()
        
        # Check for errors in the response
        if hasattr(response, 'error') and response.error:
            logger.error(f"⚠️ Failed to archive via Supabase client: {response.error}")
            
            # Provide troubleshooting help
            if "permission denied" in str(response.error).lower():
                logger.error("Permissions issue. Please check the following:")
                logger.error("1. Verify you're using the correct service role key from Supabase")
                logger.error("2. Make sure it's the full key starting with 'eyJ...' or another format")
                logger.error("3. Check for any typos or extra spaces in the key")
            elif "does not exist" in str(response.error).lower():
                logger.error("The 'archived_json' table might not exist. Create it in Supabase SQL Editor with:")
                logger.error("CREATE TABLE archived_json (id SERIAL PRIMARY KEY, raw_json JSONB, created_at TIMESTAMPTZ DEFAULT NOW());")
        else:
            logger.info(f"✅ Match data archived successfully with ID: {match_data.get('id', 'unknown')}")
    except Exception as e:
        logger.error(f"⚠️ Error archiving match data: {str(e)}")

if __name__ == "__main__":
    # Quick smoke-test
    test_data = {"match_id": "TEST123", "foo": "bar", "test_time": "now"}
    archive_match_json(test_data)
    
    if not supabase:
        print("⚠️ TEST FAILED: Supabase client not properly initialized")
        print("Please check the error messages above")
    else:
        print("Test complete - check logs for results")
