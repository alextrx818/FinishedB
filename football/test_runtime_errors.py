#!/usr/bin/env python3
"""
Test script to verify runtime error handling in live.py

This script temporarily injects errors into live.py to test:
1. Thread exception handling
2. Asyncio task exception handling
3. Multiple simultaneous errors
4. Import errors at the same time as runtime errors

Usage:
    python3 test_runtime_errors.py [test_type]

Where test_type is one of:
    all          - Run all tests (default)
    thread       - Test only thread error handling
    asyncio      - Test only asyncio error handling
    combined     - Test combined errors (thread + asyncio)
    import+thread - Test import failure with thread error

The script will output results of the test and restore live.py to its original state.
"""

import os
import sys
import subprocess
import time
import signal
import re

# Path to live.py
LIVE_PY_PATH = '/root/CascadeProjects/sports_bot/football/live.py'
BACKUP_PATH = '/root/CascadeProjects/sports_bot/football/live.py.bak'

# Error injection code for thread test
THREAD_ERROR_CODE = """
# Test thread exception handling
def _test_thread_error():
    # Wait a moment to ensure everything is properly initialized
    import time
    time.sleep(1)
    # This function will throw an exception
    raise Exception("This is a deliberate test error in a thread")

test_thread = threading.Thread(target=_test_thread_error, name="TestErrorThread")
test_thread.daemon = True
test_thread.start()
"""

# Error injection code for asyncio test
ASYNCIO_ERROR_CODE = """
# Test asyncio exception handling
async def _test_asyncio_error():
    # Wait a moment to make sure everything is initialized
    await asyncio.sleep(2)
    # This will throw an exception
    raise Exception("This is a deliberate test error in asyncio task")

# Schedule the task to run in the event loop
asyncio.ensure_future(_test_asyncio_error())
"""

# Error injection code for combined thread and asyncio errors
COMBINED_ERROR_CODE = """
# Test multiple exception handlers simultaneously

# Thread error test
def _test_thread_error():
    import time
    time.sleep(1.5)  # Slightly different timing than the asyncio error
    raise Exception("This is a deliberate test error in a thread (combined test)")

test_thread = threading.Thread(target=_test_thread_error, name="CombinedTestThread")
test_thread.daemon = True
test_thread.start()

# Asyncio error test
async def _test_asyncio_error():
    await asyncio.sleep(2.5)
    raise Exception("This is a deliberate test error in asyncio task (combined test)")

# Schedule the task to run in the event loop
asyncio.ensure_future(_test_asyncio_error())
"""

# Code to simulate an import error
IMPORT_ERROR_CODE = """
# Force an import error for testing
from nonexistent_module import nonexistent_function  # This will fail
"""

def backup_live_py():
    """Create a backup of live.py"""
    print(f"Creating backup of {LIVE_PY_PATH}...")
    with open(LIVE_PY_PATH, 'r') as f:
        content = f.read()
    
    with open(BACKUP_PATH, 'w') as f:
        f.write(content)
    
    return content

def restore_live_py():
    """Restore live.py from backup"""
    if os.path.exists(BACKUP_PATH):
        print(f"Restoring {LIVE_PY_PATH} from backup...")
        with open(BACKUP_PATH, 'r') as f:
            content = f.read()
        
        with open(LIVE_PY_PATH, 'w') as f:
            f.write(content)
        
        os.remove(BACKUP_PATH)
    else:
        print("Backup file not found. Cannot restore.")

def inject_thread_error(content):
    """Inject thread error test code into live.py"""
    print("Injecting thread error test code...")
    
    # Find a good location to inject the code - just before the main_async function
    pattern = r'async def main_async\(\):'
    match = re.search(pattern, content)
    
    if match:
        position = match.start()
        new_content = content[:position] + THREAD_ERROR_CODE + "\n" + content[position:]
        
        with open(LIVE_PY_PATH, 'w') as f:
            f.write(new_content)
        
        return True
    else:
        print("Could not find a suitable location to inject thread error code.")
        return False

