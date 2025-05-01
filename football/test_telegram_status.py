import requests
import time
import json

# Telegram credentials
TOKEN = "7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko"
CHAT_ID = "6128359776"

def send_message(text):
    """Send a message to the specified chat ID"""
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    response = requests.post(url, json=payload)
    print(f"Send message response: {response.status_code}")
    print(response.json())
    
def get_updates(offset=None):
    """Get updates from Telegram"""
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    params = {
        "timeout": 10,
        "allowed_updates": ["message"]
    }
    
    if offset:
        params["offset"] = offset
        
    response = requests.get(url, params=params)
    print(f"Get updates response: {response.status_code}")
    return response.json()

def main():
    """Test the Telegram functionality"""
    print("Starting Telegram test...")
    
    # Send test message
    send_message("🔄 <b>TELEGRAM TEST</b>\n\nThis is a test message from the Telegram test script.")
    
    # Get current updates and grab the latest update_id
    updates = get_updates()
    print(f"Current updates: {json.dumps(updates, indent=2)}")
    
    offset = None
    if "result" in updates and updates["result"]:
        offset = updates["result"][-1]["update_id"] + 1
        print(f"Starting with offset: {offset}")
    
    print("\nNow listening for /status commands. Send a message to the bot with '/status' to test.")
    print("Press Ctrl+C to exit.")
    
    try:
        while True:
            updates = get_updates(offset)
            
            if "result" in updates and updates["result"]:
                print(f"Received {len(updates['result'])} updates")
                
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        message_text = update["message"]["text"]
                        message_chat_id = str(update["message"]["chat"]["id"])
                        print(f"Received message: '{message_text}' from chat_id: {message_chat_id}")
                        
                        if message_text == "/status" and message_chat_id == CHAT_ID:
                            print("Status command received!")
                            send_message("📊 <b>STATUS TEST SUCCESSFUL</b>\n\nThe /status command was received and processed correctly.")
            
            # Wait a bit before polling again
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\nTest ended by user.")

if __name__ == "__main__":
    main()
