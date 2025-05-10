#!/usr/bin/env python3
"""
Test the database statistics summary functionality
"""
import os
import sys
from pprint import pprint

# Import our database modules
sys.path.append('/root/CascadeProjects/sports_bot')
from football.logger.db_api import archive_match_json, get_db_stats_summary

# Create some test match data
test_matches = [
    {"id": "test1", "match_name": "Test Match 1", "data": "sample data 1"},
    {"id": "test2", "match_name": "Test Match 2", "data": "sample data 2"},
    {"id": "test3", "match_name": "Test Match 3", "data": "sample data 3"},
]

print("="*60)
print("DATABASE STATISTICS TEST")
print("="*60)

# Archive each test match
for match in test_matches:
    print(f"Archiving match: {match['id']}")
    success = archive_match_json(match)
    print(f"Result: {'Success' if success else 'Failed'}")
    print()

# Get the summary
print("="*60)
print("DATABASE STATISTICS SUMMARY")
print("="*60)
summary = get_db_stats_summary()
print(summary)
