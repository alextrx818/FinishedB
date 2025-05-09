
import threading
import asyncio
import time

def raise_thread_error():
    """Raise an exception in a thread"""
    time.sleep(1)  # Give the system time to initialize
    print("🔥 SIMULATED ERROR: Raising exception in thread")
    raise Exception("COMBINED_TEST_THREAD_ERROR - This is an intentional test exception")

def schedule_async_error():
    """Schedule an asyncio task that will raise an exception"""
    async def async_error():
        await asyncio.sleep(2)  # Give a bit more time than the thread error
        print("🔥 SIMULATED ERROR: Raising exception in asyncio task")
        raise Exception("COMBINED_TEST_ASYNCIO_ERROR - This is an intentional test exception")
    
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(async_error())
    except Exception as e:
        print(f"Failed to schedule asyncio error: {e}")

def start_monitoring_thread():
    """Start a thread that will raise an exception"""
    # Create and start an error thread
    error_thread = threading.Thread(target=raise_thread_error, name="ErrorThread")
    error_thread.daemon = True
    error_thread.start()
    
    # Schedule an asyncio error
    schedule_async_error()
    
    print("✓ Error monitoring threads started")
    return True
