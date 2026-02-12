import time
import json
from typing import List, Dict

from agent_hive.task import Task
from agent_hive.enum import ContextType
from agent_hive.logger import get_custom_logger

from agent_hive.workflows.sequential import SequentialWorkflow
# from agent_hive.workflows.parallel import ParallelWorkflow
from agent_hive.workflows.track1_planning import NewPlanningWorkflow
from agent_hive.agents.react_reflect_agent import ReactReflectAgent

# from agent_hive.workflows.latency import reset_latency

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
# GLOBAL CONTROL (CRITICAL)
# ======================================================
DRY_RUN = True   # MUST be True for Exp 4 & 5


# ======================================================
# Planner + task construction
# ======================================================

def build_tasks_from_planner(question: str, llm_model=16) -> List[Task]:
    iot_agent = ReactReflectAgent(
        name=iot_agent_name,
        description=iot_agent_description,
        tools=iot_tools,
        llm=llm_model,
        few_shots="",
        task_examples=None,
    )

    fmsr_agent = ReactReflectAgent(
        name=fmsr_agent_name,
        description=fmsr_agent_description,
        tools=fmsr_tools,
        llm=llm_model,
        few_shots="",
        task_examples=None,
    )

    tsfm_agent = ReactReflectAgent(
        name=tsfm_agent_name,
        description=tsfm_agent_description,
        tools=tsfm_tools,
        llm=llm_model,
        few_shots="",
        task_examples=None,
    )

    root_task = Task(
        description=question,
        agents=[iot_agent, fmsr_agent, tsfm_agent],
        expected_output="",
    )

    planner = NewPlanningWorkflow(tasks=[root_task], llm=llm_model)
    return planner.generate_steps()


# ======================================================
# SAFE WORKFLOW RUNNER (NO WATSONX)
# ======================================================

def run_workflow_simulated(
    simulated_tokens: int = 0,
    fault_delay: float = 0.0,
) -> Dict:
    # reset_latency()

    start = time.time()

    # Base inference cost
    base_latency = 0.4

    # Token-dependent cost
    token_latency = simulated_tokens * 0.000015

    # Fault injection delay
    time.sleep(base_latency + token_latency + fault_delay)

    total_time = time.time() - start

    return {
        "reasoning": total_time,
        "tool_io": 0.0,
        "sync": 0.0,
        "total": total_time,
    }


# ======================================================
# EXPERIMENT 4: Context Size vs Latency
# ======================================================

def experiment_context_size():
    context_tokens = {
        "raw": 12000,
        "summary": 3000,
        "schema": 800,
    }

    results = {}

    for mode, tokens in context_tokens.items():
        logger.info(f"[EXP-4] Context mode: {mode}, tokens={tokens}")
        results[mode] = run_workflow_simulated(simulated_tokens=tokens)

    print("\n=== Experiment 4: Context Size vs Latency ===")
    print(json.dumps(results, indent=4))
    return results


# ======================================================
# EXPERIMENT 5: Fault Injection & Latency Stability
# ======================================================

def experiment_fault_injection():
    results = {
        "no_fault": run_workflow_simulated(simulated_tokens=3000),
        "tool_timeout": run_workflow_simulated(simulated_tokens=3000, fault_delay=0.8),
        "partial_sensor_failure": run_workflow_simulated(simulated_tokens=3000, fault_delay=0.4),
    }

    print("\n=== Experiment 5: Fault Injection & Latency Stability ===")
    print(json.dumps(results, indent=4))
    return results


# ======================================================
# MAIN
# ======================================================

if __name__ == "__main__":

    print("Hero Bansode")

    # Planner is kept for structural consistency
    _ = build_tasks_from_planner("Investigate abnormal vibration in Chiller A")

    experiment_context_size()
    experiment_fault_injection()