# HTCondor Optimization & Best Practices

Comprehensive guide to optimizing your CHTC workloads for maximum throughput and efficiency.

## Core Principles

1. **Right-size resources**: Request only what you need
2. **Maximize throughput**: More smaller jobs > fewer large jobs
3. **Minimize overhead**: Reduce startup/cleanup time
4. **Monitor and iterate**: Check actual usage, optimize requests

## Resource Optimization

### Understanding Resource Usage

After jobs complete, check `.log` files:

```
Partitionable Resources :    Usage  Request Allocated
   Cpus                 :                 1         1
   Disk (KB)            :   125000  5000000   8203477
   Memory (MB)          :     3891     4096      4096
```

**Analysis**:
- **Memory**: Used 3.9GB of 4GB requested ✓ (good)
- **Disk**: Used 125MB of 5GB requested ✗ (over-requested!)
- **CPUs**: Used 1 of 1 requested ✓ (good)

### Memory Optimization

**Strategy**: Request slightly more than actual usage

```bash
# Bad - way too much
request_memory = 64GB  # But only uses 4GB

# Good - right-sized
request_memory = 5GB  # Uses ~4GB, 25% buffer
```

**Finding the right value**:
1. Submit test job with generous memory
2. Check actual usage in log
3. Request actual + 20-30% buffer

**Example**:
```bash
# Test run used 3.8 GB
# Request: 3.8 * 1.25 = 4.75 GB → round to 5GB
request_memory = 5GB
```

**Impact**: Over-requesting memory reduces available slots, lowers throughput!

### Disk Optimization

**Calculate needed disk**:
```
Total = Input files + Output files + Temp files + Executable
```

**Example calculation**:
```bash
# Inputs: 2GB tar.gz, unpacks to 8GB
# Output: 1GB results
# Temp: 2GB intermediate files
# Executable: 100MB

# Total: 8GB (unpacked) + 1GB + 2GB + 0.1GB = 11.1GB
# With 30% buffer: 11.1 * 1.3 = 14.4GB → 15GB

request_disk = 15GB
```

**Tips**:
- Compressed inputs still need space when unpacked
- Remove temp files as you go
- Stream processing when possible

### CPU Optimization

**Single-threaded code**:
```bash
request_cpus = 1  # Most efficient for single-threaded
```

**Multi-threaded code**:
```bash
# Only if code uses multiple cores!
request_cpus = 4

# In your code, respect the request:
import os
n_cpus = int(os.environ.get('_CONDOR_RequestCpus', 1))
```

**Test scaling**:
```python
# Does 4 CPUs give 4x speedup?
# If not, stick with fewer CPUs
```

### GPU Optimization

**Use GPUs only when beneficial**:
```bash
# If GPU gives 10x+ speedup: worth it
request_gpus = 1

# If GPU gives <3x speedup: maybe not worth waiting in queue
request_gpus = 0  # Use CPU instead
```

**GPU memory**:
```bash
# Only if you need specific GPU memory
# Most jobs don't need this
request_gpus = 1
gpus_minimum_memory = 16000  # 16GB GPU memory
```

## Job Structure Optimization

### Principle: Many Small Jobs > Few Large Jobs

**Bad**:
```bash
# One huge job processing 10,000 files
# Takes 50 hours
# If it fails, start over from scratch
queue 1
```

**Good**:
```bash
# 100 jobs processing 100 files each
# Each takes 30 minutes
# Failures only lose 30 min of work
# Parallel execution = faster completion
queue 100
```

### Optimal Job Duration

**Target**: 1-6 hours per job

**Too short** (< 30 min):
- High overhead from file transfer
- Queue/startup time wastes resources

**Too long** (> 12 hours):
- Higher risk of interruption
- Less parallel benefit
- Longer recovery from failures

**Adjust by changing batch size**:
```bash
# If jobs too short, process more files per job
arguments = --batch-size 1000  # Instead of 100

# If jobs too long, split into smaller batches
arguments = --batch-size 50  # Instead of 500
```

### Minimize File Transfer Overhead

**Bad**:
```bash
# 10,000 small files
transfer_input_files = file1.txt, file2.txt, ..., file10000.txt
```

**Good**:
```bash
# Tarball
transfer_input_files = inputs.tar.gz

# In executable:
tar -xzf inputs.tar.gz
# Process files
```

**Impact**: Transferring 1 large file is 100x faster than 1000 small files!

### Reuse Containers and Large Files

**Bad** (transfers 8GB container to every job):
```bash
transfer_input_files = huge-container.sif, script.py
```

