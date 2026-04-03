import sys
import os

# DO NOT MODIFY these global constants unless explicitly instructed in the puzzle description.
# This list simulates memory accumulation. In a real scenario, this would be actual system memory.
_LEAKED_DATA = [] 

# Configurable simulation parameters (DO NOT MODIFY these values for the solution)
SIMULATED_MEMORY_LIMIT_MB = 1210 # The point at which the service starts returning 500s
NUM_SIMULATED_REQUESTS = 1000
OUTPUT_LOG_FILE = "service_requests.log"

def _get_simulated_memory_usage_mb():
    """Calculates the current simulated memory usage based on accumulated objects."""
    total_bytes = sum(sys.getsizeof(obj) for obj in _LEAKED_DATA)
    return total_bytes / (1024 * 1024)

def process_request(request_id: int) -> int:
    """
    Simulates processing a single web service request.
    Returns 200 for success, 500 for error.
    This function contains the bug leading to memory exhaustion.
    """
    # Check if simulated memory is over the limit
    if _get_simulated_memory_usage_mb() > SIMULATED_MEMORY_LIMIT_MB:
        return 500  # Service returning 500 errors due to resource exhaustion

    # --- POTENTIAL BUG AREA START ---
    # This section simulates some work and potentially causes a memory leak.
    # Approximately 15% of requests will add to the "leaked" data,
    # leading to gradual memory increase until the SIMULATED_MEMORY_LIMIT_MB is hit.
    if request_id % 7 == 0:  # Roughly 1/7 = ~14.2% of requests trigger this path
        # Simulate creating a large object that is not properly released or cleaned up
        large_object = bytearray(10 * 1024 * 1024)  # 10 MB per "leaked" object
        # _LEAKED_DATA.append(large_object) # This line is the root cause of the leak.
    # --- POTENTIAL BUG AREA END ---

    # Normal request processing logic would go here
    return 200

def run_simulation(num_requests: int, output_file: str):
    """Runs the web service simulation and logs results."""
    with open(output_file, 'w') as f:
        f.write("Request_ID,Status_Code\n")
        for i in range(1, num_requests + 1):
            status = process_request(i)
            f.write(f"{i},{status}\n")

if __name__ == "__main__":
    print(f"Running simulation for {NUM_SIMULATED_REQUESTS} requests, logging to {OUTPUT_LOG_FILE}...")
    run_simulation(NUM_SIMULATED_REQUESTS, OUTPUT_LOG_FILE)
    print("Simulation complete.")
    final_mem_usage = _get_simulated_memory_usage_mb()
    print(f"Final simulated memory usage: {final_mem_usage:.2f} MB")
    if final_mem_usage > SIMULATED_MEMORY_LIMIT_MB:
        print(f"Warning: Simulated memory usage exceeded limit ({SIMULATED_MEMORY_LIMIT_MB:.2f} MB).")
