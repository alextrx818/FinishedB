#!/usr/bin/env python3
"""
API Connectivity Diagnostic Tests

This module tests the Sports Bot's API connections to ensure they function correctly
and meet established standards.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '../../..'))
sys.path.append(project_root)

# Import TestResult from main diagnostics
sys.path.append(os.path.join(project_root, 'tools', 'diagnostics'))
try:
    from diagnostics import TestResult
except ImportError:
    # Fallback definition if main script is not available
    class TestResult:
        def __init__(self, name, passed, message="", details=None):
            self.name = name
            self.passed = passed
            self.message = message
            self.details = details or {}
            self.timestamp = datetime.now()

# Extract API credentials from live.py
def extract_api_credentials():
    """Extract API credentials from live.py file"""
    try:
        live_py_path = os.path.join(project_root, 'football', 'live.py')
        user = None
        secret = None
        
        with open(live_py_path, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                if 'USER =' in line:
                    user_line = line.strip()
                    user = user_line.split('=')[1].strip().strip('"\'')
                elif 'SECRET =' in line:
                    secret_line = line.strip()
                    secret = secret_line.split('=')[1].strip().strip('"\'')
                
                if user and secret:
                    break
        
        return user, secret
    except Exception as e:
        print(f"Error extracting API credentials: {e}")
        return None, None

# Test API endpoint with retries
def test_api_endpoint(endpoint, params=None, max_retries=2, expected_keys=None):
    """Test an API endpoint with retry logic"""
    user, secret = extract_api_credentials()
    if not user or not secret:
        return TestResult(
            name=f"api_credentials",
            passed=False,
            message="Failed to extract API credentials from live.py"
        )
    
    # Base parameters with authentication
    base_params = {
        "user": user,
        "secret": secret
    }
    
    # Merge with additional parameters if provided
    if params:
        base_params.update(params)
    
    # Attempt API request with retries
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(
                f"https://api.thesports.com/v1/football/{endpoint}",
                params=base_params,
                timeout=10
            )
            
            # Check HTTP status
            if response.status_code != 200:
                if attempt < max_retries:
                    time.sleep(1)  # Simple backoff
                    continue
                return TestResult(
                    name=f"api_{endpoint}",
                    passed=False,
                    message=f"API returned HTTP {response.status_code}",
                    details={"status_code": response.status_code, "response": response.text[:200]}
                )
            
            # Parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                return TestResult(
                    name=f"api_{endpoint}",
                    passed=False,
                    message="API returned invalid JSON",
                    details={"response": response.text[:200]}
                )
            
            # Check response code
            if data.get("code") != 0:
                return TestResult(
                    name=f"api_{endpoint}",
                    passed=False,
                    message=f"API returned error code {data.get('code')}",
                    details={"response": data}
                )
            
            # Check for expected keys
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in data]
                if missing_keys:
                    return TestResult(
                        name=f"api_{endpoint}",
                        passed=False,
                        message=f"API response missing expected keys: {', '.join(missing_keys)}",
                        details={"response": data, "missing_keys": missing_keys}
                    )
            
            # All checks passed
            return TestResult(
                name=f"api_{endpoint}",
                passed=True,
                message="API endpoint is functioning correctly",
                details={"sample_keys": list(data.keys())[:5]}
            )
            
        except requests.RequestException as e:
            if attempt < max_retries:
                time.sleep(1)  # Simple backoff
                continue
            return TestResult(
                name=f"api_{endpoint}",
                passed=False,
                message=f"API request failed: {str(e)}",
                details={"error": str(e)}
            )
    
    # Should never reach here
    return TestResult(
        name=f"api_{endpoint}",
        passed=False,
        message="API test failed after retries",
    )

def run_tests(verbose=False):
    """Run all API tests and return results"""
    if verbose:
        print("Running API connectivity tests...")
    
    results = []
    
    # Test 1: Check API credentials
    user, secret = extract_api_credentials()
    if user and secret:
        results.append(TestResult(
            name="api_credentials",
            passed=True,
            message="API credentials found in live.py",
            details={"user": user[:3] + "..." if user else None}
        ))
    else:
        results.append(TestResult(
            name="api_credentials",
            passed=False,
            message="Failed to extract API credentials from live.py"
        ))
        # No point continuing if we don't have credentials
        return results
    
    # Test 2: Country list API test
    country_result = test_api_endpoint(
        "country/list",
        expected_keys=["code", "results"]
    )
    results.append(country_result)
    
    # Test 3: Live matches API test
    live_result = test_api_endpoint(
        "match/detail_live",
        expected_keys=["code", "results"]
    )
    results.append(live_result)
    
    # Test 4: Match details API test
    match_details_result = test_api_endpoint(
        "match/recent/list",
        params={"uuid": "sample_match_id"},  # Placeholder ID
        expected_keys=["code"]
    )
    results.append(match_details_result)
    
    # Test 5: Odds history API test
    odds_result = test_api_endpoint(
        "odds/history",
        params={"uuid": "sample_match_id"},  # Placeholder ID
        expected_keys=["code"]
    )
    results.append(odds_result)
    
    if verbose:
        print(f"API tests completed - {sum(1 for r in results if r.passed)}/{len(results)} passed")
    
    return results

if __name__ == "__main__":
    # Run tests directly when script is executed
    print("Running API tests standalone mode...")
    results = run_tests(verbose=True)
    
    # Display results
    print("\nTest Results:")
    for result in results:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"{status} - {result.name}: {result.message}")
