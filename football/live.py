#!/usr/bin/env python3
# ⚠️ Please review docs/live-policy.md for all critical init & change-doc requirements.

# Initialize availability flags before any imports or handlers
# These will be properly set later during actual imports
TELEGRAM_AVAILABLE = False  # Flag for availability of Telegram notifications
SUPABASE_AVAILABLE = False  # Flag for availability of database features
VERBOSE_OUTPUT = False     # Flag for verbose logging (set via command line)

# ======== CONFIGURABLE SETTINGS ========
# Load configuration from environment variables with reasonable defaults
import os
import time  # For time-based operations and benchmarking

# Global for storing main event loop to reuse during shutdown
MAIN_EVENT_LOOP = None

# Performance and reliability settings
MAX_RETRIES = int(os.environ.get('SPORTS_BOT_MAX_RETRIES', '3'))                # API request retry count
RETRY_BACKOFF = float(os.environ.get('SPORTS_BOT_RETRY_BACKOFF', '1.5'))        # Exponential backoff multiplier
DB_SEMAPHORE_SIZE = int(os.environ.get('SPORTS_BOT_DB_CONCURRENCY', '10'))      # Max concurrent DB operations
ALERT_SEMAPHORE_SIZE = int(os.environ.get('SPORTS_BOT_ALERT_CONCURRENCY', '5')) # Max concurrent alerts
DEFAULT_INTERVAL = int(os.environ.get('SPORTS_BOT_UPDATE_INTERVAL', '30'))      # Default update interval in seconds
JSON_LOG_RATE = int(os.environ.get('SPORTS_BOT_JSON_LOG_RATE', '5'))            # Log every Nth match in non-verbose mode
GRACEFUL_SHUTDOWN_DELAY = float(os.environ.get('SPORTS_BOT_SHUTDOWN_DELAY', '1.0')) # Seconds before forced exit
DB_BATCH_SIZE = int(os.environ.get('SPORTS_BOT_DB_BATCH_SIZE', '10'))           # Number of records to batch in a single DB insert
DB_FLUSH_INTERVAL = int(os.environ.get('SPORTS_BOT_DB_FLUSH_INTERVAL', '60'))   # Seconds between forced DB batch flushes
ENABLE_BATCH_INSERTS = os.environ.get('SPORTS_BOT_ENABLE_BATCH_INSERTS', 'true').lower() == 'true'  # Enable batch DB inserts
ASYNC_LOGGING = os.environ.get('SPORTS_BOT_ASYNC_LOGGING', 'true').lower() == 'true'  # Enable async logging

# Entity cache settings
ENTITY_CACHE_PATH = os.environ.get('SPORTS_BOT_CACHE_PATH', '/tmp/sports_bot_cache')  # Entity cache location
ENTITY_CACHE_TTL = int(os.environ.get('SPORTS_BOT_CACHE_TTL', '86400'))         # Entity cache TTL in seconds (default: 24h)
ENABLE_ENTITY_CACHE = os.environ.get('SPORTS_BOT_ENABLE_CACHE', 'true').lower() == 'true'  # Enable entity caching

# Advanced benchmarking and instrumentation
BENCHMARK_HOT_PATHS = os.environ.get('SPORTS_BOT_BENCHMARK', 'false').lower() == 'true'  # Enable detailed benchmarking
GC_TUNING_ENABLED = os.environ.get('SPORTS_BOT_GC_TUNING', 'false').lower() == 'true'  # Enable GC optimizations

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
    
    # Define connection settings but don't create the connector yet
    # We'll create it when we have a running event loop
    CONN_PARAMS = {
        "limit": int(os.environ.get('SPORTS_BOT_CONN_LIMIT', '10')),        # Overall connection limit
        "limit_per_host": int(os.environ.get('SPORTS_BOT_HOST_LIMIT', '5')), # Prevent overwhelming any single endpoint
        "enable_cleanup_closed": True,  # Prevent socket leak
        "force_close": False,     # Keep connections alive when possible
        "ttl_dns_cache": 300      # Cache DNS results for 5 minutes
    }
    
    # Set reasonable timeouts to prevent hung connections
    TIMEOUT_PARAMS = {
        "total": int(os.environ.get('SPORTS_BOT_TIMEOUT_TOTAL', '30')),     # Overall operation timeout
        "connect": int(os.environ.get('SPORTS_BOT_TIMEOUT_CONNECT', '10')),  # Connection establishment timeout
        "sock_read": int(os.environ.get('SPORTS_BOT_TIMEOUT_READ', '15'))   # Socket read timeout
    }

    # Module-level HTTP session for reuse - will be properly initialized in main_async
    HTTP_SESSION = None
    
except ImportError:
    AIOHTTP_AVAILABLE = False
    
# GC optimization imports
if GC_TUNING_ENABLED:
    try:
        import gc
        print("✓ GC tuning enabled - optimizing garbage collection")  
    except ImportError:
        print("⚠️ GC module not available")
        GC_TUNING_ENABLED = False

# Entity cache management
if ENABLE_ENTITY_CACHE:
    try:
        import os.path
        import json
        import pickle
        import hashlib
        
        # Create cache directory if it doesn't exist
        if not os.path.exists(ENTITY_CACHE_PATH):
            os.makedirs(ENTITY_CACHE_PATH, exist_ok=True)
        
        def load_entity_cache(cache_key, default=None):
            """Load entity data from disk cache with TTL validation"""
            cache_file = os.path.join(ENTITY_CACHE_PATH, f"{cache_key}.cache")
            try:
                # Check if cache file exists and is within TTL
                if os.path.exists(cache_file):
                    file_age = time.time() - os.path.getmtime(cache_file)
                    if file_age < ENTITY_CACHE_TTL:
                        with open(cache_file, 'rb') as f:
                            cached_data = pickle.load(f)
                            if VERBOSE_OUTPUT:
                                print(f"✓ Loaded cache for {cache_key} (age: {file_age:.1f}s)")
                            return cached_data
                    elif VERBOSE_OUTPUT:
                        print(f"⚠️ Cache for {cache_key} expired (age: {file_age:.1f}s > TTL: {ENTITY_CACHE_TTL}s)")
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"Error loading cache for {cache_key}: {e}")
            return default
        
        def save_entity_cache(cache_key, data):
            """Save entity data to disk cache"""
            cache_file = os.path.join(ENTITY_CACHE_PATH, f"{cache_key}.cache")
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
                if VERBOSE_OUTPUT:
                    print(f"✓ Saved cache for {cache_key}")
                return True
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"Error saving cache for {cache_key}: {e}")
                return False
        
        def generate_cache_key(resource_type, resource_id=None, query_params=None):
            """Generate a deterministic cache key for an API resource"""
            if resource_id:
                key_parts = [resource_type, str(resource_id)]
            else:
                key_parts = [resource_type]
                
            # Add query params to key if provided
            if query_params:
                # Sort to ensure deterministic keys
                sorted_params = sorted(query_params.items())
                for k, v in sorted_params:
                    if k not in ['user', 'secret']:  # Skip credentials
                        key_parts.append(f"{k}={v}")
            
            # Create a hash of the key for filesystem safety
            key_str = "_".join(key_parts)
            key_hash = hashlib.md5(key_str.encode()).hexdigest()[:10]
            return f"{resource_type}_{key_hash}"
        
        print("✓ Entity cache system initialized at", ENTITY_CACHE_PATH)
    except ImportError as e:
        print(f"⚠️ Entity caching disabled due to missing dependencies: {e}")
        ENABLE_ENTITY_CACHE = False

