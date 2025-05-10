import os
import logging
import json
import sys
from collections import defaultdict

# ========== DATABASE CONNECTION METHODS ==========
# NOTE: This system now uses the shared Supabase client from supabase_config.py
# to ensure consistent database connections across the application.
# ================================================

# Configure logging - reduce HTTP library verbosity
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db_api")
# Reduce httpx logging to ERROR level only
logging.getLogger("httpx").setLevel(logging.ERROR)

# Track database operation statistics
db_stats = {
    "success": [],
    "failed": []
}

# Import the shared supabase client
try:
    # Add parent directory to path if needed to find supabase_config
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Import the shared supabase client from the main config
    from supabase_config import supabase
    
    if supabase is not None:
        logger.info("✅ Using shared Supabase client from supabase_config.py")
    else:
        logger.warning("⚠️ Supabase client from supabase_config.py is None")
        logger.warning("Check SERVICE_KEY environment variable or supabase_config.py configuration")

except ImportError as e:
    logger.error(f"❌ Could not import supabase from supabase_config.py: {str(e)}")
    supabase = None
except Exception as e:
    logger.error(f"❌ Error accessing shared Supabase client: {str(e)}")
    supabase = None

def archive_match_json(match_data: dict) -> None:
    """
    Inserts the full match_data JSON into archived_json table via Supabase client
    using the service role key to bypass RLS policies.
    Returns True if successful, False otherwise.
    """
    if not supabase:
        logger.warning("Skipping database archiving - Supabase client not properly initialized")
        return False
    
    match_id = match_data.get('id', 'unknown')
    logger.info(f"Archiving match {match_id} to database")
        
    try:
        # Insert the match data into the archived_json table
        response = supabase.table("archived_json").insert({"raw_json": match_data}).execute()
        
        # Check for errors in the response
        if hasattr(response, 'error') and response.error:
            error_msg = f"Failed to archive match {match_id}: {response.error}"
            logger.error(error_msg)
            db_stats['failed'].append(match_id)
            
            # Provide troubleshooting help
            if "permission denied" in str(response.error).lower():
                logger.error("Permissions issue. Please check the following:")
                logger.error("1. Verify you're using the correct service role key from Supabase")
                logger.error("2. Make sure it's the full key starting with 'eyJ...' or another format")
                logger.error("3. Check for any typos or extra spaces in the key")
            elif "does not exist" in str(response.error).lower():
                logger.error("The 'archived_json' table might not exist. Create it in Supabase SQL Editor with:")
                logger.error("CREATE TABLE archived_json (id SERIAL PRIMARY KEY, raw_json JSONB, created_at TIMESTAMPTZ DEFAULT NOW());")
            return False
        else:
            logger.info(f"Match {match_id} archived successfully to Supabase")
            db_stats['success'].append(match_id)
            return True
    except Exception as e:
        error_msg = f"Error archiving match {match_id}: {str(e)}"
        logger.error(error_msg)
        db_stats['failed'].append(match_id)
        return False

def get_db_stats_summary():
    """
    Returns a formatted summary of database operations.
    Call this at the end of a batch of operations to get a summary report.
    """
    success_count = len(db_stats['success'])
    failed_count = len(db_stats['failed'])
    total = success_count + failed_count
    
    if total == 0:
        return "No database operations performed."
    
    # Reset counters after reporting
    summary = [
        f"\n------ DATABASE OPERATIONS SUMMARY ------",
        f"Total operations: {total}",
        f"✅ Successful: {success_count}",
    ]
    
    if failed_count > 0:
        summary.append(f"❌ Failed: {failed_count}")
        # Show the first few failed match IDs if any
        if failed_count <= 5:
            failed_ids = ', '.join(db_stats['failed'])
            summary.append(f"Failed match IDs: {failed_ids}")
        else:
            # Show just the first 5 if there are many
            failed_sample = ', '.join(db_stats['failed'][:5])
            summary.append(f"Sample of failed match IDs: {failed_sample}...")
    
    summary.append("----------------------------------------")
    
    # Clear stats after reporting
    db_stats['success'] = []
    db_stats['failed'] = []
    
    return "\n".join(summary)


if __name__ == "__main__":
    # Quick smoke-test
    test_data = {"match_id": "TEST123", "foo": "bar", "test_time": "now"}
    result = archive_match_json(test_data)
    
    if not supabase:
        print("⚠️ TEST FAILED: Supabase client not properly initialized")
        print("Please check the error messages above")
    else:
        print("Test complete - check logs for results")
        
    # Show database operation summary
    print(get_db_stats_summary())
