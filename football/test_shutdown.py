#!/usr/bin/env python3
"""
Simple test script to verify the shutdown notification works properly.
This uses the same exit handler as live.py but runs as a separate process.
"""
import os
import sys
import atexit
import requests
import time
import datetime

# Function to send a Telegram alert (copied from live.py)
def send_telegram_alert(message, token="7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko", chat_id="6128359776"):
    """Send an alert message via Telegram"""
    telegram_url = f"https://api.telegram.org/bot{token}/sendMessage"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted_message = f"{message}\n\nTimestamp: {timestamp}"
    
    try:
        response = requests.post(
            telegram_url,
            json={
                "chat_id": chat_id,
                "text": formatted_message,
                "parse_mode": "HTML"
            }
        )
        if response.status_code == 200:
            print(f"Successfully sent Telegram alert: {message}")
        else:
            print(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"Error sending Telegram alert: {e}")

# Setup exit handler
def exit_handler():
    exit_message = f"🧪 <b>TEST: SHUTDOWN NOTIFICATION</b>\n\nThis is a test of the shutdown notification system. If you're seeing this, the shutdown alerts from live.py will work correctly."
    try:
        send_telegram_alert(exit_message)
    except:
        print("Failed to send exit notification")

# Register exit handler
atexit.register(exit_handler)

# Start message
print("Testing shutdown notification...")
send_telegram_alert("🧪 <b>TEST: STARTING SHUTDOWN TEST</b>\n\nThe test script will run for 5 seconds and then exit, triggering a shutdown notification.")

# Wait a few seconds
print("Running for 5 seconds before shutdown...")
time.sleep(5)

# Exit normally, which should trigger the exit handler
print("Test complete, exiting normally.")
sys.exit(0)
