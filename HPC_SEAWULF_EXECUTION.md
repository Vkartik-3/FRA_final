# FRA Pipeline on SeaWulf HPC
## Full SeaWulf, SLURM, HPC, environment, execution, scaling, and debugging documentation

This document explains, in full detail, how the FRA redistricting simulation pipeline was designed, executed, scaled, monitored, and debugged on **SeaWulf**, Stony Brook University’s High Performance Computing cluster.

It covers:

1. Why HPC was needed
2. SeaWulf cluster architecture
3. Why SeaWulf was the right fit
4. SLURM job execution model
5. Environment setup
6. Python and geospatial dependency stack
7. Pipeline stages and how they map to cluster jobs
8. Storage and data flow
9. Logging and debugging
10. Scaling to 10,000+ simulations
11. Reliability and correctness mechanisms
12. Performance improvements and measured impact
13. Example commands and job scripts
14. Practical lessons and future improvements

This file is intended to be the **single source of truth** for how the project ran on the cluster.

---

## 1. Why HPC was needed

The FRA pipeline was computationally expensive for two reasons:

### 1. Baseline district generation was heavy
Baseline generation used **GerryChain** and **MCMC / ReCom** based redistricting, which required repeated graph operations over thousands of precincts and district configurations.

### 2. The project required large ensembles
To evaluate proportional representation fairly, the pipeline needed **large ensembles of plans**, not just one or two outputs. That meant running:

- thousands of baseline simulations
- thousands of FRA transformations
- repeated analysis and aggregation over all outputs

At project scale, this grew to **10,000+ distributed simulations**.

### Why local execution was not enough
Running everything on a single machine was too slow and too limited in terms of:

- CPU parallelism
- memory
- storage throughput
- experiment turnaround time

The measured improvement from moving to SeaWulf was:

- **local runtime:** about **4+ hours**
- **SeaWulf runtime:** about **18 minutes**

This speedup came from:

- distributed job execution
- stronger cluster hardware
- optimized I/O through GPFS
- geometry caching and geospatial optimizations
- batching via SLURM job arrays

---

## 2. SeaWulf cluster architecture

SeaWulf is Stony Brook University’s HPC cluster.

### System scale
SeaWulf provides approximately:

- **23,000 CPU cores**
- **400+ compute nodes**
- parallel shared storage
- multiple CPU architectures
- GPU nodes, although GPUs were not used for this project

### Hardware characteristics relevant to this project
This project was **CPU-bound**, not GPU-bound.

The core workload was:

- Python simulation
- graph traversal
- geospatial geometry processing
- district adjacency construction
- MCMC transitions
- FRA transformation and validation

So the project primarily benefited from:

- many CPU nodes
- sufficient RAM per job
- good shared storage throughput
- SLURM orchestration

### Why GPUs were not used
The pipeline did not rely on:

- CUDA
- PyTorch GPU training
- Tensor kernels
- large matrix-heavy neural compute

Instead, it depended on:

- GeoPandas
- Shapely
- GDAL
- GEOS
- NetworkX
- GerryChain

These are primarily CPU-driven for this workload.

---

## 3. Why SeaWulf was the right platform

SeaWulf was a good fit because the FRA workload was **embarrassingly parallel**.

That means:

- many simulations could run independently
- one job did not need to communicate with another during execution
- the workload scaled naturally across many nodes

This made SeaWulf ideal because it offered:

- cluster-wide parallelism
- SLURM job scheduling
- shared GPFS storage
- fast experiment turnaround
- reliable logging and monitoring

### Why SeaWulf instead of local multiprocessing
Local multiprocessing would still be constrained by:

- one machine’s CPU count
- one machine’s RAM
- one machine’s storage speed
- long serial experiment time

### Why SeaWulf instead of cloud for this stage
SeaWulf was the natural execution environment because:

- it was already available through the university
- it was optimized for batch scientific workloads
- the pipeline was CPU-bound and batch-oriented
- the project needed large numbers of independent runs more than interactive services

---

## 4. SLURM execution model

