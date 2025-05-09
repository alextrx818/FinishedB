#!/usr/bin/env python3
"""
Test script for the sports bot alert system.
This will simulate various failures to verify alerts are sent correctly.
"""

import sys
import os
import importlib
import time

# Add parent directory to path to allow imports
sys.path.append('/root/CascadeProjects/sports_bot')

# Set up proper import paths
print(f"Current directory: {os.getcwd()}")
print(f"Python path: {sys.path}")

def test_module_verification():
    """Test that module verification alerts work"""
    print("\n=== Testing Module Verification Alerts ===")
    try:
        # Import directly from live.py which now has the verification functionality
        from live import verify_system
        print("Running system verification test...")
        verify_system()
        print("System verification completed")
    except Exception as e:
        print(f"⚠️ System verification error: {e}")

def test_supabase_alert():
    """Test Supabase connection failure alerts"""
    print("\n=== Testing Supabase Connection Alerts ===")
    # Temporarily rename supabase_config.py to force an import error
    supabase_path = '/root/CascadeProjects/sports_bot/supabase_config.py'
    temp_path = '/root/CascadeProjects/sports_bot/supabase_config.py.temp'
    
    if os.path.exists(supabase_path):
        try:
            # Backup the real file
            os.rename(supabase_path, temp_path)
            print("Temporarily moved supabase_config.py to simulate failure")
            
            # Try to import, this should fail
            try:
                # Clear any cached import
                if 'supabase_config' in sys.modules:
                    del sys.modules['supabase_config']
                    
                # This will fail
                from supabase_config import supabase
                print("✓ Supabase connection established")
            except Exception as e:
                print(f"⚠️ Supabase connection failed as expected: {e}")
                print("⚠️ Running with limited functionality - database features disabled")
                
                # Import telegram and send alert
                try:
                    # Import directly from the current directory structure
                    from telegram import send_system_alert
                    send_system_alert(
                        f"TEST ALERT: Supabase connection failed. Sports bot running with limited functionality.", 
                        alert_type="error",
                        error_details=str(e)
                    )
                    print("✓ Test alert sent for Supabase failure")
                except Exception as alert_error:
                    print(f"⚠️ Could not send Telegram alert for Supabase failure: {alert_error}")
        finally:
            # Restore the original file
            if os.path.exists(temp_path):
                os.rename(temp_path, supabase_path)
                print("Restored supabase_config.py")
    else:
        print(f"⚠️ Could not find {supabase_path} to test with")

def test_logger_alert():
    """Test logger failure alerts"""
    print("\n=== Testing Logger Failure Alerts ===")
    # Create a temporary directory that shouldn't be writable
    try:
        # Import the logger directly to get access to its internals
        import importlib
        logger_module = importlib.import_module('logger.main_logger')
        
        # Save the original path
        original_path = logger_module.LOG_FILE_PATH
        
        # Set a bad path that will cause a failure
        test_bad_path = '/root/nonexistent_directory/main.logger'
        print(f"Setting bad logger path: {test_bad_path}")
        
        # Create a controlled failure by trying to log directly
        try:
            # Temporarily override the path
            logger_module.LOG_FILE_PATH = test_bad_path
            
            # Force the logger to reload
            print("Testing logger setup failure alert...")
            if hasattr(logger_module, 'setup_logger'):
                logger_module.setup_logger()
            
        except Exception as e:
            print(f"Logger setup failed as expected: {e}")
            
        finally:
            # Restore the original path
            logger_module.LOG_FILE_PATH = original_path
            print(f"Restored original logger path: {original_path}")
            
    except Exception as e:
        print(f"Error in logger test: {e}")

if __name__ == "__main__":
    print("Starting alert system tests...")
    print("NOTE: These are controlled tests and errors are expected.\n")
    
    # Uncomment tests as needed
    test_module_verification()
    test_supabase_alert()  
    test_logger_alert()
    
    print("\n=== Alert Testing Complete ===")
    print("Check your Telegram messages for test alerts")
