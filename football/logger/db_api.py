import os
import requests
import json
import logging
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_api")

# Supabase API configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://pryhbrttsgamlqxvwiap.supabase.co")
SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Validate service key looks like a valid key before proceeding
if not SERVICE_KEY or len(SERVICE_KEY) < 20:
    logger.error("⚠️ SUPABASE_SERVICE_KEY is invalid or not set properly.")
    logger.error("Please make sure to set it with: export SUPABASE_SERVICE_KEY='your-service-key'")
    SERVICE_KEY = None

# Setup headers for API requests with service role
headers = {
    "apikey": SERVICE_KEY,
    "Authorization": f"Bearer {SERVICE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"  # Don't return the inserted record
}

def archive_match_json(match_data: dict) -> None:
    """
    Inserts the full match_data JSON into archived_json table via Supabase REST API
    using the service role key to bypass RLS policies.
    """
    if not SERVICE_KEY:
        logger.warning("Skipping database archiving - Supabase service key not properly configured")
        return
        
    try:
        # Using the service role key to bypass RLS policies
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/archived_json",
            headers=headers,
            json={"payload": match_data}
        )
        
        if response.status_code in (200, 201, 204):
            logger.info(f"✅ Match data archived successfully with ID: {match_data.get('id', 'unknown')}")
        else:
            logger.error(f"⚠️ Failed to archive via REST: {response.status_code} - {response.text}")
            
            # Provide troubleshooting help
            if "Invalid API key" in response.text:
                logger.error("The service key appears to be invalid. Please check the following:")
                logger.error("1. Verify you're using the correct service role key from Supabase")
                logger.error("2. Make sure it's the full key starting with 'eyJ...' or another format")
                logger.error("3. Check for any typos or extra spaces in the key")
            elif "does not exist" in response.text:
                logger.error("The 'archived_json' table might not exist. Create it in Supabase SQL Editor with:")
                logger.error("CREATE TABLE archived_json (id SERIAL PRIMARY KEY, payload JSONB, created_at TIMESTAMPTZ DEFAULT NOW());")
    except Exception as e:
        logger.error(f"⚠️ Error archiving match data: {str(e)}")

if __name__ == "__main__":
    # Quick smoke-test
    test_data = {"match_id": "TEST123", "foo": "bar", "test_time": "now"}
    archive_match_json(test_data)
    
    if not SERVICE_KEY:
        print("⚠️ TEST FAILED: SUPABASE_SERVICE_KEY not properly set")
        print("Please set it with: export SUPABASE_SERVICE_KEY='your-actual-service-key'")
    else:
        print("Test complete - check logs for results")
