#!/usr/bin/env python3
"""
Test script to verify database connection to Supabase
This is a standalone script that does not modify live.py
"""

import os
import sys
import json
from datetime import datetime

# Add venv's site-packages to path to ensure we use the installed supabase
venv_path = '/root/CascadeProjects/sports_bot/venv/lib/python3.12/site-packages'
if venv_path not in sys.path:
    sys.path.insert(0, venv_path)

# Import database functions    
from logger.db_api import archive_match_json, supabase

def test_database_connection():
    """Test the database connection and display status"""
    print("\n===== DATABASE CONNECTION TEST =====")
    
    # Check if Supabase client is initialized
    if supabase:
        print("✅ Supabase client is initialized")
        
        # Generate test data
        test_data = {
            "test_id": f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "message": "Database connection test",
            "timestamp": datetime.now().isoformat()
        }
        
        # Test writing to the database
        print(f"\nAttempting to write test data to database...")
        try:
            archive_match_json(test_data)
            print("✅ Test data written successfully!")
            
            # Try to read from the database
            print("\nAttempting to read from database...")
            response = supabase.table("archived_json").select("*").limit(5).execute()
            
            if hasattr(response, 'data') and response.data:
                print(f"✅ Successfully read {len(response.data)} records from database")
                print("\nLatest 5 records:")
                for idx, record in enumerate(response.data[:5], 1):
                    # Pretty print with indentation
                    if 'raw_json' in record:
                        record_excerpt = json.dumps(record['raw_json'], indent=2)[:100] + "..."
                    else:
                        record_excerpt = str(record)[:100] + "..."
                    print(f"{idx}. ID: {record.get('id', 'unknown')} - {record_excerpt}")
            else:
                print("⚠️ No records found or couldn't read from database")
        
        except Exception as e:
            print(f"❌ Error during database operation: {str(e)}")
    else:
        print("❌ Supabase client is NOT initialized")
        print("\nPossible reasons:")
        print("1. The supabase Python package is not installed")
        print("2. The SUPABASE_KEY or SUPABASE_SERVICE_KEY environment variable is not set")
        print("3. The URL or key format is incorrect")
        
        # Check environment variables
        supabase_key = os.environ.get("SUPABASE_KEY")
        supabase_service_key = os.environ.get("SUPABASE_SERVICE_KEY")
        supabase_url = os.environ.get("SUPABASE_URL")
        
        print("\nEnvironment variables status:")
        print(f"SUPABASE_URL: {'✅ Set' if supabase_url else '❌ Not set'}")
        print(f"SUPABASE_KEY: {'✅ Set' if supabase_key else '❌ Not set'}")
        print(f"SUPABASE_SERVICE_KEY: {'✅ Set' if supabase_service_key else '❌ Not set'}")
        
        if supabase_service_key:
            print(f"\nSUPABASE_SERVICE_KEY format check:")
            if len(supabase_service_key) >= 20 and supabase_service_key.startswith("ey"):
                print("✅ Key format looks correct (starts with 'ey' and is 20+ characters)")
            else:
                print("❌ Key format may be incorrect")
                
    print("\n===== TEST COMPLETE =====")

if __name__ == "__main__":
    test_database_connection()
