#!/usr/bin/env python3
"""
Test script for the Telegram notification system
"""

import sys
import os
import traceback
from datetime import datetime

# Add the project root to the path to ensure imports work
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    print("Testing Telegram notification system...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    
    # Try to import the telegram module
    print("Attempting to import telegram module...")
    from telegram import send_message
    
    # Send a test message
    print("Sending test message...")
    result = send_message(f"Test message from Football Monitor at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if result:
        print("Message sent successfully!")
    else:
        print("Failed to send message. Check logs for details.")
    
except ImportError as e:
    print(f"Import Error: {e}")
    print("This might be due to the module path configuration.")
    print("Python path:")
    for p in sys.path:
        print(f"  - {p}")
    
except Exception as e:
    print(f"Error: {e}")
    print(traceback.format_exc())
    
print("Test completed.")
