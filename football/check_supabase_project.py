#!/usr/bin/env python3
"""
Script to extract and display the Supabase project reference ID
"""
import os
import sys

# Get the URL from environment variable
supabase_url = os.environ.get("SUPABASE_URL", "https://pryhbrttsgamlqxvwiap.supabase.co")

# Extract the project reference ID (subdomain part)
project_ref = supabase_url.replace("https://", "").split(".")[0]

print(f"Supabase Project Reference ID: {project_ref}")
print(f"Full Supabase URL: {supabase_url}")
print()
print("When viewing your Supabase dashboard, make sure you're in the correct project.")
print(f"The URL in your browser should contain: {project_ref}")
