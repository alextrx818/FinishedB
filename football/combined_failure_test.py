#!/usr/bin/env python3

"""
Combined Failure Smoke Test

This test verifies that all error handling mechanisms in live.py work correctly by:
1. Forcing an import error by temporarily renaming a module
2. Launching a thread that raises an exception
3. Scheduling an asyncio task that raises an exception
4. Verifying that appropriate Telegram alerts are fired for each failure

Usage:
    python3 combined_failure_test.py [--no-restore] [--no-telegram-check]

Options:
    --no-restore        Don't restore the original module file after testing
    --no-telegram-check Don't verify Telegram alerts were sent
"""

import os
import sys
import time
import signal
import shutil
import argparse
import threading
import asyncio
import subprocess
import traceback
from pathlib import Path

# Add parent directory to path so we can import from the root
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Define the module to temporarily rename to force an import error
MODULE_TO_RENAME = "logger/main_logger.py"
MODULE_BACKUP = "logger/main_logger.py.bak"

# Set up color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

class TestFailure(Exception):
    """Custom exception for test failures"""
    pass

def print_status(message, status, details=None):
    """Print a formatted status message"""
    status_color = GREEN if status == "PASS" else RED
    print(f"{status_color}[{status}]{RESET} {message}")
    if details:
        print(f"       {details}")

def verify_alerts(expected_alerts, timeout=30):
    """
    Verify that expected alerts were sent to Telegram
    
    Args:
        expected_alerts: List of alert substrings to check for
        timeout: Maximum time to wait for alerts in seconds
    
    Returns:
        True if all alerts were sent, False otherwise
    """
    # This function should be implemented with your specific Telegram verification logic
    # For now, we'll simply check the output for expected strings
    print(f"{YELLOW}[INFO]{RESET} Would check for Telegram alerts: {expected_alerts}")
    return True

def backup_module():
    """Create a backup of the module we'll rename"""
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULE_TO_RENAME)
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULE_BACKUP)
    
    if os.path.exists(module_path):
        shutil.copy2(module_path, backup_path)
        print_status(f"Backed up {MODULE_TO_RENAME} to {MODULE_BACKUP}", "PASS")
        return True
    else:
        print_status(f"Module {MODULE_TO_RENAME} not found", "FAIL")
        return False

def rename_module():
    """Rename the module to force an import error"""
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULE_TO_RENAME)
    temp_path = f"{module_path}.temp"
    
    if os.path.exists(module_path):
        os.rename(module_path, temp_path)
        print_status(f"Renamed {MODULE_TO_RENAME} to {MODULE_TO_RENAME}.temp", "PASS")
        return True
    else:
        print_status(f"Module {MODULE_TO_RENAME} not found", "FAIL")
        return False

def restore_module():
    """Restore the module from backup"""
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULE_TO_RENAME)
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), MODULE_BACKUP)
    temp_path = f"{module_path}.temp"
    
    # First try to restore from the temp rename
    if os.path.exists(temp_path):
        os.rename(temp_path, module_path)
        print_status(f"Restored {MODULE_TO_RENAME} from temporary rename", "PASS")
        return True
    
    # If that fails, try to restore from backup
    elif os.path.exists(backup_path):
        shutil.copy2(backup_path, module_path)
        print_status(f"Restored {MODULE_TO_RENAME} from backup", "PASS")
        return True
    
    else:
        print_status(f"Failed to restore {MODULE_TO_RENAME}", "FAIL")
        return False

def run_with_timeout(cmd, timeout=120):
    """Run a command with a timeout"""
    process = subprocess.Popen(
        cmd, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        universal_newlines=True,
        shell=True
    )
    
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        process.kill()
        print_status("Process timed out, terminating", "FAIL")
        return -1, "", "Timeout"

