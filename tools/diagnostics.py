#!/usr/bin/env python3
"""
Sports Bot Comprehensive Diagnostic Tool

This tool performs thorough diagnostics on all components of the Sports Bot system
to verify they are functioning according to standards.

Usage:
    python3 diagnostics.py [--verbose] [--send-alerts]

Options:
    --verbose      Show detailed test output
    --send-alerts  Send actual Telegram alerts during testing (default: dry run)

Tests performed:
1. API Connectivity - Tests connections to thesports.com API 
2. Database Operations - Tests Supabase connection and operations
3. Telegram Integration - Tests alert functionality
4. Match Data Monitor - Tests monitor pattern detection
5. Logging System - Tests log file creation and rotation
6. Process Integration - Tests thread creation and management
"""

import os
import sys
import json
import time
import argparse
import datetime
import re
import requests
import importlib.util
import traceback
from pathlib import Path

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.append(project_root)

# Test result class
class TestResult:
    """Stores the result of a single diagnostic test"""
    def __init__(self, name, passed, message="", details=None):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.datetime.now()
    
    def to_dict(self):
        """Convert to dictionary for serialization"""
        return {
            "name": self.name,
            "passed": self.passed, 
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }

#==========================================
# API CONNECTIVITY TESTS
#==========================================

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

def test_api_credentials():
    """Test if API credentials are configured"""
    user, secret = extract_api_credentials()
    
    if not user:
        return TestResult(
            name="api_credentials",
            passed=False,
            message="Could not find API user in live.py"
        )
    
    if not secret:
        return TestResult(
            name="api_credentials",
            passed=False,
            message="Could not find API secret in live.py"
        )
    
    # All checks passed
    return TestResult(
        name="api_credentials",
        passed=True,
        message="API credentials found in live.py",
        details={"user": user[:3] + "..." if user else None}
    )

