import sys
import random
import time
import os

# --- Do not modify above this line ---

# This simulates a memory-intensive data object that might be cached
# Each call adds approximately 100KB to memory.
def create_large_object_for_cache():
    return os.urandom(100 * 1024) # 100 KB random bytes

# Simulate a global unbounded cache that grows with each request
_request_cache = []

def process_request(request_id):
    global _request_cache
    try:
        # Simulate some processing delay
        time.sleep(0.0001) # Very small delay

        # This line simulates adding data to a "cache" that is not properly managed.
        # It's intended to cause memory growth.
        _request_cache.append(create_large_object_for_cache())

        # Simulate a system-level memory check. If memory usage exceeds a threshold,
        # it causes a "500 error" due to resource exhaustion.
        # This threshold is set to trigger failure after a certain number of requests.
        # (Approx 500 requests will consume ~50MB of just this cache)
        if sys.getsizeof(_request_cache) > 50 * 1024 * 1024: # 50 MB threshold
            raise MemoryError("Simulated Service Resource Exhaustion (500 Error)")

        return f"Request {request_id}: Successfully processed."
    except MemoryError as e:
        # This simulates a 500 error response due to memory issues
        return f"Request {request_id}: ERROR - {e}"
    except Exception as e:
        # Catch any other unexpected errors
        return f"Request {request_id}: UNEXPECTED ERROR - {e}"

def run_service_simulation(num_requests, output_file="service_output.txt"):
    with open(output_file, "w") as f:
        failed_requests_count = 0
        for i in range(1, num_requests + 1):
            result = process_request(i)
            if "ERROR" in result:
                failed_requests_count += 1
            f.write(result + "
")
        
        f.write("
--- Simulation Summary ---
")
        f.write(f"Total requests processed: {num_requests}
")
        f.write(f"Requests failed due to ERROR: {failed_requests_count}
")
        
        if failed_requests_count > 0:
            f.write("OVERALL_STATUS: FAILED_DUE_TO_MEMORY_ISSUES
")
        else:
            f.write("OVERALL_STATUS: ALL_REQUESTS_SUCCESSFUL
")

if __name__ == "__main__":
    # Run a simulation for 600 requests.
    # With the current settings, approximately 100-150 requests should fail due to memory,
    # simulating the '15% of requests' scenario.
    run_service_simulation(num_requests=600)

# --- Do not modify below this line ---