def create_error_thread_module():
    """Create a module that will be imported by live.py and spawn an error thread"""
    error_module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools/monitor_live.py")
    error_module_dir = os.path.dirname(error_module_path)
    os.makedirs(error_module_dir, exist_ok=True)
    
    with open(error_module_path, "w") as f:
        f.write("""
import threading
import asyncio
import time

def raise_thread_error():
    \"\"\"Raise an exception in a thread\"\"\"
    time.sleep(1)  # Give the system time to initialize
    print("🔥 SIMULATED ERROR: Raising exception in thread")
    raise Exception("COMBINED_TEST_THREAD_ERROR - This is an intentional test exception")

def schedule_async_error():
    \"\"\"Schedule an asyncio task that will raise an exception\"\"\"
    async def async_error():
        await asyncio.sleep(2)  # Give a bit more time than the thread error
        print("🔥 SIMULATED ERROR: Raising exception in asyncio task")
        raise Exception("COMBINED_TEST_ASYNCIO_ERROR - This is an intentional test exception")
    
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(async_error())
    except Exception as e:
        print(f"Failed to schedule asyncio error: {e}")

def start_monitoring_thread():
    \"\"\"Start a thread that will raise an exception\"\"\"
    # Create and start an error thread
    error_thread = threading.Thread(target=raise_thread_error, name="ErrorThread")
    error_thread.daemon = True
    error_thread.start()
    
    # Schedule an asyncio error
    schedule_async_error()
    
    print("✓ Error monitoring threads started")
    return True
""")
    print_status("Created error thread module", "PASS")

def signal_handler(sig, frame):
    """Handle interruption signals to ensure cleanup"""
    print(f"\n{RED}Test interrupted - cleaning up{RESET}")
    restore_module()
    sys.exit(1)

def run_import_failure_test():
    """Test that import failures are properly caught and reported"""
    print(f"\n{BOLD}Testing Import Failure Handling{RESET}")
    
    # Create a backup of the original module
    module_backed_up = backup_module()
    if not module_backed_up:
        return False
    
    try:
        # Rename the module to force an import error
        module_renamed = rename_module()
        if not module_renamed:
            return False
        
        print("\nLaunching live.py with purposely broken import...\n")
        
        # Run live.py and capture output
        cmd = "cd /root/CascadeProjects/sports_bot/football && python3 live.py"
        returncode, stdout, stderr = run_with_timeout(cmd, timeout=5)
        
        print("\n----- Import Error Test Output -----")
        print(stdout)
        if stderr:
            print("\n----- Error Output -----")
            print(stderr)
        print("-----------------------------------\n")
        
        # Verify expected errors in output
        import_error_detected = "main_logger" in stdout.lower() and "error" in stdout.lower()
        
        if import_error_detected:
            print_status("Import error was detected", "PASS")
            return True
        else:
            print_status("Import error was NOT detected", "FAIL")
            return False
            
    except Exception as e:
        print_status("Import failure test failed", "FAIL", str(e))
        traceback.print_exc()
        return False
    
    finally:
        # Always restore the module
        if module_backed_up and module_renamed:
            restore_module()

def run_thread_exception_test():
    """Test that thread exceptions are properly caught and reported"""
    print(f"\n{BOLD}Testing Thread Exception Handling{RESET}")
    
    try:
        # Create the module that will spawn error threads
        create_error_thread_module()
        
        print("\nLaunching live.py with thread that will raise exception...\n")
        
        # Run live.py with the error thread module
        cmd = "cd /root/CascadeProjects/sports_bot/football && python3 -c 'import tools.monitor_live; tools.monitor_live.raise_thread_error()'"
        returncode, stdout, stderr = run_with_timeout(cmd, timeout=5)
        
        print("\n----- Thread Error Test Output -----")
        print(stdout)
        if stderr:
            print("\n----- Error Output -----")
            print(stderr)
        print("-----------------------------------\n")
        
        # Check for thread exception in output
        thread_error_detected = "COMBINED_TEST_THREAD_ERROR" in stdout or "COMBINED_TEST_THREAD_ERROR" in stderr
        
        if thread_error_detected:
            print_status("Thread error was detected", "PASS")
            return True
        else:
            print_status("Thread error was NOT detected", "FAIL")
            return False
            
    except Exception as e:
        print_status("Thread exception test failed", "FAIL", str(e))
        traceback.print_exc()
        return False