def inject_asyncio_error(content):
    """Inject asyncio error test code into live.py"""
    print("Injecting asyncio error test code...")
    
    # Find a good location in the main_async function to inject the code
    pattern = r'async def main_async\(\):[^\n]*\n\s+'
    match = re.search(pattern, content)
    
    if match:
        position = match.end()
        new_content = content[:position] + ASYNCIO_ERROR_CODE + "\n    " + content[position:]
        
        with open(LIVE_PY_PATH, 'w') as f:
            f.write(new_content)
        
        return True
    else:
        print("Could not find a suitable location to inject asyncio error code.")
        return False

def run_live_py(wait_time=10):
    """Run live.py and capture its output"""
    print(f"\nStarting live.py to test error handling (waiting {wait_time} seconds)...")
    process = subprocess.Popen(
        ['python3', LIVE_PY_PATH],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Give it time to trigger the errors
    time.sleep(wait_time)
    
    # Kill the process
    try:
        process.send_signal(signal.SIGTERM)
    except:
        pass
    
    # Get the output
    try:
        output, _ = process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
        
    return output

def run_thread_error_test():
    """Run test for thread exception handling"""
    print("\n=== Thread Exception Handling Test ===")
    
    try:
        # Backup live.py
        original_content = backup_live_py()
        
        # Inject thread error
        if not inject_thread_error(original_content):
            return False
        
        # Run live.py
        output = run_live_py()
        
        # Check the output for expected error messages
        if "Thread 'TestErrorThread' crashed" in output:
            print("✅ TEST PASSED: Thread error was properly handled!")
            print("The exception handler caught the thread error and attempted to send a Telegram alert.")
            success = True
        else:
            print("❌ TEST FAILED: Thread error was not handled as expected.")
            print("Output did not contain expected error messages.")
            success = False
        
        # Print the relevant output
        print("\nRelevant output from live.py:")
        for line in output.splitlines():
            if "Thread" in line and "crashed" in line:
                print(f"  {line}")
                
        return success
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Restore live.py from backup
        restore_live_py()

def run_asyncio_error_test():
    """Run test for asyncio exception handling"""
    print("\n=== Asyncio Exception Handling Test ===")
    
    try:
        # Backup live.py
        original_content = backup_live_py()
        
        # Inject asyncio error
        if not inject_asyncio_error(original_content):
            return False
        
        # Run live.py
        output = run_live_py()
        
        # Check the output for expected error messages
        if "Asyncio error" in output and "deliberate test error in asyncio" in output:
            print("✅ TEST PASSED: Asyncio error was properly handled!")
            print("The exception handler caught the asyncio error and attempted to send a Telegram alert.")
            success = True
        else:
            print("❌ TEST FAILED: Asyncio error was not handled as expected.")
            print("Output did not contain expected error messages.")
            success = False
        
        # Print the relevant output
        print("\nRelevant output from live.py:")
        for line in output.splitlines():
            if "Asyncio error" in line:
                print(f"  {line}")
                
        return success
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Restore live.py from backup
        restore_live_py()

def run_combined_error_test():
    """Run test for combined thread and asyncio exception handling"""
    print("\n=== Combined Exception Handling Test ===")
    
    try:
        # Backup live.py
        original_content = backup_live_py()
        
        # Inject combined errors
        print("Injecting combined thread and asyncio error test code...")
        pattern = r'async def main_async\(\):[^\n]*\n\s+'
        match = re.search(pattern, original_content)
        
        if match:
            position = match.end()
            new_content = original_content[:position] + COMBINED_ERROR_CODE + "\n    " + original_content[position:]
            
            with open(LIVE_PY_PATH, 'w') as f:
                f.write(new_content)
        else:
            print("Could not find a suitable location to inject combined error code.")
            return False
        
        # Run live.py
        output = run_live_py()
        
        # Check for both expected error messages
        thread_found = "Thread 'CombinedTestThread' crashed" in output
        asyncio_found = "Asyncio error" in output and "combined test" in output
        
        if thread_found and asyncio_found:
            print("✅ TEST PASSED: Both thread and asyncio errors were properly handled!")
            print("The exception handler caught both errors and attempted to send Telegram alerts.")
            success = True
        elif thread_found:
            print("⚠️ PARTIAL TEST: Thread error was handled, but asyncio error was not detected.")
            success = False
        elif asyncio_found:
            print("⚠️ PARTIAL TEST: Asyncio error was handled, but thread error was not detected.")
            success = False
        else:
            print("❌ TEST FAILED: Neither thread nor asyncio errors were handled.")
            success = False
        
        # Print the relevant output
        print("\nRelevant output from live.py:")
        for line in output.splitlines():
            if ("Thread" in line and "crashed" in line) or "Asyncio error" in line:
                print(f"  {line}")
        
        return success
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Restore live.py from backup
        restore_live_py()

def run_import_with_thread_test():
    """Run test for import error with thread exception"""
    print("\n=== Import + Thread Error Handling Test ===")
    
    try:
        # Backup live.py
        original_content = backup_live_py()
        
        # Find a good place to inject import error - at the top of main_async
        pattern = r'async def main_async\(\):[^\n]*\n\s+'
        match = re.search(pattern, original_content)
        
        if not match:
            print("Could not find a suitable location to inject import error.")
            return False
            
        position = match.end()
        
        # Add both import error and thread error
        combined_code = IMPORT_ERROR_CODE + "\n" + THREAD_ERROR_CODE
        new_content = original_content[:position] + combined_code + "\n    " + original_content[position:]
        
        with open(LIVE_PY_PATH, 'w') as f:
            f.write(new_content)
        
        # Run live.py
        output = run_live_py()
        
        # Check for both expected error messages
        import_error = "No module named 'nonexistent_module'" in output or "ImportError" in output
        thread_error = "Thread 'TestErrorThread' crashed" in output
        
        if import_error and thread_error:
            print("✅ TEST PASSED: Both import and thread errors were properly handled!")
            success = True
        elif import_error:
            print("⚠️ PARTIAL TEST: Import error was handled, but thread error was not detected.")
            success = False
        elif thread_error:
            print("⚠️ PARTIAL TEST: Thread error was handled, but import error was not detected.")
            success = False
        else:
            print("❌ TEST FAILED: Neither import nor thread errors were handled.")
            success = False
        
        print("\nRelevant output from live.py:")
        for line in output.splitlines():
            if ("module" in line and "nonexistent" in line) or ("Thread" in line and "crashed" in line):
                print(f"  {line}")
        
        return success
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Restore live.py from backup
        restore_live_py()

def main():
    """Main test function"""
    import sys
    print("=== Enhanced Runtime Error Handling Tests ===\n")
    
    # Parse command line arguments
    test_type = "all"
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    
    # Track test results
    results = {}
    
    # Run selected tests
    if test_type in ["all", "thread"]:
        results["thread"] = run_thread_error_test()
    
    if test_type in ["all", "asyncio"]:
        results["asyncio"] = run_asyncio_error_test()
    
    if test_type in ["all", "combined"]:
        results["combined"] = run_combined_error_test()
    
    if test_type in ["all", "import+thread"]:
        results["import+thread"] = run_import_with_thread_test()
    
    # Print overall results
    print("\n=== Overall Test Results ===")
    
    if not results:
        print(f"No tests run. Invalid test type: {test_type}")
        print("Valid options: all, thread, asyncio, combined, import+thread")
    elif all(results.values()):
        print("✅ ALL TESTS PASSED: Error handling is working properly!")
    elif any(results.values()):
        print("⚠️ PARTIAL SUCCESS: Some tests passed, but others failed.")
        for test, result in results.items():
            print(f"  - {test}: {'PASSED' if result else 'FAILED'}")
    else:
        print("❌ ALL TESTS FAILED: Error handling is not working correctly.")
    
    print("\nTest completed. live.py has been restored to its original state.")
    print("\nUsage: python3 test_runtime_errors.py [test_type]")
    print("Where test_type is one of: all, thread, asyncio, combined, import+thread")

if __name__ == "__main__":
    main()