# Performance benchmarking decorator
if BENCHMARK_HOT_PATHS:
    def perf_benchmark(func):
        """Decorator to benchmark function execution time"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration = time.perf_counter() - start
            
            # Store timing metrics
            func_name = func.__qualname__
            if not hasattr(Metrics, 'function_timings'):
                Metrics.function_timings = {}
            if func_name not in Metrics.function_timings:
                Metrics.function_timings[func_name] = {'calls': 0, 'total': 0.0, 'min': float('inf'), 'max': 0.0}
            
            stats = Metrics.function_timings[func_name]
            stats['calls'] += 1
            stats['total'] += duration
            stats['min'] = min(stats['min'], duration)
            stats['max'] = max(stats['max'], duration)
            
            # Log if this is an unusually slow call (>3x average)
            avg = stats['total'] / stats['calls']
            if stats['calls'] > 10 and duration > avg * 3 and duration > 0.1:
                if VERBOSE_OUTPUT:
                    print(f"Slow {func_name}: {duration:.4f}s (avg: {avg:.4f}s)")
            
            return result
        return wrapper
else:
    # No-op decorator when benchmarking is disabled
    def perf_benchmark(func):
        return func

# Optional aiofiles for non-blocking file I/O
try:
    import aiofiles
    import asyncio
    AIOFILES_AVAILABLE = True
    
    # Async logging queue setup with batching
    class AsyncJsonLogger:
        def __init__(self, filename: str, max_queue_size: int = 1000):
            self.filename = filename
            self.queue = asyncio.Queue(maxsize=max_queue_size)
            self.running = True
            self.worker_task = None
            # Batching settings
            self.batch = []
            self.batch_size = int(os.environ.get('SPORTS_BOT_LOG_BATCH_SIZE', '20'))  # Messages per batch
            self.batch_interval = float(os.environ.get('SPORTS_BOT_LOG_BATCH_INTERVAL', '5.0'))  # Seconds
            self.last_flush = time.time()
            
        async def start_worker(self):
            """Start the async logging worker"""
            self.worker_task = asyncio.create_task(self._worker())
            
        async def _worker(self):
            """Worker that processes queued log messages with batching"""
            try:
                async with aiofiles.open(self.filename, 'a') as f:
                    while self.running:
                        try:
                            # Check if we need a time-based flush
                            time_since_flush = time.time() - self.last_flush
                            if self.batch and time_since_flush >= self.batch_interval:
                                await self._flush_batch(f)
                                continue
                            
                            # Try to get a message with timeout
                            message = await asyncio.wait_for(self.queue.get(), timeout=1.0)
                            self.batch.append(message)
                            self.queue.task_done()
                            
                            # Flush if batch is full
                            if len(self.batch) >= self.batch_size:
                                await self._flush_batch(f)
                                
                        except asyncio.TimeoutError:
                            # No message available, check if we need to flush
                            if self.batch and time_since_flush >= self.batch_interval:
                                await self._flush_batch(f)
                            continue
                        except Exception as e:
                            print(f"Error in async logger worker: {e}")
            except Exception as e:
                print(f"Failed to open log file {self.filename}: {e}")
        
        async def _flush_batch(self, file_handle):
            """Flush the current batch of messages to disk"""
            if not self.batch:
                return
                
            try:
                # Write all batched messages at once
                await file_handle.write('\n'.join(self.batch) + '\n')
                await file_handle.flush()  # Ensure it's written to disk
                self.last_flush = time.time()
                
                if VERBOSE_OUTPUT and len(self.batch) > 1:
                    print(f"Flushed batch of {len(self.batch)} log messages")
                    
                # Clear the batch
                self.batch = []
            except Exception as e:
                print(f"Error flushing log batch: {e}")
                        
        async def debug(self, message):
            """Queue a debug message for async writing"""
            if ASYNC_LOGGING:
                try:
                    # Use non-blocking put with a timeout
                    await asyncio.wait_for(self.queue.put(message), timeout=0.1)
                except asyncio.TimeoutError:
                    # Queue is full, log this and continue
                    if VERBOSE_OUTPUT:
                        print(f"Async logger queue full, dropping message")
                except Exception as e:
                    print(f"Error queuing log message: {e}")
            else:
                # Fallback to synchronous logging if async logging is disabled
                try:
                    with open(self.filename, 'a') as f:
                        f.write(message + '\n')
                except Exception as e:
                    print(f"Error writing to log file: {e}")
                    
        async def shutdown(self):
            """Gracefully shut down the logger"""
            self.running = False
            
            # Make sure any batched messages are flushed
            if self.batch:
                try:
                    async with aiofiles.open(self.filename, 'a') as f:
                        await self._flush_batch(f)
                except Exception as e:
                    print(f"Error during final batch flush: {e}")
            
            if self.worker_task:
                try:
                    # Wait for remaining messages to be processed
                    await asyncio.wait_for(self.queue.join(), timeout=5.0)
                    self.worker_task.cancel()
                    await asyncio.wait_for(asyncio.gather(self.worker_task, return_exceptions=True), timeout=1.0)
                except (asyncio.TimeoutError, asyncio.CancelledError):
                    # If we timeout waiting, we still want to cancel the task
                    if self.worker_task and not self.worker_task.done():
                        self.worker_task.cancel()
                except Exception as e:
                    print(f"Error during logger shutdown: {e}")
    
except ImportError:
    AIOFILES_AVAILABLE = False

# ======== METRICS TRACKING ========
# Simple counters for operational metrics and monitoring
class Metrics:
    """Track operational metrics for monitoring and health checks"""
    alerts_sent = 0          # Total number of alerts sent
    alerts_skipped = 0       # Alerts skipped due to back-pressure
    db_operations = 0        # Total DB operations attempted
    db_successes = 0         # Successful DB operations
    db_failures = 0          # Failed DB operations
    db_skipped = 0           # DB operations skipped due to back-pressure
    api_requests = 0         # Total API requests
    api_retries = 0          # API request retries
    api_failures = 0         # Failed API requests after all retries
    startup_time = None      # Set when system starts
    last_refresh = None      # Last data refresh time
    processed_matches = 0    # Total matches processed
    
    @classmethod
    def get_health_report(cls) -> dict:
        """Return a health check report with key metrics"""
        return {
            "alerts": {
                "sent": cls.alerts_sent,
                "skipped": cls.alerts_skipped,
            },
            "database": {
                "operations": cls.db_operations,
                "successes": cls.db_successes,
                "failures": cls.db_failures,
                "skipped": cls.db_skipped,
                "success_rate": (cls.db_successes / cls.db_operations if cls.db_operations > 0 else 1.0),
            },
            "api": {
                "requests": cls.api_requests,
                "retries": cls.api_retries,
                "failures": cls.api_failures,
                "retry_rate": (cls.api_retries / cls.api_requests if cls.api_requests > 0 else 0.0),
            },
            "uptime": {
                "startup": cls.startup_time.isoformat() if cls.startup_time else None,
                "last_refresh": cls.last_refresh.isoformat() if cls.last_refresh else None,
            },
            "matches": {
                "processed": cls.processed_matches,
            }
        }

# ======== GLOBAL EXCEPTION HANDLING ========
# Import core modules needed for exception handling
try:
    import sys
    import threading
    import traceback
    import asyncio  # Import asyncio early to ensure exception handler is set up
    
    # Global exception handler for main process
    def _handle_exception(exc_type, exc_value, exc_tb):
        """Handle uncaught exceptions in the main thread"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        
        tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        error_msg = f"❌ LIVE.PY CRASH: {exc_value}"
        print(error_msg)
        print(tb)
        
        # Direct import attempt - TELEGRAM_AVAILABLE isn't defined yet
        try:
            from telegram import send_system_alert
            send_alert_with_backpressure(error_msg, alert_type="critical", error_details=tb)
        except Exception as alert_err:
            print(f"⚠️ Could not send Telegram alert: {alert_err}")
        
        # Allow cleanup hooks to run before exit
        print("Scheduling shutdown in 1 second to allow cleanup...")
        import threading
        threading.Timer(1.0, lambda: os._exit(1)).start()
    
    # Thread exception handler
    def _handle_thread_exception(args):
        """Handle uncaught exceptions in worker threads"""
        error_msg = f"❌ Thread '{args.thread.name}' crashed: {args.exc_value}"
        tb = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        print(error_msg)
        print(tb)
        
        # For thread exceptions, we can check TELEGRAM_AVAILABLE since it will be defined by the time threads are running
        if 'TELEGRAM_AVAILABLE' in globals() and TELEGRAM_AVAILABLE:
            try:
                from telegram import send_system_alert
                send_alert_with_backpressure(error_msg, alert_type="error", error_details=tb)  # Downgraded from critical as thread errors may not be fatal
            except Exception as alert_err:
                print(f"⚠️ Could not send Telegram alert: {alert_err}")
    
    # Asyncio exception handler
    def _handle_asyncio_exception(loop, context):
        """Handle uncaught exceptions in asyncio tasks"""
        error_msg = f"❌ Asyncio error: {context.get('exception') or context.get('message')}"
        exc = context.get('exception')
        tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__)) if exc else str(context)
        print(error_msg)
        print(tb)
        
        # For asyncio exceptions, we can check TELEGRAM_AVAILABLE since it will be defined by the time tasks are running
        if 'TELEGRAM_AVAILABLE' in globals() and TELEGRAM_AVAILABLE:
            try:
                from telegram import send_system_alert
                send_alert_with_backpressure(error_msg, alert_type="error", error_details=tb)  # Downgraded from critical as task errors may not be fatal
            except Exception as alert_err:
                print(f"⚠️ Could not send Telegram alert: {alert_err}")
    
    # Install exception hooks
    sys.excepthook = _handle_exception
    threading.excepthook = _handle_thread_exception
    
    # Automatically enable uvloop for ~2-3x better async performance if available
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        print("✓ uvloop enabled for improved async performance")
    except ImportError:
        pass  # uvloop not installed, continuing with standard loop
    
    # Install asyncio exception handler - do this directly after threading hook
    # We do this once here, early in the startup process, and never again
    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(_handle_asyncio_exception)
        print("✓ Asyncio exception handler installed")
    except Exception as e:
        print(f"❌ CRITICAL: Could not setup asyncio exception handler: {e}")
        # Allow cleanup hooks to run before exit
        print("Scheduling shutdown in 1 second to allow cleanup...")
        threading.Timer(1.0, lambda: os._exit(1)).start()
        # We won't try again - if we can't set it up now, it likely won't work later either
    
    # Patch asyncio.run to ensure any new loops also get our exception handler
    original_asyncio_run = asyncio.run
    def patched_asyncio_run(coro, **kwargs):
        try:
            return original_asyncio_run(coro, **kwargs)
        except Exception as e:
            # Handle any exceptions that might escape asyncio.run
            _handle_exception(type(e), e, e.__traceback__)
            return None
    
    # Replace the standard asyncio.run with our patched version
    asyncio.run = patched_asyncio_run
    print("✓ Patched asyncio.run to ensure all loops use our exception handler")

except Exception as e:
    print(f"⚠️ Failed to set up exception handlers: {e}")
    # Continue running even if exception handlers fail

# Concurrency limiter for back-pressure management
# This prevents unbounded queuing when downstream systems slow down
# Using threading.Semaphore instead of asyncio.Semaphore for sync code compatibility
ALERT_SEMAPHORE = threading.Semaphore(ALERT_SEMAPHORE_SIZE)  # Max pending alert operations (from env var)
DB_SEMAPHORE = threading.Semaphore(DB_SEMAPHORE_SIZE)        # Max pending DB operations (from env var)

# Helper function for sending alerts with back-pressure management
def send_alert_with_backpressure(message: str, alert_type: str = "info", error_details: str = None) -> None:
    """Send alerts with back-pressure control using semaphores"""
    if not TELEGRAM_AVAILABLE:
        return
        
    # Use a thread-safe approach that works in both sync and async contexts
    try:
        # Non-blocking acquire - skip if at capacity
        if hasattr(ALERT_SEMAPHORE, '_value') and ALERT_SEMAPHORE._value > 0:
            ALERT_SEMAPHORE.acquire(blocking=False)
            try:
                from telegram import send_system_alert
                send_system_alert(message, alert_type=alert_type, error_details=error_details)
                # Track alert metrics
                Metrics.alerts_sent += 1
            finally:
                ALERT_SEMAPHORE.release()
        elif VERBOSE_OUTPUT:
            print("Skipping alert due to back-pressure (too many concurrent alerts)")
        Metrics.alerts_skipped += 1
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"⚠️ Failed to send alert: {e}")
    return

# ======== CORE IMPORTS ========
# These are essential and failure should be caught by the global hook
import os
# sys, traceback, threading, and asyncio already imported in the global handler section
# Use faster JSON serialization if available
try:
    import orjson as _json
    json_dumps = lambda obj: _json.dumps(obj, option=_json.OPT_SERIALIZE_NUMPY).decode()
    print("✓ Using orjson for improved serialization performance")
except ImportError:
    import json as _json
    json_dumps = lambda obj: _json.dumps(obj, separators=(',',':'))

# Maintain standard json module for compatibility with existing code
import json
# time already imported in the global handler section
import argparse
import datetime
import pytz
import signal
import fcntl
import atexit
import requests
import functools  # For performance optimizations
import re         # For regex optimizations

# Pre-compile regex patterns for use in hot path functions
WIND_VALUE_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)m/s")
WEATHER_VALUE_PATTERN = re.compile(r"([0-9]+(?:\.[0-9]+)?)°C")

# Add project to path with error handling
try:
    project_path = '/root/CascadeProjects/sports_bot'
    # Define PROJECT_PATH as global variable for use throughout the script
    PROJECT_PATH = project_path
    sys.path.append(project_path)
    # Verify the path was actually added
    if project_path in sys.path:
        print("✓ Added project root to sys.path")
    else:
        raise RuntimeError("Path addition verified but not found in sys.path")
except Exception as e:
    # This is truly critical as imports will fail without the correct path
    error_msg = f"CRITICAL: Failed to modify sys.path: {e}"
    print(f"❌ {error_msg}")
    # Don't check TELEGRAM_AVAILABLE here since it hasn't been set yet
    # Just try to import and send directly
    try:
        from telegram import send_system_alert
        # This is correctly marked as critical since it's a fatal startup error
        send_system_alert(
            error_msg, 
            alert_type="critical", 
            error_details=str(e)
        )
    except Exception as alert_err:
        print(f"❌ Could not send Telegram alert: {alert_err}")

