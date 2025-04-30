#!/usr/bin/env python3
"""
3HT0 (Logger) Alert Implementation
Scans logs for matches with O/U ≥ 3.0 at minutes 4-6 that reach halftime with 0-0 score
"""

import re
import logging
from .base import LogScannerAlert

logger = logging.getLogger("log_alerts")

class ThreeHtZeroLoggerAlert(LogScannerAlert):
    """
    3HT0 (Logger) Alert
    Criteria:
    - Status: Half-time break (Status ID: 3)
    - Score: 0-0
    - Over/Under line: minimum 3.0, no maximum, recorded at minutes 4-6
    """
    def __init__(self, telegram_token=None, telegram_chat_id=None):
        super().__init__("3HT0 (Logger)", telegram_token, telegram_chat_id)
    
    def scan_log_file(self, log_file):
        """Scan the log file for matches meeting the 3HT0 criteria"""
        with open(log_file, 'r') as f:
            content = f.read()
        
        # Split the log file into individual match blocks
        match_blocks = re.split(r'==================================================\nMATCH #\d+ OF \d+\n==================================================', content)
        
        # Process each match block
        for block in match_blocks:
            if not block.strip():
                continue
                
            # Create a match identifier
            match_id = None
            match_name = None
            competition = None
            
            # Check if this match is at half-time with 0-0 score
            is_halftime = "Status: Half-time break (Status ID: 3)" in block
            is_zero_zero = "Score: 0 - 0" in block
            
            # Extract Over/Under line
            ou_line = None
            ou_time = None
            if "Over/Under:" in block:
                ou_match = re.search(r'Over/Under:.*\nTime: (\d+) min \| Over: [+-]\d+ \| Line: (\d+\.?\d*) \| Under: [+-]\d+', block)
                if ou_match:
                    ou_time = int(ou_match.group(1))
                    ou_line = float(ou_match.group(2))
            
            # Extract match name and competition for identification
            match_name_match = re.search(r'Match: (.*?)\n', block)
            if match_name_match:
                match_name = match_name_match.group(1).strip()
                
            competition_match = re.search(r'Competition: (.*?)\n', block)
            if competition_match:
                competition = competition_match.group(1).strip()
                
            # Create a unique match identifier
            if match_name and competition:
                match_id = f"{competition} - {match_name}"
            
            # Check if this match meets all criteria
            if (is_halftime and is_zero_zero and ou_line is not None and ou_time is not None and
                ou_line >= 3.0 and ou_time >= 4 and ou_time <= 6 and
                match_id and match_id not in self.tracked_matches):
                
                logger.info(f"Found match meeting 3HT0 criteria: {match_id}, O/U line: {ou_line}, Time: {ou_time} min")
                
                # Extract the full match summary section for the alert
                match_summary = ""
                in_match_section = False
                
                for line in block.split('\n'):
                    if "----- MATCH SUMMARY -----" in line:
                        in_match_section = True
                        match_summary += line + "\n"
                    elif in_match_section and "---" in line and "MATCH" in line:
                        # End of match summary section
                        in_match_section = False
                        match_summary += "\n"
                    elif in_match_section:
                        match_summary += line + "\n"
                
                # Add the O/U line information
                ou_section = ""
                in_ou_section = False
                
                for line in block.split('\n'):
                    if "Over/Under:" in line:
                        in_ou_section = True
                        ou_section += line + "\n"
                    elif in_ou_section and line.strip() == "":
                        in_ou_section = False
                        break
                    elif in_ou_section:
                        ou_section += line + "\n"
                
                # Format the alert message
                message = f"ALERT TYPE: {self.name}\n\n{match_summary}\n{ou_section}"
                
                # Send the Telegram alert
                self.send_telegram_alert(message)
                
                # Add this match to tracked matches
                self.tracked_matches.add(match_id)
