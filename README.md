# Abstract

This repository presents a reproducible experimental framework built on AssetOpsBench (CODS Track-1) for evaluating agentic workflows in complex operational environments. The system leverages containerized execution, structured workflows, and controlled benchmarking to ensure deterministic, repeatable experiments.

All experiments are executed within the official AssetOpsBench Docker environment, ensuring consistency across machines and eliminating dependency drift.

# Key Features

Fully reproducible Docker-based experimentation

Structured workflow execution (Sequential / Planning)

Isolation using Conda-managed runtime

Deterministic experiment setup

Easy modification and extension of agent workflows

<pre>
AssetOpsBench/
│
├── benchmark/                     # Benchmark orchestration and configs
├── docs/                          # Documentation
├── src/                           # Core source code (ALL importable code lives here)
│   ├── agent_hive/
│   │   └── workspace/             # Experiments
│   ├── assetopsbench/
│   ├── meta_agent/
│   └── ...
├── docker-compose.yml
└── README.md
</pre>



# Running 
1. git clone <your-repo-url>
cd AssetOpsBench

2. docker-compose -f benchmark/cods_track1/docker-compose.yml up -d

3. docker ps

Expected:
cods_track1-assetopsbench-1
cods_track1-couchdb-1

4. Enter Experiment Container
docker exec -it cods_track1-assetopsbench-1 /bin/bash

5. Activate Official Runtime (Critical)
conda activate assetopsbench

6. Configure Python Import Path
export PYTHONPATH=/workspace/src
cd /workspace
<pre>
This enables Python to resolve project modules correctly.

### Running Experiments
Sequential Workflow
python -m src.agent_hive.workflows.sequential

### Planning Workflow
python -m src.agent_hive.workflows.planning

### Extending / Custom Experiments
All new experimental modules must be placed inside:
/workspace/src/

### Example:
/workspace/src/agent_hive/custom_experiment.py
  
### Run:
python -m src.agent_hive.custom_experiment

No rebuild required unless dependencies change.
</pre>