# Make Supabase optional - system will run even if connection fails
try:
    from supabase_config import supabase
    SUPABASE_AVAILABLE = True
    print("✓ Supabase connection established")
except Exception as e:
    print(f"❌ ERROR: Supabase connection failed: {e}")
    print("⚠️ Running with limited functionality - database features disabled")
    supabase = None
    SUPABASE_AVAILABLE = False
    # Import telegram only after failure to avoid circular imports
    try:
        from telegram import send_system_alert
        send_alert_with_backpressure(
            f"Supabase connection failed. Sports bot running with limited functionality.", 
            alert_type="error",
            error_details=str(e)
        )
    except Exception as alert_error:
        print(f"⚠️ Could not send Telegram alert for Supabase failure: {alert_error}")

print("🔍 DEBUG — CWD:", os.getcwd())
print("🔍 DEBUG — PYTHONPATH:", os.getenv("PYTHONPATH"))

# Run system module verification - this sends alerts for failures but allows the program to continue
try:
    from football.alerts import verify_system
    print("Running system module verification...")
    verify_system()
    print("System verification completed")
except Exception as e:
    print(f"⚠️ System verification error: {e} - continuing anyway")
    # We continue even if verification itself fails

"""
Sports Bot - Live Match Processing System

# ========== LEFT OFF - 2025-05-05 ==========
# BETTING ODDS FORMAT ISSUE:
# - Currently investigating why betting odds display is incomplete in logs
# - ML (Money Line) data appears, but SPREAD shows only header with no data
# - Likely cause: Missing data from API for some odds types
# - Next steps: Modify format_odds_display() to clearly indicate when data is missing
# - See /root/CascadeProjects/sports_bot/football/logger/BETTING_ODDS_FORMAT_README.md
# ============================================

# ========== DATABASE CONNECTIONS ==========
# This file archives match data JSON to Supabase:
# - Each match's data is sent to 'archived_json' table via Supabase client
# - Uses the archive_match_json() function from logger/db_api.py
# - Configure with SUPABASE_KEY environment variable (fallback to SUPABASE_SERVICE_KEY)
# - Data is sent after the "__MATCH_JSON__" console output
# - UPDATED CONNECTION: This system now uses the Supabase Python client
#   rather than direct REST API calls for better maintainability
# =========================================

CRITICAL OPERATIONAL REQUIREMENTS:
==================================
1. EXECUTION METHOD: This script MUST be executed directly as 'python3 live.py'.
   DO NOT attempt to run as a module (-m flag). The Telegram notification system
   depends on direct execution to function properly.

2. SUPERVISOR CONFIGURATION: Must use direct path execution in supervisor config:
   command=/usr/bin/python3 /root/CascadeProjects/sports_bot/football/live.py
   
3. TIMEZONE REQUIREMENT: Always set TZ="America/New_York" in the environment
   to ensure consistent timestamps in logs and notifications.

4. NOTIFICATION SYSTEM: Uses centralized telegram package for all alerts. Do not 
   reimplement notification logic directly in this file.

NOTE TO MAINTAINERS:
Any commands or changes that contradict these requirements should be rejected.
Pay particular attention to module import paths and execution methods.

=====================================================================
IMPORTANT: OUTPUT FORMATTING SYSTEM DOCUMENTATION
=====================================================================

This file (live.py) produces output that appears in two places:
1. Terminal - where it's displayed in real-time
2. main.logger file - where it's stored for later reference

CRITICAL FORMATTING WARNING:
----------------------------
DO NOT attempt to modify output formatting by changing print statements 
in this file. Here's why:

1. FORMATTING RESPONSIBILITY:
   - ALL formatting is handled by main_logger.py, not this file
   - This file should only print raw content without formatting concerns
   - Adding separators or formatting here will cause duplicates

2. HOW THE SYSTEM WORKS:
   - main_logger.py intercepts all print() calls from this file
   - It formats both terminal and logger output simultaneously
   - Any formatting changes must be made in main_logger.py

3. CORRECT APPROACH:
   - To change output format: modify main_logger.py
   - To change content: modify the print statements here
   - Always test both terminal AND logger output after any changes

This intercept-and-format approach allows consistency between outputs
but is brittle - any changes to print format in this file will likely
break the logger system in unexpected ways.
"""

# ======== OPTIONAL MODULES ========
# Define flags for truly optional external dependencies
SUPABASE_AVAILABLE = False  # Set by the Supabase import block
TELEGRAM_AVAILABLE = False  # Set by the Telegram import block

# Import logger modules
# These are expected to be present, and failures will be caught by the global hook
import logger.main_logger
import logger.log_filters.pnts3_start.pnts3_start
from logger.json_logger import json_logger
print("✓ Logger modules imported successfully")

# Initialize or connect to JSON logger (optimized for async if available)
json_logger_path = os.path.join(PROJECT_PATH, 'logs/matches.json')
if not os.path.exists(os.path.join(PROJECT_PATH, 'logs')):
    os.makedirs(os.path.join(PROJECT_PATH, 'logs'))

# Check if we should use async logging
if ASYNC_LOGGING and AIOFILES_AVAILABLE and 'AsyncJsonLogger' in globals():
    # Create async json logger
    async_json_logger = AsyncJsonLogger(json_logger_path)
    # Start the async logger worker in the event loop
    if asyncio._get_running_loop() is not None:
        asyncio.create_task(async_json_logger.start_worker())
    else:
        # We need a running event loop to start the worker
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(async_json_logger.start_worker())
    json_logger = async_json_logger  # Use our async logger
    if VERBOSE_OUTPUT:
        print("✓ Using async file I/O for JSON logging")
else:
    # Fallback to standard logger
    from logger.main_logger import get_logger
    json_logger = get_logger('match_json', log_file=json_logger_path)

# Import telegram notifier functions - this is truly optional
try:
    from telegram import send_message, send_alert, send_match_alert, send_system_alert
    TELEGRAM_AVAILABLE = True
    print("✓ Telegram notification system initialized")
except Exception as e:
    print(f"⚠️ Telegram import failed: {e}")
    print("⚠️ Running without Telegram notification capability")

# Import performance monitoring - optional module
try:
    from tools.monitor_live import start_monitoring_thread
    # Start performance monitoring in background thread
    monitor_thread = start_monitoring_thread()
    print("Performance monitoring started in background")
except ImportError:
    print("Performance monitoring module not found - continuing without monitoring")

# Import asyncio-related modules
try:
    # asyncio should be imported already by the global error handler setup
    import aiohttp
    print("✓ Core async libraries imported successfully")
except Exception as e:
    # This is critical as the application cannot function without aiohttp
    error_msg = f"CRITICAL: Async library import failed: {e}"
    print(f"❌ {error_msg}")
    # We don't need to set up the async handler again - it's already done at the top of the file
    # Don't check TELEGRAM_AVAILABLE - just try the import directly
    try:
        from telegram import send_system_alert
        send_alert_with_backpressure(error_msg, alert_type="critical", error_details=str(e))
    except Exception as alert_err:
        print(f"❌ Could not send Telegram alert: {alert_err}")
# Removed the second import of supabase from logger.db_api

# Record when the script started
START_TIME = datetime.datetime.now()
# Set metrics startup time
Metrics.startup_time = START_TIME

# API credentials
USER = "thenecpt"
SECRET = "0c55322e8e196d6ef9066fa4252cf386"

# Define standard datetime formats as constants
DATE_FORMAT = "%m/%d/%Y"
TIME_FORMAT = "%I:%M:%S %p ET"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
CONSOLE_TIME_FORMAT = "%I:%M:%S %p ET"  # For console output only
API_DATETIME_FORMAT = "%m/%d/%Y %I:%M:%S %p ET"  # For APIs and data

