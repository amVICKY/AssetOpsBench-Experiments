import time
import json
import statistics
from typing import List, Dict

from agent_hive.task import Task
from agent_hive.enum import ContextType
from agent_hive.logger import get_custom_logger

from agent_hive.workflows.sequential import SequentialWorkflow
from agent_hive.workflows.parallel import ParallelWorkflow
from agent_hive.workflows.track1_planning import NewPlanningWorkflow
from agent_hive.agents.react_reflect_agent import ReactReflectAgent

from agent_hive.tools.skyspark import (
    iot_agent_name,
    iot_agent_description,
    iot_tools,
)
from agent_hive.tools.fmsr import (
    fmsr_agent_name,
    fmsr_agent_description,
    fmsr_tools,
)
from agent_hive.tools.tsfm import (
    tsfm_agent_name,
    tsfm_agent_description,
    tsfm_tools,
)

logger = get_custom_logger(__name__)

# ======================================================
# Build workflow once (planner excluded)
# ======================================================

def build_tasks(question: str, llm_model=16) -> List[Task]:
    agents = [
        ReactReflectAgent(iot_agent_name, iot_agent_description, iot_tools, llm_model),
        ReactReflectAgent(fmsr_agent_name, fmsr_agent_description, fmsr_tools, llm_model),
        ReactReflectAgent(tsfm_agent_name, tsfm_agent_description, tsfm_tools, llm_model),
    ]

    root = Task(description=question, agents=agents, expected_output="")
    planner = NewPlanningWorkflow(tasks=[root], llm=llm_model)
    return planner.generate_steps()


# ======================================================
# Run workflow once
# ======================================================

def run_once(workflow) -> float:
    start = time.time()
    workflow.run()
    return time.time() - start


# ======================================================
# EXPERIMENT 6: Reproducibility
# ======================================================

def experiment_reproducibility(tasks: List[Task], runs=5):
    seq_latencies = []
    par_latencies = []

    for i in range(runs):
        logger.info(f"[EXP-6] Sequential run {i+1}/{runs}")
        seq_latencies.append(
            run_once(SequentialWorkflow(tasks, ContextType.SELECTED))
        )

        logger.info(f"[EXP-6] Parallel run {i+1}/{runs}")
        par_latencies.append(
            run_once(ParallelWorkflow(tasks, ContextType.SELECTED))
        )

    results = {
        "sequential": {
            "median": statistics.median(seq_latencies),
            "std": statistics.stdev(seq_latencies),
            "min": min(seq_latencies),
            "max": max(seq_latencies),
        },
        "parallel": {
            "median": statistics.median(par_latencies),
            "std": statistics.stdev(par_latencies),
            "min": min(par_latencies),
            "max": max(par_latencies),
        },
        "speedup": statistics.median(seq_latencies) /
                   statistics.median(par_latencies),
    }

    print("\n=== Experiment 6: Reproducibility ===")
    print(json.dumps(results, indent=4))
    return results


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":
    QUESTION = "Investigate abnormal vibration in Chiller A"
    tasks = build_tasks(QUESTION)
    experiment_reproducibility(tasks, runs=5)