# CHTC Tools - Quick Start Guide

## Installation

```bash
cd chtc-tools
./install.sh
source ~/.bashrc  # or ~/.zshrc
```

Edit `~/.chtcrc` with your CHTC username (already set to `nandwani2`).

## First Time Setup

```bash
# Connect to CHTC (you'll be prompted for password + Duo 2FA)
chtc connect

# Check connection status
chtc status

# Check your quota
chtc quota
```

The SSH connection will persist for 4 hours, so you won't need to re-authenticate with 2FA for subsequent commands!

## Basic Workflow

### 1. Create a Project

```bash
chtc project init my-research
cd ~/chtc-workspace/projects/my-research
```

This creates a structured project:
```
my-research/
├── code/           # Your scripts
├── data/           # Input data
├── containers/     # Container definitions
├── jobs/           # HTCondor submit files
└── results/        # Output (auto-created)
```

### 2. Add Your Code

```bash
# Edit the example script or add your own
vim code/run.sh

# Or copy your existing code
cp /path/to/your/script.py code/
```

### 3. Submit a Job with WandB Tracking

```bash
# Edit the submit file
vim jobs/example.sub

# Submit with WandB tracking
chtc submit jobs/example.sub --wandb --project my-research
```

WandB will automatically track:
- Job submission time
- Resource usage (CPU, memory, disk)
- Job duration
- Exit status
- Output files as artifacts

### 4. Monitor Jobs

```bash
# Check job queue
chtc queue

# Monitor in real-time (refreshes every 10s)
chtc monitor --watch

# Fetch logs when complete
chtc logs <job-id>
```

## GPU Jobs

```bash
# Submit GPU job
chtc submit jobs/gpu_job.sub --gpu --gpus 1 --wandb
```

Your submit file should include:
```
request_gpus = 1
container_image = osdf:///chtc/staging/nandwani2/pytorch-gpu.sif
requirements = (HasCHTCStaging == true) && (TARGET.CUDACapability >= 5.0)
```

## Container Workflow

```bash
# Build container on CHTC (interactive)
chtc container build templates/pytorch-gpu.def

# List containers
chtc container list

# Use in job
# Add to submit file:
#   container_image = osdf:///chtc/staging/nandwani2/pytorch-gpu.sif
#   requirements = (HasCHTCStaging == true)
```

## File Transfer

```bash
# Upload files/directories
chtc upload /local/path /home/nandwani2/destination

# Download files/directories
chtc download /home/nandwani2/source /local/destination

# For large files (>1GB), use staging:
chtc upload large_data.tar.gz /staging/nandwani2/
```

## WandB Integration

### Automatic Tracking

When you submit with `--wandb`, the system automatically:
1. Creates a WandB run
2. Logs job metadata (cluster ID, resources)
3. Uploads submit file as artifact
4. Tracks job duration and exit status
5. Uploads logs and outputs when you fetch them

### Manual WandB in Your Code

See `examples/train-wandb.py` for a complete example:

```python
import wandb

# Initialize (API key is already in environment)
wandb.init(project="my-research", config={"lr": 0.001})

# Log metrics
wandb.log({"loss": loss, "accuracy": acc})

# Save artifacts
artifact = wandb.Artifact("model", type="model")
artifact.add_file("model.pt")
wandb.log_artifact(artifact)

wandb.finish()
```

### WandB Sweeps

```bash
# Create sweep from config
wandb sweep examples/wandb-sweep.yaml

# Get sweep ID (e.g., abc123xyz)
# Create a submit file that runs multiple agents:
#   executable = wandb
#   arguments = agent SWEEP_ID
#   queue 10  # Run 10 parallel agents
```

## Advanced Features

### DAG Workflows

For multi-step workflows:

```bash
# Create DAG file (jobs.dag)
cat > jobs.dag <<EOF
JOB preprocess preprocess.sub
JOB train train.sub
JOB evaluate eval.sub

PARENT preprocess CHILD train
PARENT train CHILD evaluate
EOF

# Submit DAG
chtc exec "cd ~/jobs && condor_submit_dag jobs.dag"

# Monitor
chtc exec "condor_q -dag"
```

### Project Sync

```bash
# Sync local changes to CHTC
chtc project sync my-research

# Pull results back
chtc project pull my-research
```

### Execute Arbitrary Commands

```bash
# Run any command on CHTC
chtc exec "condor_q -better-analyze 12345"
chtc exec "ls -lh /staging/nandwani2"
```

## Troubleshooting

### Connection Issues

```bash
# Disconnect and reconnect
chtc disconnect
chtc connect
```

### Job Debugging

```bash
# Check why job is held
chtc exec "condor_q -hold"

# View detailed job info
chtc exec "condor_q -better-analyze <job-id>"

# Fetch and view logs
chtc logs <job-id>
```

### WandB Issues

Check if API key is set:
```bash
grep WANDB_API_KEY ~/.chtcrc
```

Test WandB locally:
```bash
python3 -c "import wandb; wandb.login(key='f04957e341167ac5452921a251b0921fedd3558b')"
```

## Tips

1. **Keep connections alive**: The SSH connection persists for 4h. If you're doing a lot of work, your connection will stay active.

2. **Use projects**: They keep everything organized and make syncing easy.

3. **Enable WandB tracking**: It costs nothing and gives you complete visibility into all jobs.

4. **Check quota regularly**: Run `chtc quota` to avoid hitting limits.

5. **Use staging for large files**: Files >1GB should go in `/staging/nandwani2/`

6. **Build containers on CHTC**: Don't build locally, use `chtc container build`

## Common Commands Cheat Sheet

```bash
chtc connect              # Connect (2FA required once)
chtc status               # Check connection
chtc submit job.sub --wandb  # Submit with tracking
chtc monitor --watch      # Real-time monitoring
chtc queue                # Check queue
chtc logs <id>            # Fetch logs
chtc quota                # Check disk usage
chtc project init <name>  # New project
chtc project sync <name>  # Sync to CHTC
chtc container build X.def # Build container
chtc disconnect           # Close connection
```

## Next Steps

1. Try the example: `examples/train-wandb.py`
2. Read the full CHTC docs: https://chtc.cs.wisc.edu/
3. Explore WandB features: https://wandb.ai/
4. Build your first real project!

---

**Support**: If you encounter issues, check CHTC docs or email chtc@cs.wisc.edu
