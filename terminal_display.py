#!/usr/bin/env python3
"""
Terminal Display for Sports Bot
Displays live.py output in a terminal without modifying the original live.py file
"""

import subprocess
import re
import sys
import time
import signal
import os

# Terminal colors
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    CYAN = '\033[0;36m'
    PURPLE = '\033[0;35m'
    NC = '\033[0m'  # No Color

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear')

def print_header():
    """Print the header for the terminal display"""
    clear_screen()
    print(f"{Colors.BLUE}==============================================={Colors.NC}")
    print(f"{Colors.BLUE}      SPORTS BOT LIVE TERMINAL DISPLAY        {Colors.NC}")
    print(f"{Colors.BLUE}==============================================={Colors.NC}")
    print(f"{Colors.GREEN}Live.py output - Press Ctrl+C to exit{Colors.NC}\n")

def format_line(line):
    """Format a single line of output"""
    # Extract the message part without the prefix (date, hostname, etc.)
    match = re.search(r'[A-Za-z]+ [0-9]+ [0-9:.]+ [a-zA-Z0-9_-]+ bash\[[0-9]+\]: (.*)', line)
    if match:
        message = match.group(1)
    else:
        message = line
    
    # Check if line contains different types of information and format accordingly
    if "MATCH SUMMARY" in message:
        return f"\n{Colors.YELLOW}{message}{Colors.NC}"
    elif "Timestamp:" in message:
        return f"{Colors.CYAN}{message}{Colors.NC}"
    elif "Competition:" in message:
        return f"{Colors.GREEN}{message}{Colors.NC}"
    elif "Match:" in message:
        return f"{Colors.PURPLE}{message}{Colors.NC}"
    elif "Score:" in message:
        return f"{Colors.RED}{message}{Colors.NC}"
    elif "MATCH BETTING ODDS" in message:
        return f"{Colors.YELLOW}{message}{Colors.NC}"
    elif any(x in message for x in ["ML (Money Line):", "SPREAD", "Over/Under:"]):
        return f"{Colors.CYAN}{message}{Colors.NC}"
    elif "MATCH ENVIRONMENT" in message:
        return f"{Colors.YELLOW}{message}{Colors.NC}"
    elif "========" in message:
        return f"{Colors.BLUE}{message}{Colors.NC}"
    else:
        return message

def handle_exit(signum, frame):
    """Handle exit signal gracefully"""
    print(f"\n{Colors.GREEN}Terminal display stopped. The live.py process is still running.{Colors.NC}")
    sys.exit(0)

def main():
    """Main function to display the journal output"""
    # Register signal handler for clean exit
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    print_header()
    
    # Check if the sportsbot service is running
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "sportsbot.service"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.stdout.strip() != "active":
            print(f"{Colors.RED}Warning: sportsbot.service is not running.{Colors.NC}")
            print(f"{Colors.YELLOW}Starting from last available logs...{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}Error checking service status: {e}{Colors.NC}")
    
    try:
        # Run journalctl and process its output in real-time
        process = subprocess.Popen(
            ["journalctl", "-u", "sportsbot.service", "-f", "-n", "50", "-o", "cat"],
            stdout=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Process and print each line with formatting
        for line in iter(process.stdout.readline, ""):
            formatted_line = format_line(line.rstrip())
            print(formatted_line)
    
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.NC}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