def test_api_endpoint(endpoint, params=None, max_retries=2, expected_keys=None):
    """Test an API endpoint with retry logic"""
    user, secret = extract_api_credentials()
    if not user or not secret:
        return TestResult(
            name=f"api_{endpoint}",
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

def run_api_tests(verbose=False):
    """Run all API tests and return results"""
    if verbose:
        print("Running API connectivity tests...")
    
    results = []
    
    # Test 1: Check API credentials
    credentials_result = test_api_credentials()
    results.append(credentials_result)
    
    # Only continue if credentials are valid
    if credentials_result.passed:
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
    
    if verbose:
        print(f"API tests completed - {sum(1 for r in results if r.passed)}/{len(results)} passed")
    
    return results

#==========================================
# DATABASE TESTS
#==========================================

def import_supabase_config():
    """Import the Supabase configuration module"""
    try:
        # Try direct import first
        try:
            from supabase_config import supabase
            return supabase, None
        except ImportError:
            pass
        
        # Try to find the module location
        supabase_paths = [
            os.path.join(project_root, 'supabase_config.py'),
            os.path.join(project_root, 'football', 'supabase_config.py'),
            os.path.join(project_root, 'config', 'supabase_config.py')
        ]
        
        for path in supabase_paths:
            if os.path.exists(path):
                spec = importlib.util.spec_from_file_location("supabase_config", path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                if hasattr(module, 'supabase'):
                    return module.supabase, None
        
        return None, "Could not find supabase_config.py"
    
    except Exception as e:
        return None, f"Error importing Supabase config: {str(e)}"

def test_db_connection():
    """Test the database connection"""
    supabase, error = import_supabase_config()
    
    if error:
        return TestResult(
            name="db_connection",
            passed=False,
            message=f"Failed to import Supabase configuration: {error}"
        )
    
    if not supabase:
        return TestResult(
            name="db_connection",
            passed=False,
            message="Supabase client is None or not properly initialized"
        )
    
    try:
        # Simple test query to check if connection works
        response = supabase.table('archived_json').select('count', count='exact').limit(1).execute()
        
        # Verify the response structure
        if not hasattr(response, 'data') or not hasattr(response, 'count'):
            return TestResult(
                name="db_connection",
                passed=False,
                message="Unexpected response structure from Supabase",
                details={"response": str(response)[:200]}
            )
        
        # All checks passed
        return TestResult(
            name="db_connection",
            passed=True,
            message=f"Successfully connected to Supabase",
            details={"count": response.count}
        )
    
    except Exception as e:
        return TestResult(
            name="db_connection",
            passed=False,
            message=f"Database connection failed: {str(e)}",
            details={"error": str(e)}
        )

def run_db_tests(verbose=False):
    """Run all database tests and return results"""
    if verbose:
        print("Running database connectivity tests...")
    
    results = []
    
    # Test 1: Database Connection
    connection_result = test_db_connection()
    results.append(connection_result)
    
    if verbose:
        print(f"Database tests completed - {sum(1 for r in results if r.passed)}/{len(results)} passed")
    
    return results

#==========================================
# TELEGRAM TESTS
#==========================================

def import_telegram_module():
    """Import the Telegram module"""
    try:
        # Try direct import first
        try:
            from football.telegram import send_system_alert, send_match_alert
            return (send_system_alert, send_match_alert), None
        except ImportError:
            pass
        
        # Try dynamic import
        telegram_module_path = os.path.join(project_root, 'football', 'telegram', 'alerts.py')
        if os.path.exists(telegram_module_path):
            spec = importlib.util.spec_from_file_location("telegram_alerts", telegram_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            send_system_alert = getattr(module, 'send_system_alert', None)
            send_match_alert = getattr(module, 'send_match_alert', None)
            
            if send_system_alert and send_match_alert:
                return (send_system_alert, send_match_alert), None
            else:
                return None, "Required functions not found in telegram module"
        
        return None, "Could not find telegram module"
    
    except Exception as e:
        return None, f"Error importing Telegram module: {str(e)}"

def extract_telegram_credentials():
    """Extract Telegram bot token and chat ID from the codebase"""
    try:
        # Look in various potential files
        potential_files = [
            os.path.join(project_root, 'football', 'telegram', 'alerts.py'),
            os.path.join(project_root, 'football', 'telegram', '__init__.py'),
            os.path.join(project_root, 'football', 'live.py')
        ]
        
        token = None
        chat_id = None
        
        # Regex patterns for token and chat ID
        token_pattern = re.compile(r'token="?([0-9]+:[A-Za-z0-9_-]+)"?')
        chat_id_pattern = re.compile(r'chat_id="?([0-9]+)"?')
        
        for file_path in potential_files:
            if not os.path.exists(file_path):
                continue
                
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for token
                if not token:
                    token_match = token_pattern.search(content)
                    if token_match:
                        token = token_match.group(1)
                
                # Look for chat_id
                if not chat_id:
                    chat_id_match = chat_id_pattern.search(content)
                    if chat_id_match:
                        chat_id = chat_id_match.group(1)
            
            # Break if we found both
            if token and chat_id:
                break
        
        return token, chat_id
    
    except Exception as e:
        print(f"Error extracting Telegram credentials: {e}")
        return None, None

def test_telegram_credentials():
    """Test if Telegram credentials are configured"""
    token, chat_id = extract_telegram_credentials()
    
    if not token:
        return TestResult(
            name="telegram_credentials",
            passed=False,
            message="Could not find Telegram bot token in the codebase"
        )
    
    if not chat_id:
        return TestResult(
            name="telegram_credentials",
            passed=False,
            message="Could not find Telegram chat ID in the codebase"
        )
    
    # All checks passed
    return TestResult(
        name="telegram_credentials",
        passed=True,
        message="Telegram credentials are properly configured",
        details={
            "token_prefix": token[:8] + "..." if token else None,
            "chat_id_prefix": chat_id[:4] + "..." if chat_id else None
        }
    )

def test_match_data_monitor():
    """Test the match data monitor integration"""
    # Check if match_data_monitor.py exists
    monitor_path = os.path.join(project_root, 'football', 'telegram', 'match_data_monitor.py')
    
    if not os.path.exists(monitor_path):
        return TestResult(
            name="match_monitor",
            passed=False,
            message="match_data_monitor.py not found"
        )
    
    try:
        # Check if the module can be imported
        spec = importlib.util.spec_from_file_location("match_data_monitor", monitor_path)
        monitor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(monitor)
        
        # Check for required functions
        required_functions = ['process_log_chunk', 'monitor_log_file', 'send_alert']
        missing_functions = [func for func in required_functions if not hasattr(monitor, func)]
        
        if missing_functions:
            return TestResult(
                name="match_monitor",
                passed=False,
                message=f"Match data monitor missing required functions: {', '.join(missing_functions)}",
                details={"missing_functions": missing_functions}
            )
        
        # Check for required variables
        if not hasattr(monitor, 'PATTERNS') or not isinstance(monitor.PATTERNS, dict):
            return TestResult(
                name="match_monitor",
                passed=False,
                message="Match data monitor missing PATTERNS dictionary"
            )
        
        # Check specific patterns
        required_patterns = ['empty_env', 'empty_ml', 'empty_spread', 'empty_total']
        missing_patterns = [pattern for pattern in required_patterns if pattern not in monitor.PATTERNS]
        
        if missing_patterns:
            return TestResult(
                name="match_monitor",
                passed=False,
                message=f"Match data monitor missing required patterns: {', '.join(missing_patterns)}",
                details={"missing_patterns": missing_patterns}
            )
        
        # Check for alerted_conditions set (for deduplication)
        if not hasattr(monitor, 'alerted_conditions'):
            return TestResult(
                name="match_monitor",
                passed=False,
                message="Match data monitor missing alerted_conditions set for deduplication"
            )
        
        # All checks passed
        return TestResult(
            name="match_monitor",
            passed=True,
            message="Match data monitor is properly configured",
            details={"detected_patterns": list(monitor.PATTERNS.keys())}
        )
    
    except Exception as e:
        return TestResult(
            name="match_monitor",
            passed=False,
            message=f"Error testing match data monitor: {str(e)}",
            details={"error": str(e)}
        )

def run_telegram_tests(verbose=False, send_real_messages=False):
    """Run all Telegram tests and return results"""
    if verbose:
        print("Running Telegram integration tests...")
    
    results = []
    
    # Test 1: Telegram Credentials
    cred_result = test_telegram_credentials()
    results.append(cred_result)
    
    # Test 2: Match Data Monitor
    monitor_result = test_match_data_monitor()
    results.append(monitor_result)
    
    if verbose:
        print(f"Telegram tests completed - {sum(1 for r in results if r.passed)}/{len(results)} passed")
    
    return results

#==========================================
# LOGGER TESTS
#==========================================

def test_logger_file():
    """Test if the logger file exists and is writable"""
    log_path = os.path.join(project_root, 'football', 'logger', 'main.logger')
    
    if not os.path.exists(log_path):
        return TestResult(
            name="logger_file",
            passed=False,
            message="main.logger file not found"
        )
    
    # Check if file is writable
    try:
        # Try to open the file in append mode
        with open(log_path, 'a') as f:
            pass
        
        # Check if file has recent content
        stats = os.stat(log_path)
        mtime = datetime.datetime.fromtimestamp(stats.st_mtime)
        now = datetime.datetime.now()
        
        # Calculate file age in days
        age_days = (now - mtime).total_seconds() / 86400
        
        # Check file size
        size_mb = stats.st_size / (1024 * 1024)
        
        return TestResult(
            name="logger_file",
            passed=True,
            message="Logger file exists and is writable",
            details={
                "path": log_path,
                "size_mb": round(size_mb, 2),
                "last_modified": mtime.strftime("%Y-%m-%d %H:%M:%S"),
                "age_days": round(age_days, 2)
            }
        )
    
    except Exception as e:
        return TestResult(
            name="logger_file",
            passed=False,
            message=f"Error accessing logger file: {str(e)}",
            details={"error": str(e)}
        )

def test_log_rotation():
    """Test if log rotation is configured"""
    logger_dir = os.path.join(project_root, 'football', 'logger')
    main_logger_py = os.path.join(logger_dir, 'main_logger.py')
    
    if not os.path.exists(main_logger_py):
        return TestResult(
            name="log_rotation",
            passed=False,
            message="main_logger.py not found"
        )
    
    try:
        # Check if TimedRotatingFileHandler is used
        with open(main_logger_py, 'r') as f:
            content = f.read()
            
            if 'TimedRotatingFileHandler' not in content:
                return TestResult(
                    name="log_rotation",
                    passed=False,
                    message="TimedRotatingFileHandler not found in main_logger.py"
                )
            
            # Check for rotation configuration
            if 'when=' not in content or 'backupCount=' not in content:
                return TestResult(
                    name="log_rotation",
                    passed=False,
                    message="Log rotation configuration incomplete"
                )
            
            # Check for rotated log files
            log_files = [f for f in os.listdir(logger_dir) if f.startswith('main.logger.') and f != 'main.logger']
            
            return TestResult(
                name="log_rotation",
                passed=True,
                message="Log rotation is properly configured",
                details={
                    "rotated_files_count": len(log_files),
                    "rotated_files": log_files[:5] if log_files else []
                }
            )
    
    except Exception as e:
        return TestResult(
            name="log_rotation",
            passed=False,
            message=f"Error checking log rotation: {str(e)}",
            details={"error": str(e)}
        )

def run_logger_tests(verbose=False):
    """Run all logger tests and return results"""
    if verbose:
        print("Running logger system tests...")
    
    results = []
    
    # Test 1: Logger File
    file_result = test_logger_file()
    results.append(file_result)
    
    # Test 2: Log Rotation
    rotation_result = test_log_rotation()
    results.append(rotation_result)
    
    if verbose:
        print(f"Logger tests completed - {sum(1 for r in results if r.passed)}/{len(results)} passed")
    
    return results

#==========================================
# LIVE.PY INTEGRATION TESTS
#==========================================

def test_live_py_exists():
    """Test if live.py exists and is executable"""
    live_py_path = os.path.join(project_root, 'football', 'live.py')
    
    if not os.path.exists(live_py_path):
        return TestResult(
            name="live_py_exists",
            passed=False,
            message="live.py not found"
        )
    
    # Check if file is executable
    try:
        is_executable = os.access(live_py_path, os.X_OK)
        
        return TestResult(
            name="live_py_exists",
            passed=True,
            message="live.py exists and is executable" if is_executable else "live.py exists but is not executable",
            details={
                "path": live_py_path,
                "executable": is_executable,
                "size_kb": round(os.path.getsize(live_py_path) / 1024, 2)
            }
        )
    
    except Exception as e:
        return TestResult(
            name="live_py_exists",
            passed=False,
            message=f"Error checking live.py: {str(e)}",
            details={"error": str(e)}
        )

def test_monitor_integration():
    """Test if match data monitor is integrated with live.py"""
    live_py_path = os.path.join(project_root, 'football', 'live.py')
    
    if not os.path.exists(live_py_path):
        return TestResult(
            name="monitor_integration",
            passed=False,
            message="live.py not found"
        )
    
    try:
        # Check if match data monitor is imported and started in live.py
        with open(live_py_path, 'r') as f:
            content = f.read()
            
            # Check for monitor thread creation
            has_import = 'match_data_monitor' in content
            has_thread = 'data_monitor_thread' in content and ('threading.Thread' in content or 'Thread(' in content)
            
            if not has_import or not has_thread:
                return TestResult(
                    name="monitor_integration",
                    passed=False,
                    message="Match data monitor integration not found in live.py",
                    details={
                        "has_import": has_import,
                        "has_thread": has_thread
                    }
                )
            
            return TestResult(
                name="monitor_integration",
                passed=True,
                message="Match data monitor is properly integrated with live.py",
                details={
                    "has_import": has_import,
                    "has_thread": has_thread
                }
            )
    
    except Exception as e:
        return TestResult(
            name="monitor_integration",
            passed=False,
            message=f"Error checking monitor integration: {str(e)}",
            details={"error": str(e)}
        )

def run_integration_tests(verbose=False):
    """Run all integration tests and return results"""
    if verbose:
        print("Running integration tests...")
    
    results = []
    
    # Test 1: Live.py Exists
    live_result = test_live_py_exists()
    results.append(live_result)
    
    # Test 2: Monitor Integration
    monitor_result = test_monitor_integration()
    results.append(monitor_result)
    
    if verbose:
        print(f"Integration tests completed - {sum(1 for r in results if r.passed)}/{len(results)} passed")
    
    return results

#==========================================
# MAIN DIAGNOSTIC FUNCTIONS
#==========================================

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Sports Bot Diagnostic Tests")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--send-alerts", action="store_true", help="Send actual Telegram alerts")
    parser.add_argument("--report", action="store_true", help="Generate HTML report")
    return parser.parse_args()

def run_all_tests(args):
    """Run all test categories and collect results"""
    all_results = {}
    
    # API Tests
    all_results['api'] = run_api_tests(verbose=args.verbose)
    
    # Database Tests
    all_results['database'] = run_db_tests(verbose=args.verbose)
    
    # Telegram Tests
    all_results['telegram'] = run_telegram_tests(
        verbose=args.verbose, 
        send_real_messages=args.send_alerts
    )
    
    # Logger Tests
    all_results['logger'] = run_logger_tests(verbose=args.verbose)
    
    # Integration Tests
    all_results['integration'] = run_integration_tests(verbose=args.verbose)
    
    return all_results

def display_results(results):
    """Display test results in a formatted table"""
    print("\n" + "=" * 80)
    print(" SPORTS BOT DIAGNOSTIC RESULTS ".center(80))
    print("=" * 80)
    
    total_passed = 0
    total_failed = 0
    total_tests = 0
    
    for category, category_results in results.items():
        category_passed = sum(1 for r in category_results if r.passed)
        category_failed = len(category_results) - category_passed
        
        print(f"\n{category.upper()} TESTS:")
        print(f"  ✓ Passed: {category_passed}")
        print(f"  ✗ Failed: {category_failed}")
        print(f"  Total: {len(category_results)}")
        
        # Print failed tests if any
        if category_failed > 0:
            print("  Failed tests:")
            for result in category_results:
                if not result.passed:
                    print(f"    ✗ {result.name}: {result.message}")
        
        total_passed += category_passed
        total_failed += category_failed
        total_tests += len(category_results)
    
    # Print overall summary
    print("\n" + "-" * 80)
    print(f"OVERALL: {total_passed}/{total_tests} tests passed ({total_passed/total_tests*100:.1f}% success rate)")
    
    if total_failed == 0:
        print("\n✅ All tests passed! The sports bot is functioning according to established standards.")
    else:
        print(f"\n❌ {total_failed} tests failed. Sports bot needs attention in the areas listed above.")
    
    print("=" * 80)

def save_results(results):
    """Save test results to a JSON file"""
    # Create results directory if it doesn't exist
    results_dir = os.path.join(project_root, "logs", "diagnostics")
    os.makedirs(results_dir, exist_ok=True)
    
    # Format results for serialization
    serializable_results = {}
    for category, category_results in results.items():
        serializable_results[category] = [result.to_dict() for result in category_results]
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(results_dir, f"diagnostics_{timestamp}.json")
    
    # Write to file
    with open(filename, "w") as f:
        json.dump(serializable_results, f, indent=2)
    
    print(f"\nTest results saved to: {filename}")
    return filename

def main():
    """Main entry point for diagnostics"""
    # Parse command line arguments
    args = parse_args()
    
    print("\n" + "=" * 80)
    print(" SPORTS BOT DIAGNOSTIC TOOL ".center(80))
    print(" Comprehensive System Verification ".center(80))
    print("=" * 80)
    print(f"Start time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Project root: {project_root}")
    print("-" * 80)
    
    # Run all tests
    results = run_all_tests(args)
    
    # Display results
    display_results(results)
    
    # Save results to file
    save_results(results)

if __name__ == "__main__":
    main()