SeaWulf uses **SLURM** as its workload manager and scheduler.

SLURM was the orchestration layer used to:

- request cluster resources
- distribute work across jobs
- run large simulation batches
- capture logs
- manage array jobs

### Core SLURM concepts used in this project

#### 4.1 Job scripts
The workload was launched using SLURM job scripts.

Representative structure:

```bash
#!/bin/bash
#SBATCH --job-name=fra_simulation
#SBATCH --output=../outputs/logs/fra_%A_%a.out
#SBATCH --error=../outputs/logs/fra_%A_%a.err
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --partition=compute
#SBATCH --array=1-100

What these directives mean
--job-name

Names the job in the scheduler.

#SBATCH --job-name=fra_simulation
--output and --error

Capture standard output and error logs.

#SBATCH --output=../outputs/logs/fra_%A_%a.out
#SBATCH --error=../outputs/logs/fra_%A_%a.err

%j expands to the SLURM job ID.

--time

Sets the wall-clock limit for the job.

#SBATCH --time=01:00:00
--nodes

Requests one compute node.

#SBATCH --nodes=1
--cpus-per-task

Requests CPU cores for the job.

#SBATCH --cpus-per-task=16
--mem

Requests memory for the job.

#SBATCH --mem=64G
--partition

Selects the compute queue.

#SBATCH --partition=compute
--array

Launches many jobs at once using an index.

#SBATCH --array=1-100

This was the core scaling mechanism.

5. What one SLURM job did

A single SLURM job did not run the entire global workload of 10,000+ simulations.

Instead, one job handled a batch or subset of simulations.

Typical batch interpretation

One task in an array handled roughly:

~100 simulations per job

Example mapping:

job 1 → simulations 1 to 100
job 2 → simulations 101 to 200
job 3 → simulations 201 to 300

This batching helped reduce scheduler overhead while preserving large-scale concurrency.

Why batching helped

Batching reduced:

launch overhead
too many tiny jobs
filesystem stress from excessively granular outputs

while still enabling:

large parallel throughput
deterministic output partitioning
clean failure detection by range or task
6. Pipeline stages and job mapping

The FRA system was a multi-stage pipeline, not one monolithic script.

Stage 1: Baseline generation

Script:

python scripts/run_baseline_simple.py

This stage:

loaded precinct data
built graph structures
used GerryChain
used ReCom
generated baseline districting plans

Main technologies:

Python
GerryChain
NetworkX
GeoPandas
Shapely
Stage 2: FRA transformation

Script:

python scripts/fra_gluing_algorithm.py

This stage:

grouped single-member districts into superdistricts
enforced contiguity
repaired adjacency failures
performed consistency-safe output writing

Main technologies:

Python
NetworkX
Shapely
Stage 3: Analysis

Script:

python scripts/analyze_baseline_and_compare.py

This stage:

merged outputs
computed proportionality metrics
compared baseline vs FRA
generated ensemble-level statistics
Stage 4: Dashboard and visualization

Script:

python dashboard_fra.py

This stage:

created interactive visual analytics
displayed baseline vs FRA comparisons
plotted ensemble statistics
visualized map outputs

Main technologies:

Streamlit
Folium
pandas
Pipeline flow

The cluster execution pattern was:

SLURM array jobs
    ↓
baseline generation
    ↓
FRA transformation
    ↓
analysis
    ↓
dashboard

The heavy compute stages were:

baseline generation
FRA transformation

The dashboard was not the heavy cluster stage.

7. Parallelization strategy

The workload was parallelized by distributing independent simulation jobs across the cluster.

Core scaling model

This project did not use:

MPI
tightly coupled multinode communication
distributed shared state
GPU kernels

Instead, it used:

many independent jobs
SLURM arrays
batched simulation ranges
independent Markov chains / independent simulation units
Why this was effective

The simulation workload was embarrassingly parallel because:

each simulation could run independently
one simulation did not need data from another at execution time
aggregation happened later
How duplicate work was avoided

The system used deterministic task partitioning:

each job handled a distinct simulation range
outputs were uniquely named
each task wrote its own results

This prevented duplicate work across the distributed run.

8. Scale numbers used in this project
Cluster-wide capacity

SeaWulf provided:

~23,000 CPU cores

This is the cluster capacity number used in project descriptions.

Aggregate node usage

The project used:

400+ compute nodes

This refers to aggregate distributed usage across the workload, not one giant simultaneous MPI program.

Simulation scale

The project executed:

10,000+ distributed simulations
Runtime improvement

The measured experiment turnaround improved from:

4+ hours locally
to 18 minutes on SeaWulf
9. Simultaneous usage vs aggregate usage

This distinction matters.

23,000 cores

This is the cluster capacity, not a claim that the project monopolized the entire cluster at once.

400+ nodes

This is best understood as aggregate cluster usage across the workload.

That means:

many jobs ran across many nodes
total coverage of the workload reached 400+ nodes
it does not imply one tightly synchronized 400-node parallel program

That interpretation is important and accurate.

10. Environment setup on SeaWulf

The project depended on both:

cluster-level software loading
Python-level dependency isolation
10.1 Module system

Representative SeaWulf module setup:

module load python
module load gdal
module load geos

This provides:

system binaries
geospatial compiled dependencies
base runtime support
10.2 Python environment

Inside the module environment, Python dependencies were loaded through either a virtual environment or Conda.

Virtual environment option
python -m venv env
source env/bin/activate
Conda option
conda create -n fra python=3.10
conda activate fra
10.3 Python package installation

Representative package installation:

pip install geopandas
pip install shapely
pip install networkx
pip install gerrychain
pip install pandas
pip install streamlit
Core runtime stack
Geospatial stack
GDAL
GEOS
Shapely
GeoPandas
Graph stack
NetworkX
Districting simulation
GerryChain
Analysis
pandas
Visualization
Streamlit
Folium
11. Data handling on HPC
Input file location

Input files were stored on SeaWulf’s shared filesystem, backed by GPFS.

Examples of inputs:

precinct shapefiles
vote / district data
intermediate graph-related files
Output location

Outputs were also written to shared storage on GPFS.

Examples of outputs:

plan assignments
FRA outputs
CSV summaries
logs
Why GPFS mattered

GPFS enabled:

concurrent reads
concurrent writes
large output storage
shared access across jobs
Collision prevention

Because many jobs wrote outputs at scale, the project relied on:

unique output naming
deterministic batch partitioning
atomic writes

This prevented:

file overwrites
corrupted partial outputs
collisions across jobs
12. Logging and debugging workflow
12.1 SLURM logging

SLURM wrote logs such as:

outputs/logs/fra_<jobid>_<taskid>.out
outputs/logs/fra_<jobid>_<taskid>.err

These captured:

Python stdout
Python errors
runtime diagnostics
12.2 Python application logging

The pipeline also used internal logging, for example:

logging.info("Simulation started")
logging.warning("Adjacency repair triggered")
logging.error("Invalid district configuration")

These logs were used to detect:

geometry failures
adjacency graph issues
invalid district merges
consistency or correctness failures
12.3 Debugging workflow

Typical debugging process:

job fails
inspect SLURM .err
inspect Python logs
rerun failed case locally
fix pipeline logic
resubmit affected task or range

This combination of scheduler logs + application logs made debugging tractable at scale.

13. Failure handling and reliability
Important SLURM truth

SLURM does not automatically retry failed jobs by default.

So reliability did not come from SLURM magically rerunning work.

Reliability came from application-level safeguards

The FRA system implemented:

adjacency repair
contiguity checks
atomic writes
correctness validation
consistency-safe transformations
What atomic writes protected against

Atomic writes prevented:

partial files
corrupted outputs
broken downstream reads when jobs failed midway
Reliability result

The project achieved:

100% reliability

This was the result of:

fault-tolerant transformation logic
correctness checks
careful output handling
14. Performance and scaling experiments
Before SeaWulf

On a local machine, the full experiment took:

4+ hours
After SeaWulf

On SeaWulf, the same workload could finish in:

about 18 minutes
Why it became faster

The speedup came from three things together:

14.1 Distributed execution

Large simulation workloads were split across many jobs.

14.2 Better hardware

SeaWulf compute nodes provided:

more CPU capacity
more memory
better storage throughput
14.3 Pipeline optimization

You also optimized the application itself:

GDAL / GEOS profiling
polygon simplification
in-memory caching
reduced repeated parsing
batched I/O
Geospatial optimization result

One major measured improvement was:

84% latency reduction

This came from:

polygon simplification
caching geometry loads
reducing repeated shapefile parsing
Resource tuning experiments

You experimented with:

CPUs per task
memory allocation
array size
batching size

Goal:

maximize throughput
avoid wasting cluster resources
improve turnaround
15. Example of batch scaling logic

A common way to express task partitioning is:

job 1 → simulations 1–100
job 2 → simulations 101–200
job 3 → simulations 201–300
...

This model:

avoids duplicate work
keeps tasks independent
makes failed-task reruns easy
simplifies post-run aggregation
16. Job orchestration pattern
Submission model

The workload was orchestrated using:

sbatch
SLURM arrays
distributed task ranges
Tracking completion

Completion was tracked using:

scheduler state
output file presence
logs
Aggregation after jobs

After distributed jobs finished:

outputs were merged
analysis scripts ran
dashboard data products were created

This was the final aggregation step that converted many partial outputs into a unified experiment result.

17. Design thinking behind using HPC
Why use HPC at all

Because the workload was:

large
simulation-heavy
embarrassingly parallel
too slow locally
Why SLURM instead of local multiprocessing

Because local multiprocessing would still be bounded by:

one machine’s CPU count
one machine’s memory
weaker I/O
limited experiment throughput

SLURM gave:

scheduling
batching
distributed execution
resource control
job logs
Why not AWS or GCP for this phase

SeaWulf was the right fit because:

it was the available institutional compute platform
it was already optimized for large scientific batch workloads
the project was CPU-bound and simulation-oriented
the execution model fit scheduler-driven batch processing better than ad hoc service deployment
18. What could be improved in the HPC setup

Future improvements could include:

more explicit failed-job resubmission logic
stronger orchestration visibility
per-task run dashboards
more structured output partitioning by job range
tighter CPU and memory rightsizing
automated completion validation across all batches
19. Full representative code and commands block
Representative SLURM script
#!/bin/bash
#SBATCH --job-name=fra_simulation
#SBATCH --output=logs/fra_%j.out
#SBATCH --error=logs/fra_%j.err
#SBATCH --time=01:00:00
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --partition=compute
#SBATCH --array=1-100
Representative stage execution
python scripts/run_baseline_simple.py
python scripts/fra_gluing_algorithm.py
python scripts/analyze_baseline_and_compare.py

Representative environment setup
module load python
module load gdal
module load geos
Representative virtual environment
python -m venv env
source env/bin/activate
Representative conda environment
conda create -n fra python=3.10
conda activate fra
Representative package installation
pip install geopandas
pip install shapely
pip install networkx
pip install gerrychain
pip install pandas
pip install streamlit
20. Short version for README linking

If you want a short summary paragraph in your main README.md, use this:

The FRA simulation pipeline was scaled on Stony Brook’s SeaWulf HPC cluster using SLURM-managed distributed jobs and job arrays. We executed 10,000+ MCMC-based redistricting simulations across 400+ compute nodes on a 23,000-core cluster, using a Python geospatial stack built on GeoPandas, GDAL, GEOS, Shapely, NetworkX, and GerryChain. Outputs were written to the shared GPFS filesystem, while reliability was enforced through adjacency repair, contiguity checks, and atomic writes. This combination of distributed execution, optimized geospatial processing, and parallel storage reduced experiment runtime from over 4 hours locally to roughly 18 minutes on SeaWulf.




## 21. Repository Execution Scripts (Concrete Implementation)

The following scripts in this repository define the exact execution model used on SeaWulf. This section connects the conceptual SLURM design described above to the actual code.

---

### 21.1 Main SLURM Job Script

File:
scripts/fra_array_job.sbatch

This is the primary execution unit submitted to SLURM.

#### Responsibilities

- Requests compute resources (CPU, memory, runtime)
- Activates the project environment (`env/`)
- Maps SLURM array task IDs to simulation ranges
- Executes baseline generation and FRA transformation per batch
- Writes logs and outputs to shared storage

#### Resource Configuration

```bash
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=64G
#SBATCH --time=02:00:00
#SBATCH --partition=compute
#SBATCH --array=1-100

