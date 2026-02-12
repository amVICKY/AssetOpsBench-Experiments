import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# IMPORT EXISTING FUNCTION (DO NOT MODIFY IT)
from run_track_1 import run_planning_workflow

# FIXED QUERY (SAME FOR ALL USERS)
QUESTION = "List all available IoT sites."
QID = 999


def run_single_query():
    start = time.perf_counter()
    try:
        run_planning_workflow(QUESTION, QID)
        success = True
    except Exception:
        success = False
    end = time.perf_counter()

    return {
        "latency_sec": end - start,
        "success": success
    }


def run_concurrent_load(concurrency):
    results = []

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(run_single_query)
            for _ in range(concurrency)
        ]

        for future in as_completed(futures):
            results.append(future.result())

    return results


if __name__ == "__main__":
    CONCURRENCY_LEVELS = [1,5,10,20]
    lat = []
    fails = []

    for c in CONCURRENCY_LEVELS:
        print("\n==============================")
        print(f"Running with concurrency = {c}")

        results = run_concurrent_load(c)

        latencies = [r["latency_sec"] for r in results]
        failures = sum(1 for r in results if not r["success"])

        print(f"Latencies (sec): {latencies}")
        print(f"Failures: {failures}/{len(results)}")
        lat.append(latencies)
        fails.append(f"{failures}/len({results})")
    print(f"Time taken is = {lat}")
    print(f"Number of task failed = {fails}")
          

          