import random
import time
import sys
import logging
from collections import deque # Hint: This might be useful, but not used initially

# Configure logging to file
logging.basicConfig(filename='service_output.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

# --- Simulated Service Globals (Potential Issue Area) ---
_problematic_cache = [] # This list is intentionally left as a global to represent a potential issue.
MAX_CACHE_SIZE_BYTES = 2 * 1024 * 1024 # This is the *intended* maximum size for the _problematic_cache.
MEMORY_THRESHOLD_FOR_ERROR_BYTES = 10 * 1024 * 1024 # Global simulated memory limit for the entire service.

def get_current_simulated_memory_usage():
    """Estimates the current memory usage simulated by _problematic_cache."""
    total_size = sys.getsizeof(_problematic_cache)
    for item in _problematic_cache:
        if isinstance(item, str):
            total_size += sys.getsizeof(item)
        # Extend for other complex types if needed for more realism
    return total_size

def _generate_large_data(size_mb=1):
    """Generates a large string for memory consumption simulation."""
    return 'X' * (size_mb * 1024 * 1024)

def process_request(request_id: int):
    global _problematic_cache
    request_type = random.choice(['normal', 'report', 'analytics', 'heavy_report'])
    
    logging.info(f"[{request_id}] Processing request type: {request_type}")
    
    try:
        # Simulate work
        time.sleep(0.01 + random.random() * 0.05) # 10-60ms

        if request_type == 'heavy_report':
            # This type of request involves processing large datasets
            # and might interact with a "cache"
            large_item = _generate_large_data(size_mb=1) # Generate 1MB data
            _problematic_cache.append(large_item)
            logging.debug(f"[{request_id}] Added 1MB item to problematic cache.")

        # Simulate memory exhaustion leading to 500 error for the entire service
        current_simulated_service_memory = get_current_simulated_memory_usage()
        if current_simulated_service_memory > MEMORY_THRESHOLD_FOR_ERROR_BYTES:
            raise MemoryError("Simulated memory exhaustion!")

        logging.info(f"[{request_id}] Status: 200 OK. Simulated Memory: {current_simulated_service_memory / (1024 * 1024):.2f} MB")
        return "200 OK"

    except MemoryError as e:
        logging.error(f"[{request_id}] Status: 500 Internal Server Error - {e}. Simulated Memory: {get_current_simulated_memory_usage() / (1024 * 1024):.2f} MB")
        return "500 Internal Server Error"
    except Exception as e:
        logging.error(f"[{request_id}] Status: 500 Internal Server Error - An unexpected error occurred: {e}. Simulated Memory: {get_current_simulated_memory_usage() / (1024 * 1024):.2f} MB")
        return "500 Internal Server Error"

def run_service(num_requests: int):
    logging.info("--- Service Starting ---")
    error_count = 0
    for i in range(1, num_requests + 1):
        status = process_request(i)
        if "500" in status:
            error_count += 1
        if i % 100 == 0:
            current_memory = get_current_simulated_memory_usage()
            logging.info(f"--- After {i} requests: Current Error Rate: {error_count / i * 100:.2f}%. Simulated Memory: {current_memory / (1024 * 1024):.2f} MB ---")
    logging.info(f"--- Service Finished. Total Requests: {num_requests}, Total Errors: {error_count}, Final Error Rate: {error_count / num_requests * 100:.2f}% ---")

if __name__ == '__main__':
    # Run service for a significant number of requests to observe the issue
    run_service(num_requests=1000)