**Good** (container cached in staging):
```bash
container_image = osdf:///chtc/staging/username/huge-container.sif
transfer_input_files = script.py
Requirements = (Target.HasCHTCStaging == true)
```

**Impact**: OSDF caches files, subsequent jobs transfer instantly!

## Workflow Optimization

### Parameter Sweeps

**Efficient parameter sweep**:
```bash
executable = experiment.sh
arguments = $(lr) $(batch_size)

request_cpus = 1
request_memory = 8GB
request_disk = 10GB

queue lr,batch_size from (
    0.001,32
    0.001,64
    0.01,32
    0.01,64
    0.1,32
    0.1,64
)
```

**All 6 experiments run in parallel!**

### DAG for Dependencies

**When jobs depend on each other**, use DAG:

```
# Inefficient: Wait for all to finish, then manually start next
condor_submit preprocess.sub
# Wait...
condor_submit train.sub
# Wait...
condor_submit evaluate.sub

# Efficient: DAG handles everything
condor_submit_dag pipeline.dag
```

**DAG parallelizes when possible**:
```
     preprocess
        /   \\
   train1  train2  (run in parallel!)
        \\   /
      evaluate
```

### Batch Similar Jobs

**Group jobs by resource requirements**:

```bash
# CPU jobs - submit together
request_cpus = 1
request_memory = 4GB
queue 100

# Separate submission for GPU jobs
request_cpus = 4
request_memory = 16GB
request_gpus = 1
queue 10
```

**Why**: HTCondor can match jobs to resources more efficiently.

## Data Management Optimization

### Use Appropriate Transfer Method

```bash
# < 1GB: Standard transfer
transfer_input_files = data.csv

# 1-30GB: OSDF (with caching!)
transfer_input_files = osdf:///chtc/staging/username/data.tar.gz

# 30-100GB: file:/// protocol
transfer_input_files = file:///staging/username/huge-data.tar

# > 100GB: Contact CHTC for special handling
```

### Clean Up After Yourself

**In your job script**:
```bash
#!/bin/bash

# Unpack
tar -xzf large-input.tar.gz

# Process
python process.py

# Clean up temp files
rm -rf large-input/  # Don't transfer this back!

# Only keep results
# Outputs automatically transferred back
```

**In /staging**:
```bash
# Remove old containers
ssh chtc "rm /staging/nandwani2/old-container.sif"

# Remove old data no longer needed
ssh chtc "rm /staging/nandwani2/experiment-v1-data.tar.gz"
```

### Compress Everything

```bash
# Before uploading
tar -czf data.tar.gz data/  # gzip compression

# Even better for highly compressible data
tar -cjf data.tar.bz2 data/  # bzip2 (slower but smaller)

# In submit file, auto-unpack
transfer_input_files = osdf:///chtc/staging/username/data.tar.gz?pack=auto
```

## Code Optimization

### Profile Your Code

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
process_data()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumtime')
stats.print_stats(20)  # Top 20 slowest functions
```

**Optimize the bottlenecks first!**

### Vectorize Operations

**Bad** (slow Python loops):
```python
result = []
for i in range(len(data)):
    result.append(data[i] * 2 + 1)
```

**Good** (vectorized numpy):
```python
result = data * 2 + 1  # 100x faster!
```

### Use Compiled Libraries

**Prefer**:
- NumPy over pure Python loops
- Pandas over manual iteration
- Numba for JIT compilation
- Cython for C-level speed

**Example with Numba**:
```python
from numba import jit

@jit(nopython=True)
def compute(data):
    # Your computation
    return result

# Runs at C speed!
```

### Efficient I/O

**Bad**:
```python
# Read file line by line (slow)
for line in open('huge_file.txt'):
    process(line)
```

**Good**:
```python
# Read in chunks
with open('huge_file.txt') as f:
    for chunk in iter(lambda: f.read(1024*1024), ''):
        process(chunk)

# Or use pandas for tabular data
df = pd.read_csv('data.csv', chunksize=10000)
for chunk in df:
    process(chunk)
```

## Monitoring and Iteration

### Monitor Actual Resource Usage

**After each batch**:
```bash
# Check logs
chtc logs JobID

# Look for:
# - Actual memory used vs requested
# - Actual disk used vs requested
# - Job runtime

# Adjust next submission
```

### A/B Testing

**Test resource changes**:
```bash
# Submit 10 jobs with current settings
queue 10

# Submit 10 jobs with optimized settings
request_memory = 6GB  # Was 8GB
queue 10

