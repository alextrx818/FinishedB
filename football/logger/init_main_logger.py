#!/usr/bin/env python3
"""
Simple script to initialize main.logger without running the entire application.
This script will create the main.logger file if it doesn't exist.
"""
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

# Define the logger path
LOGGER_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE_PATH = os.path.join(LOGGER_DIR, "main.logger")

def init_main_logger():
    print(f"Initializing main.logger at: {LOG_FILE_PATH}")
    
    # Create logger
    logger = logging.getLogger("sports_bot")
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    
    # Create a rotating file handler
    rotating_handler = TimedRotatingFileHandler(
        LOG_FILE_PATH,
        when="midnight",      # roll over at midnight
        interval=1,           # every 1 day
        backupCount=30,       # keep 30 days' worth of logs
        encoding="utf-8",     # use UTF-8 encoding
        utc=False             # use local time for rollover
    )
    rotating_handler.setLevel(logging.INFO)
    rotating_handler.setFormatter(formatter)
    
    # append the date suffix
    rotating_handler.suffix = "%Y-%m-%d"
    
    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()
    
    logger.addHandler(rotating_handler)
    
    # Write initial header
    logger.info("=" * 50)
    logger.info("MAIN.LOGGER INITIALIZED - Ready to receive logs")
    logger.info("=" * 50)
    
    print(f"main.logger successfully initialized at: {LOG_FILE_PATH}")
    return True

if __name__ == "__main__":
    init_main_logger()