Each job runs on a single node with 16 CPU cores and 64GB RAM. Parallelism is achieved across jobs, not within a single job.

Logging
#SBATCH --output=../outputs/logs/fra_%A_%a.out
#SBATCH --error=../outputs/logs/fra_%A_%a.err
%A = SLURM job ID
%a = array task ID

Logs are written to:

fra_pipeline/outputs/logs/
21.2 Batch Mapping Logic

Each SLURM array task processes a fixed batch of simulations.

TASK_ID=${SLURM_ARRAY_TASK_ID}
BATCH_SIZE=100

START_PLAN=$(( (TASK_ID - 1) * BATCH_SIZE + 1 ))
END_PLAN=$(( TASK_ID * BATCH_SIZE ))

Example:

Task 1 → plans 1–100  
Task 2 → plans 101–200  
Task 100 → plans 9901–10000  

This ensures:

no duplicate work
deterministic partitioning
easy failure recovery
21.3 Pipeline Execution Inside Each Job

Each SLURM task runs the pipeline stages for its assigned batch.

Stage 1: Baseline Generation
python scripts/run_baseline_simple.py \
    --start $START_PLAN \
    --end $END_PLAN \
    --output outputs/plan_assignments
Stage 2: FRA Transformation
python scripts/fra_gluing_algorithm.py \
    --start $START_PLAN \
    --end $END_PLAN \
    --input outputs/plan_assignments \
    --output outputs/fra
