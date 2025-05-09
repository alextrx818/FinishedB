#!/usr/bin/env python3
"""
Centralized Alert System for Sports Bot

This module handles:
1. System verification alerts
2. Module availability checks
3. Error notifications

It provides a clean interface for live.py to trigger alerts
without containing the alert logic itself.
"""

import sys
import importlib
import traceback
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

# Dictionary to track module verification status
VERIFICATION_RESULTS = {
    'success': [],
    'failure': [],
    'total_checks': 0
}

# Define critical modules that must be checked
CRITICAL_MODULES = {
    # Logger system modules
    'logger': [
        'logger.main_logger',        # Main logger module
        'logger.db_api',             # Database API for logging
        'logger.json_logger',        # JSON-specific logger
    ],
    # Alert system modules
    'alerts': [
        'telegram',                 # Telegram package
    ],
    # Core functionality modules
    'core': [
        'requests',                  # For API calls
        'json',                      # For data parsing
    ],
    # Database modules (non-critical)
    'database': [
        'supabase_config',          # Supabase configuration
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
        __import__(module_name)
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
    
    # Reset verification results
    VERIFICATION_RESULTS['success'].clear()
    VERIFICATION_RESULTS['failure'].clear()
    VERIFICATION_RESULTS['total_checks'] = 0
    
    for category, modules in CRITICAL_MODULES.items():
        for module_name in modules:
            success, error_msg = check_module(module_name)
            
            # Track result
            if success:
                VERIFICATION_RESULTS['success'].append(module_name)
            else:
                VERIFICATION_RESULTS['failure'].append((module_name, error_msg))
                
            VERIFICATION_RESULTS['total_checks'] += 1
            
            # Store in category results
            results[category].append((module_name, success, error_msg))
    
    return dict(results)

def send_verification_alerts():
    """
    Send Telegram alerts for any failed module verifications.
    """
    if not VERIFICATION_RESULTS['failure']:
        # All modules verified successfully
        return
    
    # Construct the alert message
    alert_message = "⚠️ Some critical modules failed to load ⚠️\n\n"
    
    for module_name, error_msg in VERIFICATION_RESULTS['failure']:
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
    success_count = len(VERIFICATION_RESULTS['success'])
    total_count = VERIFICATION_RESULTS['total_checks']
    alert_message += f"\n{success_count}/{total_count} modules loaded successfully."
    
    # Send the alert
    try:
        from telegram import send_system_alert
        send_system_alert(
            alert_message,
            alert_type="warning",
            error_details=None  # We've already included error details in the main message
        )
    except Exception as e:
        # If sending the alert fails, at least print to console
        print(f"⚠️ SYSTEM ALERT: Module verification failed but couldn't send alert: {e}")

def verify_system():
    """
    Main function to verify all system modules and send alerts for failures.
    """
    print("Verifying system modules...")
    results = verify_modules()
    
    # Print results to console
    success_count = len(VERIFICATION_RESULTS['success'])
    total_count = VERIFICATION_RESULTS['total_checks']
    
    print(f"Module verification complete: {success_count}/{total_count} successful")
    
    if VERIFICATION_RESULTS['failure']:
        print("⚠️ The following modules failed verification:")
        for module_name, error_msg in VERIFICATION_RESULTS['failure']:
            print(f"  ❌ {module_name}")
        
        # Send alert for failures
        send_verification_alerts()
    else:
        print("✅ All modules verified successfully")

def send_supabase_failure_alert(error_message):
    """
    Send an alert for Supabase connection failures.
    
    Args:
        error_message: The error message from the Supabase connection attempt
    """
    try:
        from telegram import send_system_alert
        send_system_alert(
            f"Supabase connection failed. Sports bot running with limited functionality.",
            alert_type="error",
            error_details=error_message
        )
    except Exception as e:
        print(f"⚠️ Could not send Telegram alert for Supabase failure: {e}")

def send_database_operation_alert(operation, match_id, error_message):
    """
    Send an alert for database operation failures.
    
    Args:
        operation: The type of database operation that failed
        match_id: The ID of the match being processed
        error_message: The error message from the database operation
    """
    try:
        from telegram import send_system_alert
        send_system_alert(
            f"Database {operation} failed for match {match_id}",
            alert_type="error",
            error_details=error_message
        )
    except Exception as e:
        print(f"⚠️ Could not send Telegram alert for database operation: {e}")

def send_orchestration_alert(issues):
    """
    Send consolidated alerts for system orchestration issues.
    This is called by live.py's orchestration system when components fail verification.
    
    Args:
        issues: List of dictionaries containing component issues with keys:
                - component: The name of the component
                - error: Error message
                - critical: Boolean indicating if the component is critical
                - category: Component category (infrastructure, core, data)
    """
    if not issues:
        return
        
    try:
        from telegram import send_system_alert
        
        # Group issues by critical vs non-critical
        critical_issues = [issue for issue in issues if issue['critical']]
        non_critical_issues = [issue for issue in issues if not issue['critical']]
        
        # Create the alert message
        alert_type = "error" if critical_issues else "warning"
        
        # Determine the alert severity for the title
        if critical_issues:
            title = f"⚠️ CRITICAL ALERT: {len(critical_issues)} critical components failed"  
        else:
            title = f"⚠️ WARNING: {len(non_critical_issues)} non-critical components have issues"
            
        # Build detailed message
        message = f"{title}\n\n"
        
        # First list critical issues
        if critical_issues:
            message += "CRITICAL FAILURES:\n"
            for issue in critical_issues:
                message += f"  ❌ {issue['category']}/{issue['component']}\n"
            message += "\n"
            
        # Then list non-critical issues
        if non_critical_issues:
            message += "NON-CRITICAL ISSUES:\n"
            for issue in non_critical_issues:
                message += f"  ⚠️ {issue['category']}/{issue['component']}\n"
            message += "\n"
        
        # Add detailed error information (limit length for each)
        message += "DETAILS:\n"
        for issue in issues:
            # Truncate error messages that are too long
            error_msg = issue['error']
            if len(error_msg) > 200:
                error_msg = error_msg[:200] + "..."
                
            message += f"\n{issue['component']}:\n{error_msg}\n"
        
        # Send the consolidated alert
        send_system_alert(
            message,
            alert_type=alert_type,
        )
    except Exception as e:
        print(f"⚠️ Could not send orchestration alerts: {e}")

def health_check():
    """
    Health check function that components with health_check support can implement.
    This function returns a tuple of (is_healthy, message).
    
    Returns:
        Tuple of (bool, str): (True if healthy, explanation message)
    """
    # Check if we can import telegram for sending alerts
    try:
        from telegram import send_system_alert
        return True, "Alert system is healthy"
    except ImportError:
        return False, "Cannot import telegram module for sending alerts"
    except Exception as e:
        return False, f"Alert system error: {str(e)}"

if __name__ == "__main__":
    # If run directly, perform verification
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        verify_system()
    elif len(sys.argv) > 1 and sys.argv[1] == "--health":
        # Run health check and print result
        healthy, message = health_check()
        status = "HEALTHY" if healthy else "UNHEALTHY"
        print(f"Alert system status: {status}\nMessage: {message}")
    else:
        print("Run with --verify to test the alert system")
        print("Run with --health to check alert system health")
