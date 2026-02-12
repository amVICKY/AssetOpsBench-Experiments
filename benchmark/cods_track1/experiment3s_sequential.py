import time
import json
import pathlib
import random
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed

# IMPORT EXISTING FUNCTION (DO NOT MODIFY IT)
from run_track_1 import run_planning_workflow


# -------- CONFIG --------

SCENARIO_DIR = pathlib.Path(
    "/workspace/src/assetopsbench/scenarios/single_agent"
)

SCENARIO_FILES = [
    "fmsr_utterance.json",
    "iot_utterance_meta.json",
    "tsfm_utterance.json",
    "wo_utterance.json",
]

CONCURRENCY_LEVELS = [1, 5, 10, 20]
NUM_RUNS = 5                     # 🔹 how many times to repeat SAME config
CSV_PATH = "benchmark_results.csv"
# \\wsl.localhost\Ubuntu\home\vicky\projects\AssetOpsBench\benchmark\cods_track1\experiment3s_sequential.py

# -------- LOAD ALL SCENARIOS ONCE --------

def load_all_scenarios():
    all_scenarios = []

    for fname in SCENARIO_FILES:
        file_path = SCENARIO_DIR / fname
        with open(file_path, "r") as f:
            data = json.load(f)

        scenarios = data if isinstance(data, list) else [data]

        for sc in scenarios:
            all_scenarios.append(
                {
                    "id": int(sc["id"]),
                    "text": sc["text"]
                }
            )

    if not all_scenarios:
        raise RuntimeError("No scenarios loaded")

    print(f"Loaded {len(all_scenarios)} total scenarios")
    return all_scenarios


ALL_SCENARIOS = load_all_scenarios()


# -------- SINGLE QUERY RUN --------

def run_single_query():
    scenario = random.choice(ALL_SCENARIOS)
    question = scenario["text"]
    qid = scenario["id"]

    start = time.perf_counter()
    try:
        run_planning_workflow(question, qid)
        success = True
    except Exception:
        success = False
    end = time.perf_counter()

    return {
        "scenario_id": qid,
        "latency_sec": end - start,
        "success": success,
    }


# -------- CONCURRENT LOAD --------

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


# -------- MAIN (UPDATED) --------

if __name__ == "__main__":

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.writer(f)

        # CSV header
        writer.writerow([
            "concurrency",
            "run_id",
            "avg_latency_sec",
            "min_latency_sec",
            "max_latency_sec",
            "failures",
            "total_requests",
        ])

        for c in CONCURRENCY_LEVELS:
            print("\n==============================")
            print(f"Concurrency = {c}")

            all_run_avg_latencies = []
            all_run_failures = []

            for run_id in range(1, NUM_RUNS + 1):
                print(f"  Run {run_id}/{NUM_RUNS}")

                results = run_concurrent_load(c)

                latencies = [r["latency_sec"] for r in results]
                failures = sum(1 for r in results if not r["success"])

                avg_latency = sum(latencies) / len(latencies)

                # store for aggregation
                all_run_avg_latencies.append(avg_latency)
                all_run_failures.append(failures)

                # write per-run row
                writer.writerow([
                    c,
                    run_id,
                    round(avg_latency, 4),
                    round(min(latencies), 4),
                    round(max(latencies), 4),
                    failures,
                    len(results),
                ])

                print(
                    f"    avg={avg_latency:.3f}s | "
                    f"fails={failures}/{len(results)}"
                )

            # -------- AVERAGE ACROSS RUNS --------
            writer.writerow([
                c,
                "AVG",
                round(sum(all_run_avg_latencies) / NUM_RUNS, 4),
                round(min(all_run_avg_latencies), 4),
                round(max(all_run_avg_latencies), 4),
                round(sum(all_run_failures) / NUM_RUNS, 2),
                "-",
            ])

    print(f"\n✅ Benchmark completed. Results saved to {CSV_PATH}")