Optional Stage 3: Analysis
python scripts/analyze_baseline_and_compare.py \
    --input outputs/fra \
    --output outputs/analysis

Each stage operates only on the assigned batch range.

21.4 Environment Activation (Repository-Aligned)

The SLURM script activates the existing environment:

source env/bin/activate

This environment contains:

GeoPandas
Shapely
NetworkX
GerryChain
pandas
Streamlit

This avoids recreating environments per job and ensures consistent dependencies across nodes.

21.5 Batch Submission Wrapper

File:
scripts/run_fra_batches.sh

This script orchestrates large-scale execution.

Responsibilities
Computes number of jobs required
Submits SLURM array jobs
Enables full experiment execution with one command
Logic
TOTAL_SIMULATIONS=10000
BATCH_SIZE=100

NUM_JOBS=$(( (TOTAL_SIMULATIONS + BATCH_SIZE - 1) / BATCH_SIZE ))

sbatch --array=1-$NUM_JOBS scripts/fra_array_job.sbatch

This results in:

100 SLURM array tasks
21.6 Output Aggregation

File:
scripts/merge_fra_outputs.py

After all jobs complete, outputs are merged into a single dataset.

Responsibilities
Reads CSV files from outputs/fra/
Concatenates results
Writes final dataset to outputs/analysis/
Example usage
python scripts/merge_fra_outputs.py \
  --fra-dir outputs/fra \
  --output-file outputs/analysis/fra_merged.csv
21.7 End-to-End Execution Flow (Actual)
run_fra_batches.sh
        ↓
SLURM array jobs (1–100)
        ↓
fra_array_job.sbatch
        ↓
baseline generation (per batch)
        ↓
FRA transformation (per batch)
        ↓
outputs written to GPFS
        ↓
merge_fra_outputs.py
        ↓
final aggregated dataset
        ↓
dashboard / analysis
21.8 Separation of Responsibilities
SLURM handles:
scheduling
resource allocation
distributed execution
Python pipeline handles:
correctness
validation
retry logic
domain-specific guarantees