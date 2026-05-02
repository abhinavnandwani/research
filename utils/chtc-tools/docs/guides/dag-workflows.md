# DAG Workflows Guide

Complete guide to creating multi-step workflows with HTCondor DAGMan.

## What is DAGMan?

DAGMan (Directed Acyclic Graph Manager) is HTCondor's workflow management system that:
- Automatically submits jobs in the correct order
- Handles job dependencies
- Manages failure recovery
- Tracks complex multi-step workflows

## When to Use DAGs

Use DAGMan when:
- Jobs must run in a specific sequence
- Later jobs depend on earlier jobs' outputs
- You have complex data pipelines
- You need automatic retry/recovery

**Don't use DAGs if**:
- All jobs are independent (use simple `queue N` instead)
- Simple parameter sweeps (use `queue from` instead)

## DAG Basics

### DAG Components

**Nodes**: Individual HTCondor jobs
**Edges**: Dependencies between jobs (parent → child)
**DAG File**: Text file describing the workflow

### Simple Example

Workflow: preprocess → analyze → visualize

**Directory structure**:
```
workflow/
├── preprocess.sub
├── analyze.sub
├── visualize.sub
└── pipeline.dag
```

**pipeline.dag**:
```
# Define jobs
JOB preprocess preprocess.sub
JOB analyze analyze.sub
JOB visualize visualize.sub

# Define dependencies
PARENT preprocess CHILD analyze
PARENT analyze CHILD visualize
```

**Submit**:
```bash
condor_submit_dag pipeline.dag
```

DAGMan will:
1. Submit preprocess
2. Wait for it to complete
3. Submit analyze
4. Wait for it to complete
5. Submit visualize

## DAG File Syntax

### Basic Commands

**JOB**: Define a node
```
JOB NodeName submit_file.sub [OPTIONS]
```

**PARENT/CHILD**: Define dependencies
```
PARENT parent1 [parent2 ...] CHILD child1 [child2 ...]
```

**VARS**: Pass variables to jobs
```
VARS NodeName variablename="value"
```

**RETRY**: Automatic retry on failure
```
RETRY NodeName N
```

**SCRIPT PRE**: Run before job
```
SCRIPT PRE NodeName script.sh [args]
```

**SCRIPT POST**: Run after job
```
SCRIPT POST NodeName script.sh [args]
```

### Example with All Features

```
# Define jobs
JOB data_prep data_prep.sub
JOB train_model train.sub
JOB evaluate evaluate.sub

# Pass variables
VARS train_model learning_rate="0.001" epochs="100"
VARS evaluate model_path="/staging/username/model.pth"

# Dependencies
PARENT data_prep CHILD train_model
PARENT train_model CHILD evaluate

# Retry failed jobs
RETRY train_model 3
RETRY evaluate 2

# Pre-processing script
SCRIPT PRE data_prep check_data.sh

# Post-processing script
SCRIPT POST evaluate upload_results.sh
```

## Common Workflow Patterns

### Pattern 1: Linear Pipeline

```
A → B → C → D
```

**DAG file**:
```
JOB A step_a.sub
JOB B step_b.sub
JOB C step_c.sub
JOB D step_d.sub

PARENT A CHILD B
PARENT B CHILD C
PARENT C CHILD D
```

### Pattern 2: Fan-Out (One to Many)

```
    A
   /|\\
  B C D
```

**DAG file**:
```
JOB A prepare.sub
JOB B process1.sub
JOB C process2.sub
JOB D process3.sub

PARENT A CHILD B C D
```

### Pattern 3: Fan-In (Many to One)

```
  A B C
   \\|/
    D
```

**DAG file**:
```
JOB A job_a.sub
JOB B job_b.sub
JOB C job_c.sub
JOB D merge.sub

PARENT A B C CHILD D
```

### Pattern 4: Diamond

```
    A
   / \\
  B   C
   \\ /
    D
```

**DAG file**:
```
JOB A split.sub
JOB B process_left.sub
JOB C process_right.sub
JOB D merge.sub

PARENT A CHILD B C
PARENT B C CHILD D
```

### Pattern 5: Parameter Sweep with Aggregation

```
prep → job1 → collect
     → job2 →
     → job3 →
```

**DAG file**:
```
JOB prep prepare_data.sub

JOB exp1 experiment.sub
JOB exp2 experiment.sub
JOB exp3 experiment.sub

JOB collect aggregate.sub

# Prep before experiments
PARENT prep CHILD exp1 exp2 exp3

# Collect after all experiments
PARENT exp1 exp2 exp3 CHILD collect

# Pass different parameters
VARS exp1 learning_rate="0.001"
VARS exp2 learning_rate="0.01"
VARS exp3 learning_rate="0.1"
```