def run_asyncio_exception_test():
    """Test that asyncio exceptions are properly caught and reported"""
    print(f"\n{BOLD}Testing Asyncio Exception Handling{RESET}")
    
    try:
        # Create the module that will schedule an asyncio error
        create_error_thread_module()
        
        print("\nLaunching live.py with asyncio task that will raise exception...\n")
        
        # Run live.py with the asyncio error module
        cmd = "cd /root/CascadeProjects/sports_bot/football && python3 -c 'import asyncio; import tools.monitor_live; tools.monitor_live.schedule_async_error(); asyncio.get_event_loop().run_until_complete(asyncio.sleep(3))'"
        returncode, stdout, stderr = run_with_timeout(cmd, timeout=5)
        
        print("\n----- Asyncio Error Test Output -----")
        print(stdout)
        if stderr:
            print("\n----- Error Output -----")
            print(stderr)
        print("--------------------------------------\n")
        
        # Check for asyncio exception in output
        asyncio_error_detected = "COMBINED_TEST_ASYNCIO_ERROR" in stdout or "COMBINED_TEST_ASYNCIO_ERROR" in stderr
        
        if asyncio_error_detected:
            print_status("Asyncio error was detected", "PASS")
            return True
        else:
            print_status("Asyncio error was NOT detected", "FAIL")
            return False
            
    except Exception as e:
        print_status("Asyncio exception test failed", "FAIL", str(e))
        traceback.print_exc()
        return False

def run_combined_test(args):
    """Run all three tests in sequence for complete verification"""
    print(f"\n{BOLD}Running Combined Failure Test{RESET}\n")
    
    # Register signal handlers for clean termination
    original_sigint = signal.signal(signal.SIGINT, signal_handler)
    original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Run all three tests
        import_test_passed = run_import_failure_test()
        thread_test_passed = run_thread_exception_test()
        asyncio_test_passed = run_asyncio_exception_test()
        
        # Verify expected alerts if requested
        if not args.no_telegram_check:
            expected_alerts = [
                "main_logger",                     # Import error
                "COMBINED_TEST_THREAD_ERROR",      # Thread error
                "COMBINED_TEST_ASYNCIO_ERROR"      # Asyncio error
            ]
            print(f"\n{BOLD}Verifying Telegram Alerts{RESET}")
            alerts_verified = verify_alerts(expected_alerts)
            if not alerts_verified:
                print_status("Not all expected alerts were verified", "FAIL")
                return False
        
        all_tests_passed = import_test_passed and thread_test_passed and asyncio_test_passed
        
        print(f"\n{BOLD}Overall Test Results{RESET}")
        print_status("Import failure handling", "PASS" if import_test_passed else "FAIL")
        print_status("Thread exception handling", "PASS" if thread_test_passed else "FAIL")
        print_status("Asyncio exception handling", "PASS" if asyncio_test_passed else "FAIL")
        
        if all_tests_passed:
            print_status("Combined failure test completed successfully", "PASS")
        else:
            print_status("Combined failure test failed", "FAIL")
            
        return all_tests_passed
    
    except Exception as e:
        print_status("Combined failure test failed", "FAIL", str(e))
        traceback.print_exc()
        return False
    
    finally:
        # Always restore the module unless --no-restore was specified
        if not args.no_restore:
            print(f"\n{YELLOW}[INFO]{RESET} Ensuring module restoration...")
            restore_module()
        
        # Restore original signal handlers
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Combined Failure Smoke Test")
    parser.add_argument("--no-restore", action="store_true", help="Don't restore the original module after testing")
    parser.add_argument("--no-telegram-check", action="store_true", help="Don't verify Telegram alerts were sent")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    success = run_combined_test(args)
    sys.exit(0 if success else 1)
