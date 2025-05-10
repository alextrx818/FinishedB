#!/usr/bin/env python3
"""
Test Supabase Connection and Tables

This script verifies the Supabase connection and validates if 
the required database tables exist.
"""
import os
import sys
from pprint import pprint

# Import the supabase configuration
from supabase_config import supabase, SERVICE_KEY, SUPABASE_URL

print("="*60)
print("SUPABASE CONNECTION TEST")
print("="*60)

# Check connection
if supabase is None:
    print("❌ ERROR: Supabase client is None")
    print(f"SERVICE_KEY present: {'Yes' if SERVICE_KEY else 'No'}")
    print(f"SUPABASE_URL: {SUPABASE_URL}")
    sys.exit(1)
else:
    print("✅ Supabase client initialized")
    print(f"SERVICE_KEY length: {len(SERVICE_KEY) if SERVICE_KEY else 0}")
    print(f"SUPABASE_URL: {SUPABASE_URL}")

# Test connection by getting database version
print("\n" + "="*60)
print("CHECKING TABLES")
print("="*60)

# Test logs table
print("\nTesting 'logs' table:")
try:
    response = supabase.table("logs").select("id").limit(1).execute()
    print("✅ logs table exists and is accessible")
    print(f"Response: {response}")
except Exception as e:
    print(f"❌ Error accessing logs table: {str(e)}")
    print("SQL to create logs table:")
    print("""
    CREATE TABLE IF NOT EXISTS logs (
      id SERIAL PRIMARY KEY,
      level TEXT,
      msg TEXT,
      time TIMESTAMPTZ
    );
    """)

# Test archived_json table
print("\nTesting 'archived_json' table:")
try:
    response = supabase.table("archived_json").select("id").limit(1).execute()
    print("✅ archived_json table exists and is accessible")
    print(f"Response: {response}")
except Exception as e:
    print(f"❌ Error accessing archived_json table: {str(e)}")
    print("SQL to create archived_json table:")
    print("""
    CREATE TABLE IF NOT EXISTS archived_json (
      id SERIAL PRIMARY KEY, 
      raw_json JSONB, 
      created_at TIMESTAMPTZ DEFAULT NOW()
    );
    """)

# Test inserting data
print("\n" + "="*60)
print("TESTING INSERT OPERATION")
print("="*60)

test_data = {"test_id": "test123", "test_time": "now"}
print(f"\nAttempting to insert test data into archived_json: {test_data}")

try:
    response = supabase.table("archived_json").insert({"raw_json": test_data}).execute()
    print("✅ Successfully inserted test data")
    print(f"Response: {response}")
except Exception as e:
    print(f"❌ Error inserting test data: {str(e)}")

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