def generate_match_summary_text(match_data, formatted_odds):
    lines = []
    lines.append(f"MATCH #{match_data['_loop_index']} OF {match_data['_total_matches']}")
    lines.append("\n----- MATCH SUMMARY -----")
    lines.append(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
    lines.append(f"Match ID: {match_data['id']}")
    lines.append(f"Competition ID: {match_data['competition_id']}")
    lines.append(f"Competition: {match_data['competition']} ({match_data['country']})")
    lines.append(f"Match: {match_data['home_team']} vs {match_data['away_team']}")
    lines.append(f"Score: {match_data['home_score']} - {match_data['away_score']} (HT: {match_data.get('home_ht_score','')} - {match_data.get('away_ht_score','')})")
    lines.append(f"Status: {match_data['status']} (Status ID: {match_data['status_id']})")

    if formatted_odds:
        lines.append("\n--- MATCH BETTING ODDS ---")
        for l in format_odds_display(formatted_odds).split("\n"):
            lines.append(l)

    lines.append("\n--- MATCH ENVIRONMENT ---")
    env = []
    if match_data.get("weather"):     env.append(f"Weather: {match_data['weather']}")
    if match_data.get("temperature"): env.append(f"Temperature: {match_data['temperature']}")
    if match_data.get("humidity"):    env.append(f"Humidity: {match_data['humidity']}")
    if match_data.get("wind"):        env.append(f"Wind: {match_data['wind']}")
    lines.extend(env or ["No environment data available for this match"])

    return "\n".join(lines)

async def _fetch_json(session: aiohttp.ClientSession, url: str, params: dict) -> dict:
    """
    Helper function to fetch JSON data from an API endpoint
    """
    # More robust fetch with retries and better error handling
    retries = MAX_RETRIES  # From environment variable
    last_error = None
    
    # Track API metrics
    Metrics.api_requests += 1
    
    for attempt in range(retries):
        try:
            if attempt > 0:
                Metrics.api_retries += 1
                if VERBOSE_OUTPUT:
                    print(f"Retry attempt {attempt} for {url}")
                
            async with session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    error_text = await resp.text()
                    raise Exception(f"HTTP {resp.status}: {error_text[:100]}")
                    
        except Exception as e:
            last_error = e
            # Exponential backoff between retries
            if attempt < retries - 1:
                # Use configurable backoff factor
                await asyncio.sleep(RETRY_BACKOFF ** attempt)
    
    # If we get here, all retries failed
    Metrics.api_failures += 1
    raise Exception(f"Failed after {retries} attempts: {last_error}")

async def fetch_live_matches(session):
    """
    Fetch all live football matches from the API
    """
    print("Fetching live matches...")
    return await _fetch_json(session, 
                             "https://api.thesports.com/v1/football/match/detail_live",
                             {"user": USER, "secret": SECRET})

async def fetch_match_details(session, match_id):
    """
    Fetch detailed information for a specific match ID
    """
    return await _fetch_json(session, 
                             "https://api.thesports.com/v1/football/match/recent/list",
                             {"user": USER, "secret": SECRET, "uuid": match_id})

async def fetch_match_odds(session, match_id):
    """
    Fetch odds history for a specific match ID
    """
    return await _fetch_json(session, 
                             "https://api.thesports.com/v1/football/odds/history",
                             {"user": USER, "secret": SECRET, "uuid": match_id})

async def fetch_team_info(session, team_id):
    """
    Fetch team information using the team ID (cached)
    """
    return await _fetch_json(session, 
                             "https://api.thesports.com/v1/football/team/additional/list",
                             {"user": USER, "secret": SECRET, "uuid": team_id})

async def fetch_competition_info(session, competition_id):
    """
    Fetch competition information using the competition ID (cached)
    """
    return await _fetch_json(session, 
                             "https://api.thesports.com/v1/football/competition/additional/list",
                             {"user": USER, "secret": SECRET, "uuid": competition_id})

async def fetch_country_data(session):
    """
    Fetch all country data
    """
    print("Fetching country data...")
    return await _fetch_json(session, 
                             "https://api.thesports.com/v1/football/country/list",
                             {"user": USER, "secret": SECRET})

def extract_match_ids(matches_data):
    """
    Extract all match IDs from the live matches data
    """
    match_ids = []
    
    if not matches_data or "results" not in matches_data:
        return match_ids
    
    for match in matches_data["results"]:
        if "id" in match:
            match_ids.append(match["id"])
    
    return match_ids

def extract_team_name(team_data):
    """
    Extract team name from team data
    """
    if not team_data or "code" not in team_data or team_data["code"] != 0:
        return "Unknown Team"
    
    if "results" not in team_data or not team_data["results"]:
        return "Unknown Team"
    
    team_results = team_data["results"]
    team = team_results[0] if isinstance(team_results, list) and team_results else team_results
    
    return team.get("name", "Unknown Team")

def extract_competition_info(competition_data):
    """
    Extract competition name and country ID from competition data
    """
    competition_name = "Unknown Competition"
    country_id = ""
    
    if not competition_data or "code" not in competition_data or competition_data["code"] != 0:
        return competition_name, country_id
    
    if "results" not in competition_data or not competition_data["results"]:
        return competition_name, country_id
    
    comp_results = competition_data["results"]
    comp = comp_results[0] if isinstance(comp_results, list) and comp_results else comp_results
    
    competition_name = comp.get("name", "Unknown Competition")
    
    # Extract country ID if available
    # Check different possible locations for country ID
    if "country_id" in comp:
        country_id = comp.get("country_id", "")
    elif "country" in comp and comp["country"]:
        if isinstance(comp["country"], dict):
            country_id = comp["country"].get("id", "")
        else:
            country_id = comp["country"]
    
    return competition_name, country_id

def create_country_id_to_name_map(country_data):
    """
    Create a dictionary mapping country IDs to country names
    """
    country_map = {}
    
    if not country_data or "code" not in country_data or country_data["code"] != 0:
        return country_map
    
    if "results" not in country_data or not country_data["results"]:
        return country_map
    
    for country in country_data["results"]:
        if "id" in country and "name" in country:
            country_map[country["id"]] = country["name"]
    
    return country_map

def get_weather_description(weather_code):
    """
    Convert numeric weather code to a human-readable description
    """
    weather_codes = {
        "1": "Partially cloudy",
        "2": "Cloudy",
        "3": "Foggy",
        "4": "Rainy",
        "5": "Sunny",
        "6": "Snowy",
        "7": "Windy"
    }
    
    # Handle both string and integer codes
    if isinstance(weather_code, str) and weather_code.isdigit():
        code = weather_code
    elif isinstance(weather_code, int):
        code = str(weather_code)
    else:
        code = str(weather_code)
    
    return weather_codes.get(code, f"Unknown ({code})")

@functools.lru_cache(maxsize=32)
def celsius_to_fahrenheit(celsius_str):
    """
    Convert celsius temperature string to fahrenheit
    Cached for improved performance on repeated lookups
    """
    try:
        # Extract numeric part from temperature string (e.g., "20°C" -> "20")
        celsius_value = float(celsius_str.replace('°C', '').strip())
        # Convert to Fahrenheit: F = (C * 9/5) + 32
        fahrenheit_value = (celsius_value * 9/5) + 32
        return f"{fahrenheit_value:.1f}°F"
    except (ValueError, AttributeError):
        return celsius_str  # Return original if conversion fails

@functools.lru_cache(maxsize=32)
def meters_per_second_to_mph(mps_str):
    """
    Convert wind speed from m/s to mph
    Cached for improved performance on repeated lookups
    """
    try:
        # Use precompiled regex to extract numeric part (e.g., "2.0m/s" -> "2.0")
        match = WIND_VALUE_PATTERN.search(mps_str)
        if match:
            wind_value = match.group(1)
        else:
            # Fallback to old method if regex doesn't match
            wind_value = mps_str.replace("m/s", "").strip()
            
        wind_ms = float(wind_value)
        wind_mph = wind_ms * 2.237
        return f"{wind_value}m/s ({wind_mph:.1f} mph)"
    except (ValueError, AttributeError):
        return mps_str  # Return original if conversion fails

def decimal_to_american(decimal_odds):
    """
    Convert decimal odds to American odds (int value)
    For odds > 2.0: (decimal - 1) * 100
    For odds < 2.0: -100 / (decimal - 1)
    """
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds == 0:
            return 0
        
        if decimal_odds >= 2.0:
            return int(round((decimal_odds - 1) * 100))
        else:
            return int(round(-100 / (decimal_odds - 1)))
    except (ValueError, ZeroDivisionError):
        return 0

def decimal_to_american_str(decimal_odds):
    """
    Convert decimal odds to American odds with + or - prefix
    """
    try:
        decimal_odds = float(decimal_odds)
        if decimal_odds == 0:
            return "0"
            
        if decimal_odds >= 2.0:
            return f"+{int(round((decimal_odds - 1) * 100))}"
        else:
            return f"{int(round(-100 / (decimal_odds - 1)))}"
    except (ValueError, ZeroDivisionError):
        return "0"

def hk_to_american(hk_odds):
    """
    Convert Hong Kong odds to American odds (int value)
    """
    try:
        hk_odds = float(hk_odds)
        if hk_odds >= 1:
            return int(round(hk_odds * 100))
        else:
            return int(round(-100 / hk_odds))
    except (ValueError, ZeroDivisionError):
        return 0

def hk_to_american_str(hk_odds):
    """
    Convert Hong Kong odds to American odds with + or - prefix
    """
    try:
        hk_odds = float(hk_odds)
        if hk_odds >= 1:
            return f"+{int(round(hk_odds * 100))}"
        else:
            return f"{int(round(-100 / hk_odds))}"
    except (ValueError, ZeroDivisionError):
        return "0"

def format_match_odds(odds_data):
    """
    Format the odds data according to the required structure:
    - SPREAD (Asia handicap)
    - ML (European odds)
    - Over/Under (Big Small)
    
    Filter all odds types to only include minutes 4-6
    """
    if not odds_data or "code" not in odds_data or odds_data["code"] != 0:
        return {}
    
    if "results" not in odds_data:
        return {}
    
    formatted_odds = {
        "SPREAD": [],
        "ML": [],
        "Over/Under": []
    }
    
    # Handle the case where results is a dictionary rather than a list
    results = odds_data["results"]
    
    # The structure is {"results": {"bookmaker_id": {"odds_type": [odds_entries]}}}
    for bookmaker_id, bookmaker_data in results.items():
        # Process Asia handicap (SPREAD)
        if "asia" in bookmaker_data:
            target_minutes_entries = []
            other_entries = []
            
            for asia_entry in bookmaker_data["asia"]:
                if len(asia_entry) >= 5:
                    time_of_match = asia_entry[1] if asia_entry[1] else "pre-match"
                    home_win_hk = asia_entry[2]
                    handicap = asia_entry[3]
                    away_win_hk = asia_entry[4]
                    
                    spread_entry = {
                        "time_of_match": time_of_match,
                        "home_win": hk_to_american(home_win_hk),
                        "handicap": handicap,
                        "away_win": hk_to_american(away_win_hk)
                    }
                    
                    # Check if time_of_match is numeric
                    try:
                        minute = int(time_of_match) if time_of_match.isdigit() else 0
                        # Only include minutes 4-6 as requested
                        if minute >= 4 and minute <= 6:
                            target_minutes_entries.append(spread_entry)
                        else:
                            other_entries.append(spread_entry)
                    except (ValueError, TypeError):
                        # Not a numeric minute, add to other entries
                        other_entries.append(spread_entry)
            
            # Add target minutes entries if they exist (prioritized)
            if target_minutes_entries:
                formatted_odds["SPREAD"].extend(target_minutes_entries)
            # Otherwise add the other entries
            elif other_entries:
                formatted_odds["SPREAD"].extend(other_entries)
        
        # Process European odds (ML) - ONLY FOR BOOKMAKER 2
        if bookmaker_id == "2" and "eu" in bookmaker_data:
            target_minutes_entries = []
            other_entries = []
            
            for euro_entry in bookmaker_data["eu"]:
                if len(euro_entry) >= 5:
                    time_of_match = euro_entry[1] if euro_entry[1] else "pre-match"
                    home_win_decimal = float(euro_entry[2])  # Home win odds (decimal)
                    draw_decimal = float(euro_entry[3])      # Draw odds (decimal)
                    away_win_decimal = float(euro_entry[4])  # Away win odds (decimal)
                    
                    # Skip conversion if any odds value is exactly 1.0
                    if home_win_decimal == 1.0 or draw_decimal == 1.0 or away_win_decimal == 1.0:
                        continue
                    
                    # Directly apply the conversion formula
                    if home_win_decimal >= 2.0:
                        home_win = int(round((home_win_decimal - 1) * 100))
                    else:
                        home_win = int(round(-100 / (home_win_decimal - 1)))
                        
                    if draw_decimal >= 2.0:
                        draw = int(round((draw_decimal - 1) * 100))
                    else:
                        draw = int(round(-100 / (draw_decimal - 1)))
                        
                    if away_win_decimal >= 2.0:
                        away_win = int(round((away_win_decimal - 1) * 100))
                    else:
                        away_win = int(round(-100 / (away_win_decimal - 1)))
                    
                    ml_entry = {
                        "time_of_match": time_of_match,
                        "home_win": home_win,
                        "draw": draw,
                        "away_win": away_win
                    }
                    
                    # Check if time_of_match is numeric
                    try:
                        minute = int(time_of_match) if time_of_match.isdigit() else 0
                        # Only include minutes 4-6 as requested
                        if minute >= 4 and minute <= 6:
                            target_minutes_entries.append(ml_entry)
                        else:
                            other_entries.append(ml_entry)
                    except (ValueError, TypeError):
                        # Not a numeric minute, add to other entries
                        other_entries.append(ml_entry)
                        
            # Add target minutes entries if they exist (prioritized)
            if target_minutes_entries:
                formatted_odds["ML"].extend(target_minutes_entries)
            # Otherwise add the other entries
            elif other_entries:
                formatted_odds["ML"].extend(other_entries)
        
        # Process Big Small (Over/Under)
        if "bs" in bookmaker_data:
            target_minutes_entries = []
            other_entries = []
            
            for bs_entry in bookmaker_data["bs"]:
                if len(bs_entry) >= 5:
                    time_of_match = bs_entry[1] if bs_entry[1] else "pre-match"
                    over_hk = bs_entry[2]
                    points_total = bs_entry[3]
                    under_hk = bs_entry[4]
                    
                    ou_entry = {
                        "time_of_match": time_of_match,
                        "over": hk_to_american(over_hk),
                        "handicap": points_total,
                        "under": hk_to_american(under_hk)
                    }
                    
                    # Check if time_of_match is numeric
                    try:
                        minute = int(time_of_match) if time_of_match.isdigit() else 0
                        # Only include minutes 4-6 as requested
                        if minute >= 4 and minute <= 6:
                            target_minutes_entries.append(ou_entry)
                        else:
                            other_entries.append(ou_entry)
                    except (ValueError, TypeError):
                        # Not a numeric minute, add to other entries
                        other_entries.append(ou_entry)
            
            # Add target minutes entries if they exist (prioritized)
            if target_minutes_entries:
                formatted_odds["Over/Under"].extend(target_minutes_entries)
            # Otherwise add the other entries
            elif other_entries:
                formatted_odds["Over/Under"].extend(other_entries)
    
    return formatted_odds

def get_latest_odds(odds_data, odds_type):
    """
    Get the latest odds entry for a specific odds type, prioritizing early game odds,
    with special handling for ML odds (minutes 4-6)
    """
    if not odds_data or odds_type not in odds_data or not odds_data[odds_type]:
        return None
    
    # For ML (Money Line), specifically prioritize minutes 4, 5, and 6
    if odds_type == "ML":
        # Find entries from minutes 4, 5, or 6 (specifically for ML odds)
        early_minutes = [entry for entry in odds_data[odds_type] 
                        if entry["time_of_match"] in ["4", "5", "6"]]
        
        # If we have early minute entries, return the latest one
        if early_minutes:
            return early_minutes[-1]
        
        # Otherwise return the latest entry
        return odds_data[odds_type][-1]
        
    # For SPREAD and Over/Under, filter entries to only include minutes 0-3 or minutes ≥ 7 (skip minutes 4-6)
    valid_entries = []
    for entry in odds_data[odds_type]:
        time_of_match = entry.get("time_of_match", "")
        try:
            # Try to convert to integer if it's a digit string
            if isinstance(time_of_match, str) and time_of_match.isdigit():
                minute = int(time_of_match)
                # Keep minutes 0-3 or minutes ≥ 7 (skip minutes 4-6)
                if minute <= 3 or minute >= 7:
                    valid_entries.append(entry)
            else:
                # Non-numeric time, add it
                valid_entries.append(entry)
        except (ValueError, TypeError):
            # Not convertible to integer, add it
            valid_entries.append(entry)
    
    # If no valid entries after filtering, return None
    if not valid_entries:
        return None
    
    # Separate early minutes (0-3) from other valid minutes
    early_minutes = [entry for entry in valid_entries 
                    if isinstance(entry.get("time_of_match", ""), str) 
                    and entry["time_of_match"].isdigit() 
                    and int(entry["time_of_match"]) <= 3]
    
    # If we have early minute entries, return the latest one
    if early_minutes:
        return early_minutes[-1]
    
    # Otherwise return the latest valid entry
    return valid_entries[-1]

def format_american_odds(odds_value):
    """Format American odds with consistent sign display."""
    return f"{odds_value:+d}"

def format_odds_display(formatted_odds):
    """
    Format the odds for display
    """
    if not formatted_odds:
        return "No odds data available"
    
    output_lines = []
    
    # Format ML (Money Line) - European odds
    if "ML" in formatted_odds and formatted_odds["ML"]:
        ml_entries = formatted_odds["ML"]
        
        # Sort by time to find the closest entries to minutes 4-6
        # Convert time_of_match to int where possible for better sorting
        def get_time_value(entry):
            time_str = entry.get("time_of_match", "")
            try:
                if time_str.isdigit():
                    return int(time_str)
                return 1000  # Large number for non-numeric times
            except (ValueError, AttributeError):
                return 1000
                
        # Sort the entries by time
        ml_entries.sort(key=get_time_value)
        
        # Try to find an entry from minutes 4-6
        target_minutes = ["4", "5", "6"]
        ml_entry = None
        
        # First pass: check for exact match in minutes 4-6
        for entry in ml_entries:
            time_of_match = entry.get("time_of_match", "")
            if time_of_match in target_minutes:
                ml_entry = entry
                break
        
        # If no entry from minutes 4-6, find the closest minute
        if not ml_entry and ml_entries:
            # Create entries with numeric times and non-numeric times
            numeric_entries = []
            non_numeric_entries = []
            
            for entry in ml_entries:
                time_str = entry.get("time_of_match", "")
                if time_str.isdigit():
                    numeric_entries.append((int(time_str), entry))
                else:
                    non_numeric_entries.append(entry)
            
            # Find the closest numeric time to the target range (4-6)
            if numeric_entries:
                # Sort by distance to the target range (middle is 5)
                numeric_entries.sort(key=lambda x: min(abs(x[0] - 4), abs(x[0] - 5), abs(x[0] - 6)))
                ml_entry = numeric_entries[0][1]
            else:
                # If no numeric entries, use the first non-numeric entry
                ml_entry = non_numeric_entries[0] if non_numeric_entries else None
        
        if ml_entry:
            ml_time = ml_entry.get("time_of_match", "Unknown")
            ml_home_win = ml_entry.get("home_win", 0)
            ml_draw = ml_entry.get("draw", 0)
            ml_away_win = ml_entry.get("away_win", 0)
            
            # Add a note if this is not from the target minutes 4-6
            minutes_note = ""
            if ml_time not in target_minutes:
                minutes_note = f" (Closest time to minutes 4-6 available: {ml_time})"
            
            output_lines.append("ML (Money Line):")
            output_lines.append(f"Time: {ml_time} min | Home: {format_american_odds(ml_home_win)} | Draw: {format_american_odds(ml_draw)} | Away: {format_american_odds(ml_away_win)}{minutes_note}")
    
    # Display SPREAD (Asia handicap)
    if "SPREAD" in formatted_odds and formatted_odds["SPREAD"]:
        spread_entries = formatted_odds["SPREAD"]
        
        # Sort entries by time for finding closest match
        def get_time_value(entry):
            time_str = entry.get("time_of_match", "")
            try:
                if time_str.isdigit():
                    return int(time_str)
                return 1000  # Large number for non-numeric times
            except (ValueError, AttributeError):
                return 1000
                
        # Sort the entries by time
        spread_entries.sort(key=get_time_value)
        
        # Try to find an entry from minutes 4-6
        target_minutes = ["4", "5", "6"]
        spread_entry = None
        
        # First pass: check for exact match in minutes 4-6
        for entry in spread_entries:
            time_of_match = entry.get("time_of_match", "")
            if time_of_match in target_minutes:
                spread_entry = entry
                break
        
        # If no entry from minutes 4-6, find the closest minute
        if not spread_entry and spread_entries:
            # Create entries with numeric times and non-numeric times
            numeric_entries = []
            non_numeric_entries = []
            
            for entry in spread_entries:
                time_str = entry.get("time_of_match", "")
                if time_str.isdigit():
                    numeric_entries.append((int(time_str), entry))
                else:
                    non_numeric_entries.append(entry)
            
            # Find the closest numeric time to the target range (4-6)
            if numeric_entries:
                # Sort by distance to the target range (middle is 5)
                numeric_entries.sort(key=lambda x: min(abs(x[0] - 4), abs(x[0] - 5), abs(x[0] - 6)))
                spread_entry = numeric_entries[0][1]
            else:
                # If no numeric entries, use the first non-numeric entry
                spread_entry = non_numeric_entries[0] if non_numeric_entries else None
                
        if spread_entry:
            spread_time = spread_entry.get("time_of_match", "Unknown")
            home_odds = format_american_odds(spread_entry.get("home_win", 0))
            handicap = spread_entry.get("handicap", 0)
            away_odds = format_american_odds(spread_entry.get("away_win", 0))
            
            # Add a note if this is not from the target minutes 4-6
            minutes_note = ""
            if spread_time not in target_minutes:
                minutes_note = f" (Closest time to minutes 4-6 available: {spread_time})"
                
            output_lines.append("\nSPREAD (Asia Handicap):")
            output_lines.append(f"Time: {spread_time} min | Home: {home_odds} | Handicap: {handicap} | Away: {away_odds}{minutes_note}")
    
    # Display Over/Under
    if "Over/Under" in formatted_odds and formatted_odds["Over/Under"]:
        ou_entries = formatted_odds["Over/Under"]
        
        # Sort entries by time for finding closest match
        def get_time_value(entry):
            time_str = entry.get("time_of_match", "")
            try:
                if time_str.isdigit():
                    return int(time_str)
                return 1000  # Large number for non-numeric times
            except (ValueError, AttributeError):
                return 1000
                
        # Sort the entries by time
        ou_entries.sort(key=get_time_value)
        
        # Try to find an entry from minutes 4-6
        target_minutes = ["4", "5", "6"]
        ou_entry = None
        
        # First pass: check for exact match in minutes 4-6
        for entry in ou_entries:
            time_of_match = entry.get("time_of_match", "")
            if time_of_match in target_minutes:
                ou_entry = entry
                break
        
        # If no entry from minutes 4-6, find the closest minute
        if not ou_entry and ou_entries:
            # Create entries with numeric times and non-numeric times
            numeric_entries = []
            non_numeric_entries = []
            
            for entry in ou_entries:
                time_str = entry.get("time_of_match", "")
                if time_str.isdigit():
                    numeric_entries.append((int(time_str), entry))
                else:
                    non_numeric_entries.append(entry)
            
            # Find the closest numeric time to the target range (4-6)
            if numeric_entries:
                # Sort by distance to the target range (middle is 5)
                numeric_entries.sort(key=lambda x: min(abs(x[0] - 4), abs(x[0] - 5), abs(x[0] - 6)))
                ou_entry = numeric_entries[0][1]
            else:
                # If no numeric entries, use the first non-numeric entry
                ou_entry = non_numeric_entries[0] if non_numeric_entries else None
        
        if ou_entry:
            ou_time = ou_entry.get("time_of_match", "Unknown")
            over_odds = format_american_odds(ou_entry.get("over", 0))
            handicap = ou_entry.get("handicap", 0)
            under_odds = format_american_odds(ou_entry.get("under", 0))
            
            # Add a note if this is not from the target minutes 4-6
            minutes_note = ""
            if ou_time not in target_minutes:
                minutes_note = f" (Closest time to minutes 4-6 available: {ou_time})"
                
            output_lines.append("\nOver/Under:")
            output_lines.append(f"Time: {ou_time} min | Over: {over_odds} | Line: {handicap} | Under: {under_odds}{minutes_note}")
    
    return "\n".join(output_lines)

@functools.lru_cache(maxsize=32)
def get_status_description(status_id):
    """
    Convert numeric status_id to a human-readable description
    Cached for improved performance on repeated lookups
    """
    status_mapping = {
        "1": "Not started",
        "2": "First half",
        "3": "Half-time break",
        "4": "Second half",
        "5": "Extra time",
        "6": "Penalty shootout",
        "7": "Finished",
        "8": "Finished",
        "9": "Postponed",
        "10": "Canceled",
        "11": "To be announced",
        "12": "Interrupted",
        "13": "Abandoned",
        "14": "Suspended",
    }
    
    # Handle both string and integer status codes
    if isinstance(status_id, str) and status_id.isdigit():
        code = status_id
    elif isinstance(status_id, int):
        code = str(status_id)
    else:
        code = str(status_id)
    
    return status_mapping.get(code, f"Unknown (ID: {code})")

# Cache timezone object at module level to avoid repeated allocation
EASTERN = pytz.timezone('America/New_York') if 'pytz' in sys.modules else None

# Performance-critical helper functions
def get_eastern_time():
    """Convert current time to Eastern Time (ET) for standardized display"""
    return datetime.datetime.now(pytz.utc).astimezone(EASTERN)

def get_uptime_status():
    """Generate a formatted status message about the application's uptime"""
    now = datetime.datetime.now()
    uptime = now - START_TIME
    
    # Calculate hours, minutes, seconds
    hours, remainder = divmod(uptime.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    # Format the uptime string
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    # Convert START_TIME to Eastern Time
    eastern = pytz.timezone('America/New_York')
    utc_start = pytz.utc.localize(START_TIME.replace(tzinfo=None))
    start_time_et = utc_start.astimezone(eastern)
    
    # Format the message with HTML formatting for Telegram
    message = f"📊 <b>LIVE.PY STATUS REPORT</b>\n\n"
    message += f"• <b>Started at:</b> {start_time_et.strftime(API_DATETIME_FORMAT)}\n"
    message += f"• <b>Current uptime:</b> {uptime_str}\n"
    message += f"• <b>Running process ID:</b> {os.getpid()}\n"
    
    return message

def handle_sigusr1(signum, frame) -> None:
    """Signal handler for SIGUSR1 to report uptime status via Telegram"""
    # Include health metrics in the status report
    metrics_report = Metrics.get_health_report()
    status_message = get_uptime_status()
    
    # Add metrics to the status message
    status_message += "\n\n📊 <b>PERFORMANCE METRICS</b>\n"
    status_message += f"DB Operations: {metrics_report['database']['operations']} "
    status_message += f"(Success rate: {metrics_report['database']['success_rate']:.1%})\n"
    status_message += f"API Requests: {metrics_report['api']['requests']} "
    status_message += f"(Retry rate: {metrics_report['api']['retry_rate']:.1%})\n"
    status_message += f"Alerts sent: {metrics_report['alerts']['sent']}\n"
    status_message += f"Matches processed: {metrics_report['matches']['processed']}"
    
    if TELEGRAM_AVAILABLE:
        # Use thread-safe semaphore for alert sending
        send_alert_with_backpressure(status_message, "info")

def telegram_listener(token="7764953908:AAHMpJsw5vKQYPiJGWrj0PgDkztiIgY_dko", chat_id="6128359776"):
    """
    Background thread that listens for status requests from Telegram
    Processes /status commands sent to the bot
    """
    if not TELEGRAM_AVAILABLE:
        print("Telegram listener not started - Telegram module not available")
        return
        
    telegram_url = f"https://api.telegram.org/bot{token}/getUpdates"
    offset = None
    
    print(f"[Telegram Listener] Started with token: {token[:8]}... and chat_id: {chat_id}")
    
    while True:
        try:
            params = {
                "timeout": 30,
                "allowed_updates": ["message"]
            }
            
            if offset:
                params["offset"] = offset
            
            print(f"[Telegram Listener] Polling for updates with params: {params}")
            response = requests.get(telegram_url, params=params)
            
            if response.status_code == 200:
                updates = response.json()
                print(f"[Telegram Listener] Response: {json.dumps(updates)[:300]}...")
                
                if "result" in updates and updates["result"]:
                    print(f"[Telegram Listener] Received {len(updates['result'])} updates")
                    for update in updates["result"]:
                        # Update offset to acknowledge this update
                        offset = update["update_id"] + 1
                        print(f"[Telegram Listener] Processing update {update['update_id']}: {json.dumps(update)[:150]}...")
                        
                        # Check if this is a message with text
                        if "message" in update and "text" in update["message"]:
                            message_text = update["message"]["text"]
                            message_chat_id = str(update["message"]["chat"]["id"])
                            print(f"[Telegram Listener] Message: '{message_text}' from chat_id: {message_chat_id}, expected chat_id: {chat_id}")
                            
                            # Check if this is a status command from the configured chat
                            if message_text.lower() == "/status" and message_chat_id == chat_id:
                                print(f"[Telegram Listener] Status command received from authorized chat")
                                status_message = get_uptime_status()
                                print(f"[Telegram Listener] Sending status message: {status_message[:100]}...")
                                if TELEGRAM_AVAILABLE:
                                    send_alert_with_backpressure(status_message, "info")
                            else:
                                print(f"[Telegram Listener] Not a status command or unauthorized chat: '{message_text}' != '/status' or '{message_chat_id}' != '{chat_id}'")
                else:
                    print(f"[Telegram Listener] No updates in response")
            else:
                print(f"[Telegram Listener] Error: {response.status_code} - {response.text}")
            
            # Sleep to avoid hammering the API
            time.sleep(5)
            
        except Exception as e:
            print(f"[Telegram Listener] Error in Telegram listener: {e}")
            traceback.print_exc()
            # Sleep and continue on error
            time.sleep(10)

async def main_async():
    """
    Main async function to fetch live matches and print match details with team names and competition country
    """
    # Store the event loop globally for reuse during shutdown
    global MAIN_EVENT_LOOP, HTTP_SESSION
    MAIN_EVENT_LOOP = asyncio.get_running_loop()
    
    # Apply GC optimizations if enabled
    if GC_TUNING_ENABLED and 'gc' in globals():
        # Adjust GC thresholds for better performance in hot loops
        current = gc.get_threshold()
        gc.set_threshold(current[0]*3, current[1]*3, current[2]*3)
        if VERBOSE_OUTPUT:
            print(f"✓ Adjusted GC thresholds from {current} to {gc.get_threshold()}")
    
    # Parse command line arguments once at startup
    continuous_mode = True  # Default to continuous mode
    interval = DEFAULT_INTERVAL  # Default interval from environment variable
    parser = argparse.ArgumentParser(description='Live Football Match Monitor')
    parser.add_argument('-s', '--single', action='store_true', help='Run once and exit (default: run continuously)')
    parser.add_argument('-i', '--interval', type=int, help='Update interval in seconds (default: 30)')
    args = parser.parse_args()
    
    if args.single:
        continuous_mode = False
    if args.interval:
        interval = args.interval
    
    try:
        # Create the connector now that we have a running event loop
        if AIOHTTP_AVAILABLE:
            conn = aiohttp.TCPConnector(**CONN_PARAMS)
            timeout = aiohttp.ClientTimeout(**TIMEOUT_PARAMS)
            # Initialize the shared session for reuse across the application
            HTTP_SESSION = aiohttp.ClientSession(connector=conn, timeout=timeout)
            if VERBOSE_OUTPUT:
                print("✓ Created shared HTTP session with optimized parameters")
        
        # Use the shared HTTP session
        # Try to load country data from cache first if entity caching is enabled
        country_data = None
        if ENABLE_ENTITY_CACHE:
            cache_key = generate_cache_key('countries')
            country_data = load_entity_cache(cache_key)
            if country_data and VERBOSE_OUTPUT:
                print(f"✓ Loaded {len(country_data)} countries from cache")
        
        # Fetch from API if not in cache
        if not country_data:
            country_data = await fetch_country_data(HTTP_SESSION)
            if country_data and ENABLE_ENTITY_CACHE:
                save_entity_cache(cache_key, country_data)
            
        country_map = create_country_id_to_name_map(country_data)
            
        # Run the fetch process in a loop if continuous mode is enabled
        while True:
            await process_live_matches_async(HTTP_SESSION, country_map)
            
            if not continuous_mode:
                # If single-run mode, break after the first iteration
                break
                
            # Convert current time to Eastern Time (ET)
            eastern_now = get_eastern_time()
            
            # Use the logger for debug info instead of prints to avoid terminal output
            # when verbose mode is disabled
            if VERBOSE_OUTPUT:
                print(f"\nWaiting {interval} seconds before next update at {eastern_now.strftime(CONSOLE_TIME_FORMAT)}...")
                print(f"{'-' * 50}")
            
            # Wait for the next update cycle
            await asyncio.sleep(interval)
            
            if VERBOSE_OUTPUT:
                eastern_now = get_eastern_time()  # Update time after sleep
                print(f"\n{'=' * 50}")
                print(f"REFRESHING DATA AT: {eastern_now.strftime(CONSOLE_TIME_FORMAT)}")
                print(f"{'=' * 50}\n")
    
    except KeyboardInterrupt:
        print("\nLive match monitoring stopped by user.")
    except Exception as e:
        print(f"Error in main function: {e}")
        traceback.print_exc()
    finally:
        # Ensure we close the shared HTTP session
        if HTTP_SESSION and not HTTP_SESSION.closed:
            if VERBOSE_OUTPUT:
                print("Closing shared HTTP session...")
            try:
                asyncio.create_task(HTTP_SESSION.close())
            except:
                pass

async def process_live_matches_async(session, country_map):
    """
    Process live matches and display their details using async batch fetching
    """
    # Initialize batch array once at function start if batch inserts are enabled
    if ENABLE_BATCH_INSERTS:
        batch_matches = []
        # Track the last time we flushed the database batch
        if not hasattr(process_live_matches_async, 'last_db_flush_time'):
            process_live_matches_async.last_db_flush_time = time.time()
    
    # Fetch live matches
    if VERBOSE_OUTPUT:
        print("Fetching live matches data...")
    live_matches_data = await fetch_live_matches(session)
    if not live_matches_data or "results" not in live_matches_data:
        print("No live matches found.")
        # Add telegram alert for no matches found
        message = "⚠️ <b>ALERT: NO LIVE MATCHES FOUND</b>\n\nThe API returned no live matches, which is unusual and may indicate a problem with the API or the system. Please check the connection and API status."
        if TELEGRAM_AVAILABLE:
            send_alert_with_backpressure(message, "warning")
        # Don't return any value - just return control to the caller
        return None
    
    # Extract match IDs
    match_ids = extract_match_ids(live_matches_data)
    
    # Batch-fetch match details
    detail_tasks = [fetch_match_details(session, mid) for mid in match_ids]
    all_details = await asyncio.gather(*detail_tasks, return_exceptions=True)
    # Build lookup dictionary
    details_by_id = {mid: detail for mid, detail in zip(match_ids, all_details) 
                    if not isinstance(detail, Exception)}
    
    # Batch-fetch match odds for all matches
    odds_tasks = [fetch_match_odds(session, mid) for mid in match_ids]
    all_odds   = await asyncio.gather(*odds_tasks, return_exceptions=True)
    odds_by_id = {
        mid: odds
        for mid, odds in zip(match_ids, all_odds)
        if not isinstance(odds, Exception)
    }
    
    # Extract team and competition IDs from match details data instead of live data
    team_ids = set()
    competition_ids = set()
    
    # Process match details to extract IDs
    for match_id, details in details_by_id.items():
        if "results" not in details or not details["results"]:
            continue
            
        results = details["results"]
        match_detail = results[0] if isinstance(results, list) and results else results
        
        # Extract team and competition IDs
        home_team_id = match_detail.get("home_team_id", "")
        away_team_id = match_detail.get("away_team_id", "")
        competition_id = match_detail.get("competition_id", "")
        
        if home_team_id:
            team_ids.add(home_team_id)
        if away_team_id:
            team_ids.add(away_team_id)
        if competition_id:
            competition_ids.add(competition_id)
    
    team_tasks = [fetch_team_info(session, tid) for tid in team_ids]
    team_results = await asyncio.gather(*team_tasks, return_exceptions=True)
    # Build team cache
    team_cache = {tid: result for tid, result in zip(team_ids, team_results) 
                 if not isinstance(result, Exception)}
    
    competition_tasks = [fetch_competition_info(session, cid) for cid in competition_ids]
    competition_results = await asyncio.gather(*competition_tasks, return_exceptions=True)
    # Build competition cache
    competition_cache = {cid: result for cid, result in zip(competition_ids, competition_results) 
                        if not isinstance(result, Exception)}
    
    # Print a header with total matches found
    print(f"\n===== FOUND {len(match_ids)} LIVE FOOTBALL MATCHES =====\n")
    eastern_now = get_eastern_time()
    print(f"Last updated: {eastern_now.strftime(DATE_FORMAT)} {eastern_now.strftime(CONSOLE_TIME_FORMAT)}")
    # Update metrics
    Metrics.processed_matches += len(match_ids)
    Metrics.last_refresh = datetime.datetime.now()
    
    # Process each match in turn
    for i, match_id in enumerate(match_ids, 1):
        try:
            # Get match data from the live endpoint
            live_match_data = None
            for match in live_matches_data["results"]:
                if match["id"] == match_id:
                    live_match_data = match
                    break
            
            if not live_match_data:
                continue
            
            # Get match details from the batch-fetched data
            match_details_data = details_by_id.get(match_id)
            
            # Get match details from the response
            match_details = None
            if match_details_data and "results" in match_details_data and match_details_data["results"]:
                # Match details from recent/list endpoint may be in various formats
                if isinstance(match_details_data["results"], list):
                    match_details = match_details_data["results"][0]
                else:
                    match_details = match_details_data["results"]
            
            # Combine data from both endpoints
            match_data = live_match_data.copy()  # Start with live data
            
            # Add or override with details data if available
            if match_details:
                match_data.update({k: v for k, v in match_details.items() if k not in match_data or not match_data[k]})
            
            # Fetch team and competition info
            home_team_id = match_data.get("home_team_id", "")
            away_team_id = match_data.get("away_team_id", "")
            competition_id = match_data.get("competition_id", "")
            
            # Get team and competition info from caches
            home_team_info = team_cache.get(home_team_id) if home_team_id else None
            away_team_info = team_cache.get(away_team_id) if away_team_id else None
            competition_info = competition_cache.get(competition_id) if competition_id else None
            
            home_team_name = extract_team_name(home_team_info) if home_team_info else "Unknown Home Team"
            away_team_name = extract_team_name(away_team_info) if away_team_info else "Unknown Away Team"
            
            competition_name = extract_competition_info(competition_info)[0] if competition_info else "Unknown Competition"
            competition_country_id = extract_competition_info(competition_info)[1] if competition_info else None
            competition_country = country_map.get(competition_country_id, "Unknown Country")
            
            # Fetch odds data
            odds_data = odds_by_id.get(match_id)
            
            # Format the match odds
            formatted_odds = format_match_odds(odds_data)

            # ————————————————
            # Promote key odds fields into match_data
            # Over/Under
            ou_list = formatted_odds.get("Over/Under", [])
            if ou_list:
                first_ou = ou_list[0]
                ou_line  = first_ou.get("handicap")
                ou_over  = first_ou.get("over")
                ou_under = first_ou.get("under")
            else:
                ou_line = ou_over = ou_under = None

            # Money Line (ML)
            ml_list = formatted_odds.get("ML", [])
            if ml_list:
                first_ml = ml_list[0]
                ml_home = first_ml.get("home_win")
                ml_draw = first_ml.get("draw")
                ml_away = first_ml.get("away_win")
            else:
                ml_home = ml_draw = ml_away = None
            # ————————————————

            # Get environment data
            environment = match_data.get("environment", {})
            weather = environment.get("weather", "")
            temperature = environment.get("temperature", "")
            wind = environment.get("wind", "")
            humidity = environment.get("humidity", "")
            
            # Convert temperature from Celsius to Fahrenheit if available
            temperature_fahrenheit = ""
            if temperature:
                try:
                    temp_c = float(temperature)
                    temp_f = (temp_c * 9/5) + 32
                    temperature_fahrenheit = f"{temp_f:.1f}°F"
                except (ValueError, TypeError):
                    temperature_fahrenheit = ""
            
            # Process weather code to text description
            weather_text = get_weather_description(weather) if weather else ""
            
            # Convert wind speed from m/s to mph if available
            wind_mph = ""
            if wind:
                try:
                    # Extract numeric part from the wind string (remove "m/s" if present)
                    wind_value = wind.replace("m/s", "").strip()
                    wind_ms = float(wind_value)
                    wind_mph = f"{wind} ({wind_ms * 2.237:.1f} mph)"
                except (ValueError, TypeError):
                    wind_mph = wind
            
            # Format humidity with single %
            humidity_text = ""
            if humidity:
                # Remove any existing % sign and add a single one
                humidity_clean = str(humidity).replace("%", "").strip()
                humidity_text = f"{humidity_clean}%"
            
            # We're now only passing the match number to the logger system
            # without printing it directly, to avoid duplication
            # The logger will handle the printing with proper formatting
            print(f"MATCH #{i} OF {len(match_ids)}")
            
            # Print match summary
            print("\n----- MATCH SUMMARY -----")
            print(f"Timestamp: {get_eastern_time().strftime(API_DATETIME_FORMAT)}")
            print(f"Match ID: {match_id}")
            print(f"Competition ID: {competition_id}")
            print(f"Competition: {competition_name} ({competition_country})")
            print(f"Match: {home_team_name} vs {away_team_name}")
            
            # Extract scores from detail_live API format
            home_live_score = 0
            home_ht_score = 0
            away_live_score = 0
            away_ht_score = 0
            
            if "score" in match_data:
                score_data = match_data.get("score", [])
                if isinstance(score_data, list) and len(score_data) > 3:
                    # Home scores (index 2)
                    home_scores = score_data[2]
                    if isinstance(home_scores, list) and len(home_scores) > 1:
                        # Home live score (index 0)
                        if isinstance(home_scores[0], str) and " " in home_scores[0]:
                            home_live_score = home_scores[0].split(" ")[0]
                        else:
                            home_live_score = home_scores[0]
                        # Home half-time score (index 1)
                        if isinstance(home_scores[1], str) and " " in home_scores[1]:
                            home_ht_score = home_scores[1].split(" ")[0]
                        else:
                            home_ht_score = home_scores[1]
                    
                    # Away scores (index 3)
                    away_scores = score_data[3]
                    if isinstance(away_scores, list) and len(away_scores) > 1:
                        # Away live score (index 0)
                        if isinstance(away_scores[0], str) and " " in away_scores[0]:
                            away_live_score = away_scores[0].split(" ")[0]
                        else:
                            away_live_score = away_scores[0]
                        # Away half-time score (index 1)
                        if isinstance(away_scores[1], str) and " " in away_scores[1]:
                            away_ht_score = away_scores[1].split(" ")[0]
                        else:
                            away_ht_score = away_scores[1]
            
            # Print the updated score format
            print(f"Score: {home_live_score} - {away_live_score} (HT: {home_ht_score} - {away_ht_score})")
            
            # Print match status with status_id
            status_name = get_status_description(match_data.get('status_id', 'Unknown'))
            status_id = match_data.get('status_id', 'Unknown')
            print(f"Status: {status_name} (Status ID: {status_id})")
            
            # Print odds information first
            if formatted_odds:
                print("\n--- MATCH BETTING ODDS ---")
                print(format_odds_display(formatted_odds))
            
            # Print environment info after the odds
            if weather_text or temperature_fahrenheit or wind_mph or humidity_text:
                print("\n--- MATCH ENVIRONMENT ---")
                if weather_text:
                    print(f"Weather: {weather_text}")
                if temperature_fahrenheit:
                    print(f"Temperature: {temperature_fahrenheit}")
                if humidity_text:
                    print(f"Humidity: {humidity_text}")
                if wind_mph:
                    print(f"Wind: {wind_mph}")
            else:
                print("\n--- MATCH ENVIRONMENT ---")
                print("No environment data available for this match")
            
            # Log match data to file in JSON format for easier parsing by other tools
            match_data = {
                "id": match_id,
                "timestamp": get_eastern_time().strftime(API_DATETIME_FORMAT),
                "competition_id": competition_id,
                "competition": competition_name,
                "country": competition_country,
                "home_team": home_team_name,
                "away_team": away_team_name,
                "score": f"{home_live_score} - {away_live_score}",
                "status": status_name,
                "status_id": status_id,
                "odds": formatted_odds,

                # Promoted odds fields:
                "ou_line":  ou_line,
                "ou_over":  ou_over,
                "ou_under": ou_under,
                "ml_home":  ml_home,
                "ml_draw":  ml_draw,
                "ml_away":  ml_away,

                # Loop information for summary generation
                "_loop_index": i,
                "_total_matches": len(match_ids),
                "home_score": home_live_score,
                "away_score": away_live_score,
                "home_ht_score": home_ht_score if 'home_ht_score' in locals() else "",
                "away_ht_score": away_ht_score if 'away_ht_score' in locals() else "",

                "weather": weather_text,
                "humidity": humidity_text,
                "wind": wind_mph
            }
            
            # Only log detailed JSON in verbose mode or limit by rate
            if VERBOSE_OUTPUT or (i % JSON_LOG_RATE == 0):  # Log every Nth match based on config
                # Use optimized JSON serialization
                serialized_data = json_dumps(match_data)
                
                # Handle async vs synchronous logging
                if ASYNC_LOGGING and AIOFILES_AVAILABLE and isinstance(json_logger, AsyncJsonLogger):
                    # Queue for async writing to avoid blocking
                    asyncio.create_task(json_logger.debug(serialized_data))
                else:
                    # Use standard synchronous logger
                    json_logger.debug(serialized_data)

            # Insert into archived_json as before
            response = None

            # Store if we have a working Supabase connection
            if SUPABASE_AVAILABLE:
                try:
                    from supabase_config import supabase
                    
                    # Decide between single and batch inserts
                    if ENABLE_BATCH_INSERTS:
                        # Add to batch for bulk insert (we already initialized batch_matches at function start)
                        batch_matches.append(match_data)
                        
                        # Calculate time since last flush
                        time_since_flush = time.time() - process_live_matches_async.last_db_flush_time
                        
                        # Perform batch insert when:
                        # 1. We've collected enough records, OR
                        # 2. This is the last match, OR
                        # 3. It's been too long since last flush (time-based flushing)
                        if (len(batch_matches) >= DB_BATCH_SIZE or 
                            i == len(match_ids) or 
                            time_since_flush >= DB_FLUSH_INTERVAL):
                            if VERBOSE_OUTPUT:
                                print(f"Performing batch insert of {len(batch_matches)} records")
                                
                            # Use thread-safe semaphore for DB operations - don't peek at internal _value
                            acquired = DB_SEMAPHORE.acquire(blocking=False)
                            if acquired:
                                try:
                                    Metrics.db_operations += len(batch_matches)
                                    # Create the batch insert payload
                                    batch_payload = [{"raw_json": match} for match in batch_matches]
                                    response = supabase \
                                    .table("archived_json") \
                                    .insert(batch_payload) \
                                    .execute()
                                    Metrics.db_successes += len(batch_matches)
                                    # Clear the batch after successful insert
                                    batch_matches = []
                                except Exception as e:
                                    error_msg = f"Failed to batch insert {len(batch_matches)} matches: {str(e)}"
                                    if VERBOSE_OUTPUT:
                                        print(f"⚠️ {error_msg}")
                                    # Use our thread-safe helper function
                                    send_alert_with_backpressure(
                                        f"Batch database operation failed for {len(batch_matches)} matches",
                                        alert_type="warning",
                                        error_details=error_msg
                                    )
                                    Metrics.db_failures += len(batch_matches)
                                    # Fall back to individual inserts on batch failure
                                    if VERBOSE_OUTPUT:
                                        print("Falling back to individual inserts")
                                    for single_match in batch_matches:
                                        try:
                                            Metrics.db_operations += 1
                                            supabase.table("archived_json").insert({"raw_json": single_match}).execute()
                                            Metrics.db_successes += 1
                                        except Exception as e2:
                                            Metrics.db_failures += 1
                                            if VERBOSE_OUTPUT:
                                                print(f"Failed individual insert: {e2}")
                                    batch_matches = []
                                finally:
                                    DB_SEMAPHORE.release()
                            else:
                                # We couldn't acquire the semaphore, so we'll skip this batch
                                if VERBOSE_OUTPUT:
                                    print("Skipping batch DB insert due to back-pressure")
                                Metrics.db_skipped += len(batch_matches)
                    else:
                        # Traditional single-record insert
                        # Use thread-safe semaphore for DB operations
                        if hasattr(DB_SEMAPHORE, '_value') and DB_SEMAPHORE._value > 0:
                            acquired = DB_SEMAPHORE.acquire(blocking=False)
                            if acquired:
                                try:
                                    Metrics.db_operations += 1
                                    response = supabase \
                                    .table("archived_json") \
                                    .insert({"raw_json": match_data}) \
                                    .execute()
                                    Metrics.db_successes += 1
                                finally:
                                    DB_SEMAPHORE.release()
                            elif VERBOSE_OUTPUT:
                                print("Skipping DB insert due to back-pressure (too many concurrent operations)")
                            Metrics.db_skipped += 1
                        else:
                            # Fallback if _value not accessible - just try to execute
                            response = supabase \
                            .table("archived_json") \
                            .insert({"raw_json": match_data}) \
                            .execute()
                except Exception as e:
                    error_msg = f"Failed to insert match data: {str(e)}"
                    if VERBOSE_OUTPUT:
                        print(f"⚠️ {error_msg}")
                        
                    # Use our thread-safe helper function
                    send_alert_with_backpressure(
                        f"Database operation failed for match {match_data.get('id', 'unknown')}",
                        alert_type="warning",  # Downgraded from error as this is non-critical
                        error_details=error_msg
                    )
            else:
                # Fallback if _value not accessible - just try to execute
                response = supabase \
                .table("archived_json") \
                .insert({"raw_json": match_data}) \
                .execute()
    except Exception as e:
        error_msg = f"Failed to insert match data: {str(e)}"
        if VERBOSE_OUTPUT:
            print(f"⚠️ {error_msg}")

        # Use our thread-safe helper function
        send_alert_with_backpressure(
            f"Database operation failed for match {match_data.get('id', 'unknown')}",
            alert_type="warning",  # Downgraded from error as this is non-critical
            error_details=error_msg
        )
        # Track DB metrics
        Metrics.db_failures += 1
    
    # Check response status after all database operations
    if getattr(response, "error", None):
        print("   ❌ INSERT FAILED:", response.error, flush=True)
    elif response and hasattr(response, 'data') and response.data:
        print("   ✅ Inserted, DB row id:", response.data[0]["id"], flush=True)
    else:
        print("   ✅ Insert successful, but no response data available", flush=True)
                
                print("\n")
            except Exception as e:
                print(f"Error processing match {match_id}: {str(e)}")
                traceback.print_exc()
                continue
    
    # Print a footer
    print(f"{'=' * 50}")
    print(f"END OF LIVE MATCH DATA - {len(match_ids)} MATCHES DISPLAYED")
    print(f"{'=' * 50}")
    print(f"Refreshing in 30 seconds... (Press Ctrl+C to exit)")
    
    # Print a footer
    print(f"{'=' * 50}")
    print(f"END OF LIVE MATCH DATA - {len(match_ids)} MATCHES DISPLAYED")
    print(f"{'=' * 50}")
    print(f"Refreshing in 30 seconds... (Press Ctrl+C to exit)")

# Integration with automated testing
def run_smoke_test() -> bool:
    """Run smoke tests to verify critical functionality
    
    Returns True if all tests pass, False otherwise
    """
    try:
        from combined_failure_test import run_tests
        results = run_tests()
        return results['success']
    except Exception as e:
        print(f"Failed to run smoke tests: {e}")
        return False

# Health check endpoint for monitoring
def get_health_check() -> dict:
    """Return health check information for monitoring systems"""
    health = {
        "status": "healthy",
        "uptime_seconds": (datetime.datetime.now() - START_TIME).total_seconds() if 'START_TIME' in globals() else 0,
        "metrics": Metrics.get_health_report() if 'Metrics' in globals() else {}
    }
    
    # Add optimization flags
    health["optimizations"] = {
        "orjson": "_json" in globals() and globals()["_json"] != json,
        "uvloop": "uvloop" in sys.modules,
        "async_logging": ASYNC_LOGGING and AIOFILES_AVAILABLE,
        "batch_inserts": ENABLE_BATCH_INSERTS,
        "lru_cache": "functools" in sys.modules,
        "batch_size": DB_BATCH_SIZE if ENABLE_BATCH_INSERTS else None,
    }
    
    return health

if __name__ == "__main__":
    # Add profiling instrumentation if requested
    PROFILING_ENABLED = os.environ.get('SPORTS_BOT_ENABLE_PROFILING', 'false').lower() == 'true'
    if PROFILING_ENABLED:
        try:
            import cProfile
            profiler = cProfile.Profile()
            profiler.enable()
            print("✓ Profiling enabled - results will be saved at exit")
            
            # Register function to save profiling results
            def save_profile_results():
                """Save profiling results to a file"""
                if 'profiler' in globals():
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    profile_path = os.path.join(PROJECT_PATH, f'logs/profile_{timestamp}.prof')
                    profiler.disable()
                    profiler.dump_stats(profile_path)
                    print(f"\n✓ Profiling results saved to {profile_path}")
                    # Print top 10 functions by cumulative time
                    import pstats
                    from io import StringIO
                    s = StringIO()
                    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                    ps.print_stats(10)
                    print(s.getvalue())
                    
            atexit.register(save_profile_results)
        except ImportError:
            print("⚠️ Profiling requested but cProfile module not available")
    
    # Create a lock file to ensure only one instance runs at a time
    lock_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live.lock")
    lock_file = open(lock_file_path, "w")
    
    try:
        # Attempt to acquire an exclusive lock (will fail if another instance has the lock)
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(f"Acquired process lock. This is the only running instance.")
        
        # Logger is already initialized on import
        print("Main logger is active...")
        
        # Register signal handler for SIGUSR1
        signal.signal(signal.SIGUSR1, handle_sigusr1)
        
        # Send startup notification to Telegram
        startup_message = f"🚀 <b>LIVE.PY STARTED</b>\n\nThe live data collection system has been started successfully."
        if TELEGRAM_AVAILABLE:
            send_system_alert(startup_message, alert_type="info")
        
        # Register a cleanup handler to notify on shutdown
        import atexit
        # Define function to safely shutdown async logger
        def _shutdown_loggers():
            """Ensure async logger flushes all queued messages before exit"""
            if ASYNC_LOGGING and AIOFILES_AVAILABLE and 'json_logger' in globals():
                if isinstance(json_logger, AsyncJsonLogger):
                    try:
                        # Block briefly to let in-flight writes finish
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(json_logger.shutdown())
                        loop.close()
                        print("✓ Flushed async logger queues before exit")
                    except Exception as e:
                        print(f"Warning: Error during logger shutdown: {e}")
        
        def exit_handler():
            exit_message = f"⛔ <b>LIVE.PY STOPPED</b>\n\nThe live data collection system has been stopped."
            try:
                # First shutdown any async loggers to flush queued messages
                _shutdown_loggers()
                
                # Then send exit notifications and cleanup
                if TELEGRAM_AVAILABLE:
                    send_system_alert(exit_message, alert_type="info")
                
                # Release lock and close file
                fcntl.flock(lock_file, fcntl.LOCK_UN)
                lock_file.close()
                
                # Remove lock file on clean exit
                if os.path.exists(lock_file_path):
                    os.remove(lock_file_path)
            except Exception as e:
                print(f"Warning: Error during exit cleanup: {e}")
                # Continue exit process despite any errors
        atexit.register(exit_handler)
        
        # Start Telegram listener thread
        telegram_thread = threading.Thread(target=telegram_listener)
        telegram_thread.daemon = True  # Allow main thread to exit even if this thread is still running
        telegram_thread.start()
        
        asyncio.run(main_async())
        
    except IOError:
        print(f"Failed to acquire process lock. Another instance is already running.")
        print(f"If you're sure no other instance is running, delete the lock file: {lock_file_path}")
        sys.exit(1)