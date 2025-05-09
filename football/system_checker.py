#!/usr/bin/env python3
"""
System Module Checker for Football Monitor

This module verifies critical system components at startup and sends
alerts via Telegram if any fail, without preventing the system from running.
"""

import sys
import importlib
import traceback
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Dictionary to track module verification status
verification_results = {
    'success': [],
    'failure': [],
    'total_checks': 0
}

# Define critical modules that must be checked
CRITICAL_MODULES = {
    # Logger system modules
    'logger': [
        'football.logger.main_logger',
        'football.logger.db_api',
        'football.logger.json_logger',
    ],
    # Alert system modules
    'alerts': [
        'football.telegram',
        'football.telegram.notifier',
        'football.alerts',
    ],
    # Core functionality modules
    'core': [
        'football.live',
        'football.odds_analyzer',
    ],
    # Database modules (non-critical)
    'database': [
        'supabase_config',
    ]
}

def check_module(module_name: str) -> Tuple[bool, Optional[str]]:
    """
    Check if a module can be imported without error.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        Tuple of (success status, error message if any)
    """
    try:
        # Attempt to import the module
        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        # Capture the error but don't let it crash the program
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        return False, error_msg

def verify_modules() -> Dict[str, List[Tuple[str, bool, Optional[str]]]]:
    """
    Verify all critical modules and organize results by category.
    
    Returns:
        Dictionary of results organized by category
    """
    results = defaultdict(list)
    
    for category, modules in CRITICAL_MODULES.items():
        for module_name in modules:
            success, error_msg = check_module(module_name)
            
            # Track result
            if success:
                verification_results['success'].append(module_name)
            else:
                verification_results['failure'].append((module_name, error_msg))
                
            verification_results['total_checks'] += 1
            
            # Store in category results
            results[category].append((module_name, success, error_msg))
    
    return dict(results)

def send_alert_for_failures(results: Dict[str, List[Tuple[str, bool, Optional[str]]]]):
    """
    Send Telegram alerts for any failed module verifications.
    
    Args:
        results: Verification results by category
    """
    if not verification_results['failure']:
        # All modules verified successfully
        return
    
    # Try to import the Telegram system without causing a crash if it fails
    try:
        # First check if we can import the alert system
        alert_system_available = False
        try:
            from football.telegram import send_system_alert
            alert_system_available = True
        except ImportError:
            # If we can't import from football.telegram, try direct import
            try:
                # Adjust the path for direct import
                import os, sys
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from telegram.notifier import send_system_alert
                alert_system_available = True
            except ImportError:
                pass
        
        if alert_system_available:
            # Construct the alert message
            alert_message = "⚠️ Some critical modules failed to load ⚠️\n\n"
            
            for module_name, error_msg in verification_results['failure']:
                alert_message += f"❌ Module: `{module_name}`\n"
                
                # Add error details, but limit length
                if error_msg:
                    # Truncate error message if it's too long
                    if len(error_msg) > 300:
                        short_error = error_msg[:300] + "..."
                    else:
                        short_error = error_msg
                    
                    alert_message += f"Error: ```\n{short_error}\n```\n"
            
            # Add summary
            alert_message += f"\n{len(verification_results['success'])}/{verification_results['total_checks']} modules loaded successfully."
            
            # Send the alert
            send_system_alert(
                alert_message,
                alert_type="warning",
                error_details=None  # We've already included error details in the main message
            )
    except Exception as e:
        # If sending the alert fails, at least print to console
        print(f"⚠️ SYSTEM ALERT: Module verification failed but couldn't send Telegram alert: {e}")
        print(f"Failed modules: {verification_results['failure']}")

def verify_system():
    """
    Main function to verify all system modules and send alerts for failures.
    """
    print("Verifying system modules...")
    results = verify_modules()
    
    # Print results to console
    success_count = len(verification_results['success'])
    total_count = verification_results['total_checks']
    
    print(f"Module verification complete: {success_count}/{total_count} successful")
    
    if verification_results['failure']:
        print("⚠️ The following modules failed verification:")
        for module_name, error_msg in verification_results['failure']:
            print(f"  ❌ {module_name}")
        
        # Send alert for failures
        send_alert_for_failures(results)
    else:
        print("✅ All modules verified successfully")

if __name__ == "__main__":
    # If run directly, perform verification
    verify_system()