# Compare completion times and success rates
```

### Track with WandB

```python
import wandb

run = wandb.init(project="optimization")
run.log({
    'job_id': os.environ.get('CLUSTER'),
    'memory_requested': 8192,
    'memory_used': get_memory_usage(),
    'runtime': runtime,
    'throughput': records_per_second,
})
```

**Analyze trends** in WandB dashboard to find optimal settings.

## Anti-Patterns to Avoid

### ❌ Over-Requesting Resources

```bash
# "Just to be safe..."
request_memory = 128GB  # But only uses 2GB
request_cpus = 16  # But code is single-threaded
request_disk = 500GB  # But only needs 5GB
```

**Impact**: Fewer jobs run, longer queue times for everyone.

### ❌ Transferring Unnecessary Files

```bash
# Don't do this!
transfer_input_files = entire_dataset.tar.gz, \
    old_results.tar.gz, \
    backup.tar.gz, \
    test_data.tar.gz
```

**Only transfer what you need for THIS job.**

### ❌ Not Using Staging for Large Files

```bash
# Bad - 10GB file in /home
transfer_input_files = /home/username/large-file.tar.gz
```

**Use /staging for files > 1GB!**

### ❌ Long Jobs Without Checkpointing

```bash
# 48-hour job, no checkpointing
# If it fails at hour 47... start over 😢
```

**Save progress periodically!**

### ❌ Not Testing Before Scaling

```bash
# Submitting 10,000 untested jobs
queue 10000

# All fail due to typo in script 😱
```

**Test with 5-10 jobs first!**

## Performance Checklist

Before submitting large batches:

- [ ] Tested with small batch (5-10 jobs)
- [ ] Checked actual resource usage in logs
- [ ] Right-sized memory request (actual + 25%)
- [ ] Right-sized disk request (actual + 30%)
- [ ] CPUs = number your code actually uses
- [ ] Job duration 1-6 hours (split if longer)
- [ ] Large files (>1GB) in /staging
- [ ] Using OSDF for cached files
- [ ] Files compressed/tarred
- [ ] Temp files cleaned up in script
- [ ] Code profiled and optimized
- [ ] Using appropriate container

## Advanced Optimization

### Pilot Jobs

**Test different configurations**:
```bash
# Submit small batches with different settings
# Track with unique identifiers

executable = test.sh
arguments = config_$(config_id)

request_memory = $(memory)

queue config_id,memory from (
    1,4GB
    2,6GB
    3,8GB
)
```

**Find optimal settings empirically.**

### Container Layering

**Separate environment from code**:

```dockerfile
# Base container (rarely changes)
Bootstrap: docker
From: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

%post
    pip install wandb numpy pandas
```

**Submit file**:
```bash
# Reuse base container
container_image = osdf:///chtc/staging/username/base-env.sif

# Transfer only code
transfer_input_files = my_code.tar.gz

queue
```

**Container cached once, code changes freely!**

### Shared Data Patterns

**For many jobs using same large dataset**:

```bash
# Job 1, 2, 3, ... all use same data
transfer_input_files = \
    osdf:///chtc/staging/username/shared-dataset.tar.gz?pack=auto, \
    job_specific_$(Process).csv

queue 100
```

**OSDF caches the large file after first job!**

## Measuring Success

### Throughput Metrics

**Track**:
- Jobs/hour completion rate
- Average queue time
- Resource efficiency (used/requested)
- Failed job rate

**Goal**: Maximize jobs/hour while minimizing failures.

### Cost/Benefit Analysis

**Is optimization worth it?**

Example:
- Current: 1000 jobs × 2 hours = 2000 CPU-hours
- Optimized: 1000 jobs × 1.5 hours = 1500 CPU-hours
- **Savings**: 500 CPU-hours (25%)

**If optimization takes 2 hours of your time, and you run this weekly**:
- Saves 500 hours/week
- In one month: 2000 CPU-hours saved
- **Definitely worth it!**

## Sources and Further Reading

- [OSG Resource Optimization](https://portal.osg-htc.org/documentation/htc_workloads/workload_planning/preparing-to-scale-up/)
- [HTCondor Best Practices](https://htcondor.readthedocs.io/en/latest/users-manual/submitting-a-job.html)
- [CHTC Job Submission Guide](https://chtc.cs.wisc.edu/uw-research-computing/htcondor-job-submission)
- [Resource Requirements Guide](https://en.wikitolearn.org/Course:HTCondor/Exercises/Resource_requirements)
