#!/usr/bin/env python3
import json
from pathlib import Path

def check_for_unknown_values(file_path):
    """Check if there are any 'Unknown' values in the output file."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    unknown_teams = 0
    unknown_comps = 0
    unknown_countries = 0
    total_records = len(data)
    
    print(f"Examining {total_records} records in {file_path}")
    
    # Print the first 3 records to verify enrichment
    print("\nSample of first 3 records:")
    for i, record in enumerate(data[:3]):
        print(f"\nRecord {i+1}:")
        print(f"  home_team: {record.get('home_team')}")
        print(f"  away_team: {record.get('away_team')}")
        print(f"  competition: {record.get('competition')}")
        print(f"  country: {record.get('country')}")
    
    # Count unknown values
    for record in data:
        if record.get('home_team') == 'Unknown Team' or record.get('away_team') == 'Unknown Team':
            unknown_teams += 1
        if record.get('competition') == 'Unknown Competition':
            unknown_comps += 1
        if record.get('country') == 'Unknown Country':
            unknown_countries += 1
    
    print(f"\nAnalysis results:")
    print(f"  Unknown teams: {unknown_teams}")
    print(f"  Unknown competitions: {unknown_comps}")
    print(f"  Unknown countries: {unknown_countries}")
    
    if unknown_teams == 0 and unknown_comps == 0 and unknown_countries == 0:
        print("\nSUCCESS: All records have been properly enriched!")
    else:
        print("\nWARNING: Some records still have unknown values.")

if __name__ == "__main__":
    output_file = Path(__file__).parent / "merge_logic.json"
    check_for_unknown_values(output_file)