## Real-World Examples

### Example 1: Machine Learning Pipeline

```
# ML Pipeline: data → preprocess → train → evaluate → deploy

JOB download_data download.sub
JOB preprocess preprocess.sub
JOB train_model train.sub
JOB evaluate evaluate.sub
JOB deploy deploy.sub

# Linear dependency
PARENT download_data CHILD preprocess
PARENT preprocess CHILD train_model
PARENT train_model CHILD evaluate
PARENT evaluate CHILD deploy

# Retry training (might fail due to resource issues)
RETRY train_model 3

# Check data quality before starting
SCRIPT PRE download_data validate_source.sh

# Upload metrics after evaluation
SCRIPT POST evaluate upload_wandb.sh
```

### Example 2: Hyperparameter Search

```
# Grid search: split data → train with different params → select best

JOB split_data split.sub

# Training jobs with different hyperparameters
JOB train_lr001 train.sub
JOB train_lr01 train.sub
JOB train_lr1 train.sub

JOB select_best select.sub

# Split data first
PARENT split_data CHILD train_lr001 train_lr01 train_lr1

# Select best after all complete
PARENT train_lr001 train_lr01 train_lr1 CHILD select_best

# Different learning rates
VARS train_lr001 lr="0.001"
VARS train_lr01 lr="0.01"
VARS train_lr1 lr="0.1"
```

### Example 3: Genomics Pipeline

```
# Genomics: align → sort → index → call_variants → annotate

JOB align align.sub
JOB sort sort.sub
JOB index index.sub
JOB call_variants variants.sub
JOB annotate annotate.sub

PARENT align CHILD sort
PARENT sort CHILD index
PARENT index CHILD call_variants
PARENT call_variants CHILD annotate

# Process multiple samples in parallel
VARS align sample="sample1"
VARS sort sample="sample1"
# ... etc

# Retry resource-intensive steps
RETRY align 2
RETRY call_variants 2
```

## Variables and Dynamic Workflows

### Using VARS

Pass variables to submit files:

**DAG file**:
```
JOB process_A process.sub
JOB process_B process.sub

VARS process_A input_file="data_a.csv" output_file="result_a.csv"
VARS process_B input_file="data_b.csv" output_file="result_b.csv"
```

**process.sub**:
```
executable = process.sh
arguments = $(input_file) $(output_file)

request_cpus = 1
request_memory = 4GB
request_disk = 10GB

queue
```

### Generating DAGs Programmatically

For complex workflows, generate DAG files with scripts:

**Python example**:
```python
#!/usr/bin/env python3

# Generate DAG for processing 100 files

with open('pipeline.dag', 'w') as f:
    # Preparation job
    f.write("JOB prepare prepare.sub\\n")

    # Processing jobs
    for i in range(100):
        f.write(f"JOB process_{i} process.sub\\n")

    # Collection job
    f.write("JOB collect collect.sub\\n")

    # Dependencies
    prepare_children = " ".join([f"process_{i}" for i in range(100)])
    f.write(f"PARENT prepare CHILD {prepare_children}\\n")

    collect_parents = " ".join([f"process_{i}" for i in range(100)])
    f.write(f"PARENT {collect_parents} CHILD collect\\n")

    # Variables
    for i in range(100):
        f.write(f'VARS process_{i} file_id="{i}"\\n')

print("DAG file generated: pipeline.dag")
```

## Monitoring DAGs

### Submit and Track

```bash
# Submit DAG
condor_submit_dag pipeline.dag

# Monitor (detailed view)
condor_q -dag -nobatch

# Watch in real-time
watch -n 5 condor_q -dag
```

### DAG Status Files

DAGMan creates several tracking files:

- `pipeline.dag.dagman.out` - Detailed execution log
- `pipeline.dag.dagman.log` - HTCondor log for DAGMan itself
- `pipeline.dag.nodes.log` - Status of all nodes
- `pipeline.dag.metrics` - Performance metrics

**Check progress**:
```bash
tail -f pipeline.dag.dagman.out
```

### Using condor_watch_q

Real-time updates:
```bash
condor_watch_q -file pipeline.dag.nodes.log
```

## Handling Failures

### Automatic Retry

```
RETRY NodeName NumberOfRetries
```

**Example**:
```
JOB download download.sub
RETRY download 5

JOB process process.sub
RETRY process 3
```

### Rescue DAGs

If DAG fails, DAGMan creates rescue files:
- `pipeline.dag.rescue001`
- `pipeline.dag.rescue002`
- etc.

**Resubmit** (resumes from failure point):
```bash
condor_submit_dag pipeline.dag
# Automatically uses rescue file
```

