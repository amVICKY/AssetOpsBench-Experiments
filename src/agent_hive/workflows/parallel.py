import json
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

from pydantic import Field

from agent_hive.enum import ContextType
from agent_hive.task import Task
from agent_hive.workflows.base_workflow import Workflow
from agent_hive.logger import get_custom_logger

logger = get_custom_logger(__name__)

class ParallelWorkflow(Workflow):
    """
    DAG-based parallel workflow.
    Tasks are executed as soon as their dependencies (context tasks) are resolved.
    """

    context_type: ContextType = Field(
        default=ContextType.SELECTED,
        description="Parallel workflow requires explicit dependencies.",
    )

    def __init__(
        self, tasks: List[Task], context_type: ContextType = ContextType.SELECTED
    ):
        self.tasks = tasks
        self.context_type = context_type
        self.memory: Dict[Task, str] = {}
        self._verify_tasks()
        self.dag = self._build_dag()

    def _verify_tasks(self):
        if self.context_type != ContextType.SELECTED:
            raise ValueError(
                "ParallelWorkflow requires ContextType.SELECTED for DAG execution"
            )

        for task in self.tasks:
            if task.agents is None or len(task.agents) != 1:
                raise ValueError("Each task must have exactly one agent")

    def _build_dag(self):
        dag = {task: [] for task in self.tasks}
        indegree = {task: 0 for task in self.tasks}

        for task in self.tasks:
            if task.context:
                for dep in task.context:
                    dag[dep].append(task)
                    indegree[task] += 1

        return {
            "graph": dag,
            "indegree": indegree,
        }

    def _execute_task(self, task: Task):
        agent = task.agents[0]

        context = ""
        if task.context:
            for ctx_task in task.context:
                context += self.memory[ctx_task] + "\n"

        user_input = f"{task.description}\n\nContext:\n{context}" if context else task.description

        logger.info(f"Executing task: {task.description}")
        response = agent.execute_task(user_input)
        response = response.split("Final Answer:")[0].strip()
        return response

    def run(self):
        graph = self.dag["graph"]
        indegree = self.dag["indegree"]

        ready_tasks = [t for t in self.tasks if indegree[t] == 0]

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=len(self.tasks)) as executor:
            futures = {}

            for task in ready_tasks:
                futures[executor.submit(self._execute_task, task)] = task

            while futures:
                for future in as_completed(futures):
                    task = futures.pop(future)
                    result = future.result()
                    self.memory[task] = result

                    for downstream in graph[task]:
                        indegree[downstream] -= 1
                        if indegree[downstream] == 0:
                            futures[
                                executor.submit(self._execute_task, downstream)
                            ] = downstream
                    break  # re-evaluate futures dynamically

        end_time = time.time()

        history = self.generate_history()
        history.append(
            {
                "total_latency_sec": end_time - start_time,
                "workflow_type": "parallel_dag",
            }
        )

        print(json.dumps(history, indent=4))
        return history

    def generate_history(self):
        history = []
        for i, task in enumerate(self.tasks):
            history.append(
                {
                    "task_number": i + 1,
                    "task_description": task.description,
                    "agent_name": task.agents[0].name,
                    "response": self.memory.get(task, ""),
                }
            )
        return history
    
print("Class initialize successful")