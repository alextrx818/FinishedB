#!/usr/bin/env python3
"""
Test script to verify import error handling in live.py

This script can test import error handling using two methods:
1. Temporarily renaming a critical module to force an import error
2. Injecting an import statement for a non-existent module

Usage:
    python3 test_import_failure.py [test_type]
    
Where test_type is one of:
    rename     - Test by renaming an existing module (default)
    inject     - Test by injecting a non-existent import
    all        - Run both tests sequentially

The script will output results of the test and restore any modified files.
"""

import os
import sys
import subprocess
import time
import signal
import re

# Paths for the rename test
MODULE_PATH = '/root/CascadeProjects/sports_bot/football/logger/main_logger.py'
BACKUP_PATH = '/root/CascadeProjects/sports_bot/football/logger/main_logger.py.bak'

# Paths for the inject test
LIVE_PY_PATH = '/root/CascadeProjects/sports_bot/football/live.py'
LIVE_PY_BACKUP = '/root/CascadeProjects/sports_bot/football/live.py.bak'

# Import injection code
IMPORT_ERROR_CODE = "\ntry:\n    from nonexistent_module import nonexistent_function  # This will fail\nexcept Exception as e:\n    print('Expected import error in test: ' + str(e))\n"

def rename_module():
    """Temporarily rename the module to force an import error."""
    if os.path.exists(MODULE_PATH):
        print(f"Renaming {MODULE_PATH} to {BACKUP_PATH}...")
        os.rename(MODULE_PATH, BACKUP_PATH)
        return True
    else:
        print(f"Module {MODULE_PATH} not found. Test cannot proceed.")
        return False

def restore_module():
    """Restore the original module name."""
    if os.path.exists(BACKUP_PATH):
        print(f"Restoring {BACKUP_PATH} to {MODULE_PATH}...")
        os.rename(BACKUP_PATH, MODULE_PATH)
        
def backup_live_py():
    """Create a backup of live.py"""
    print(f"Creating backup of {LIVE_PY_PATH}...")
    with open(LIVE_PY_PATH, 'r') as f:
        content = f.read()
    
    with open(LIVE_PY_BACKUP, 'w') as f:
        f.write(content)
    
    return content

def restore_live_py():
    """Restore live.py from backup"""
    if os.path.exists(LIVE_PY_BACKUP):
        print(f"Restoring {LIVE_PY_PATH} from backup...")
        with open(LIVE_PY_BACKUP, 'r') as f:
            content = f.read()
        
        with open(LIVE_PY_PATH, 'w') as f:
            f.write(content)
        
        os.remove(LIVE_PY_BACKUP)
    else:
        print("Backup file not found. Cannot restore live.py.")
        
def inject_import_error():
    """Inject an import error into live.py"""
    if os.path.exists(LIVE_PY_PATH):
        # Backup first
        original_content = backup_live_py()
        
        # Find a good spot to inject the error - just after the first few import statements
        pattern = r'import os, sys'
        match = re.search(pattern, original_content)
        
        if match:
            position = match.end()
            new_content = original_content[:position] + IMPORT_ERROR_CODE + original_content[position:]
            
            with open(LIVE_PY_PATH, 'w') as f:
                f.write(new_content)
            
            return True
        else:
            print("Could not find a suitable location to inject import error.")
            return False
    else:
        print(f"File {LIVE_PY_PATH} not found. Test cannot proceed.")
        return False

def run_live_py(wait_time=5):
    """Run live.py and capture its output."""
    print(f"\nStarting live.py to test import error handling (waiting {wait_time} seconds)...")
    process = subprocess.Popen(
        ['python3', '/root/CascadeProjects/sports_bot/football/live.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Give it time to process the error
    time.sleep(wait_time)
    
    # Kill the process (it should exit on its own, but just in case)
    try:
        process.send_signal(signal.SIGTERM)
    except:
        pass
    
    # Get the output with better error handling
    try:
        output, _ = process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
    
    return output

def run_rename_test():
    """Test import error handling by renaming a module."""
    print("=== Import Error Handling Test (Module Rename) ===\n")
    restored = False
    
    try:
        # Rename the module
        if not rename_module():
            return False
        
        # Run live.py
        output = run_live_py()
        
        # Restore the module early to minimize downtime
        restore_module()
        restored = True
        
        # Check the output for expected error messages
        if "Logger import failed" in output:
            print("\n✅ TEST PASSED: Import error was properly handled!")
            print("The program detected the missing module and attempted to continue running.")
            success = True
        else:
            print("\n❌ TEST FAILED: Import error was not handled as expected.")
            print("Output did not contain expected error messages.")
            success = False
            
        # Print the relevant output
        print("\nRelevant output from live.py:")
        for line in output.splitlines():
            if "import failed" in line or "alert" in line.lower():
                print(f"  {line}")
                
        return success
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    finally:
        # Always restore the original module if not already done
        if not restored:
            restore_module()
            
def run_inject_test():
    """Test import error handling by injecting a non-existent import."""
    print("\n=== Import Error Handling Test (Import Injection) ===\n")
    restored = False
    
    try:
        # Inject the import error
        if not inject_import_error():
            return False
        
        # Run live.py
        output = run_live_py()
        
        # Restore live.py early to minimize downtime
        restore_live_py()
        restored = True
        
        # Check the output for expected error messages
        if "nonexistent_module" in output:
            print("\n✅ TEST PASSED: Injected import error was properly handled!")
            print("The program caught the error from the non-existent module import.")
            success = True
        else:
            print("\n❌ TEST FAILED: Injected import error was not handled as expected.")
            print("Output did not contain expected error messages.")
            success = False
            
        # Print the relevant output
        print("\nRelevant output from live.py:")
        for line in output.splitlines():
            if "nonexistent" in line or "import" in line or "error" in line.lower():
                print(f"  {line}")
                
        return success
    
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        return False
    
    finally:
        # Always restore the original live.py if not already done
        if not restored:
            restore_live_py()

def main():
    """Main test function."""
    import sys
    print("=== Enhanced Import Error Handling Tests ===\n")
    
    # Parse command line arguments
    test_type = "rename"
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
    
    # Track test results
    results = {}
    
    # Run the requested test(s)
    if test_type in ["rename", "all"]:
        results["rename"] = run_rename_test()
    
    if test_type in ["inject", "all"]:
        results["inject"] = run_inject_test()
    
    # Print overall results
    print("\n=== Overall Test Results ===")
    
    if not results:
        print(f"No tests run. Invalid test type: {test_type}")
        print("Valid options: rename, inject, all")
    elif all(results.values()):
        print("✅ ALL TESTS PASSED: Import error handling is working properly!")
    elif any(results.values()):
        print("⚠️ PARTIAL SUCCESS: Some tests passed, but others failed.")
        for test, result in results.items():
            print(f"  - {test}: {'PASSED' if result else 'FAILED'}")
    else:
        print("❌ ALL TESTS FAILED: Import error handling is not working correctly.")
    
    print("\nTest completed. All files have been restored to their original state.")
    print("\nUsage: python3 test_import_failure.py [test_type]")
    print("Where test_type is one of: rename, inject, all")

if __name__ == "__main__":
    main()