**Force fresh start**:
```bash
rm pipeline.dag.rescue*
condor_submit_dag pipeline.dag
```

### PRE/POST Scripts for Validation

**Validate before running**:
```
SCRIPT PRE train_model check_data.sh
```

**check_data.sh**:
```bash
#!/bin/bash
if [ ! -f training_data.csv ]; then
    echo "Training data missing!"
    exit 1
fi
exit 0
```

**Clean up after**:
```
SCRIPT POST evaluate cleanup.sh
```

## Advanced Features

### Subgraphs (Nested DAGs)

Include one DAG within another:

**main.dag**:
```
JOB prepare prepare.sub
SUBDAG EXTERNAL processing processing.dag
JOB finalize finalize.sub

PARENT prepare CHILD processing
PARENT processing CHILD finalize
```

### Priority

Control job priority:
```
PRIORITY NodeName PriorityValue
```

Higher values = higher priority (default: 0).

### Categories

Limit concurrent jobs per category:
```
CATEGORY NodeName category_name
MAXJOBS category_name 5
```

**Example** (limit concurrent GPU jobs):
```
CATEGORY train_1 GPU_JOBS
CATEGORY train_2 GPU_JOBS
CATEGORY train_3 GPU_JOBS

MAXJOBS GPU_JOBS 2  # Only 2 GPU jobs at once
```

### Throttling

Limit total concurrent jobs:
```
# In DAG file
DOT dag.dot UPDATE

# Command line
condor_submit_dag -maxjobs 10 pipeline.dag
```

## Best Practices

### 1. Test Individual Jobs First

Before creating DAG:
```bash
# Test each submit file independently
condor_submit preprocess.sub
condor_submit analyze.sub
# etc.
```

### 2. Use Descriptive Node Names

```
# Good
JOB download_training_data download.sub
JOB train_resnet_model train.sub

# Bad
JOB job1 a.sub
JOB job2 b.sub
```

### 3. Add Retry for Flaky Jobs

```
# Network-dependent jobs
RETRY download_data 5

# Resource-intensive jobs (might get evicted)
RETRY gpu_training 3
```

### 4. Use PRE Scripts for Validation

```
SCRIPT PRE expensive_job validate_inputs.sh
```

Catch errors early before wasting resources.

### 5. Log Everything

Ensure all jobs have proper logging:
```
# In submit files
log = job_$(Cluster).log
error = job_$(Cluster).err
output = job_$(Cluster).out
```

### 6. Keep DAGs Readable

```
# Good: commented, organized
# Data preparation phase
JOB download download.sub
JOB clean clean.sub
PARENT download CHILD clean

# Training phase
JOB train train.sub
PARENT clean CHILD train

# Bad: no organization
JOB a a.sub
JOB b b.sub
PARENT a CHILD b
```

## Debugging DAGs

### Common Issues

**DAG won't submit**:
```bash
# Check syntax
condor_submit_dag -no_submit pipeline.dag
```

**Jobs stuck**:
```bash
# Check job holds
condor_q -hold

# Analyze why not running
condor_q -better-analyze JobID
```

**Rescue DAG created unexpectedly**:
```bash
# Check what failed
grep -i "failed" pipeline.dag.dagman.out
```

### Visualization

Generate DOT file for visualization:
```
# In DAG file
DOT pipeline.dot
```

Convert to image:
```bash
dot -Tpng pipeline.dot -o pipeline.png
```

## Integration with WandB

Track DAG workflows:

**Pre-script** (start WandB run):
```bash
#!/bin/bash
# start_wandb.sh

RUN_ID=$(python3 -c "import wandb; run=wandb.init(project='pipeline'); print(run.id)")
echo $RUN_ID > wandb_run_id.txt
```

**Post-script** (log completion):
```bash
#!/bin/bash
# log_wandb.sh

RUN_ID=$(cat wandb_run_id.txt)
python3 -c "
import wandb
run = wandb.init(project='pipeline', id='$RUN_ID', resume='must')
run.log({'step_complete': True})
run.finish()
"
```

**DAG file**:
```
JOB step1 step1.sub
SCRIPT PRE step1 start_wandb.sh
SCRIPT POST step1 log_wandb.sh
```

## Sources and Further Reading

- [HTCondor DAGMan Introduction](https://htcondor.readthedocs.io/en/latest/automated-workflows/dagman-introduction.html)
- [DAGMan Tutorial](https://swc-osg-workshop.github.io/OSG-UserTraining-AHM18/novice/DHTC/04-dagman.html)
- [DAGMan Applications](https://htcondor.readthedocs.io/en/v8_8/users-manual/dagman-applications.html)
- [CERN DAGMan Tutorial](https://batchdocs.web.cern.ch/tutorial/exercise8Intro.html)
