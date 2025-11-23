# CHTC Tools - Complete System Summary

## What You Have

A comprehensive, production-ready system for managing all CHTC operations from your local computer with integrated WandB experiment tracking.

## Key Features

### 🔐 Smart SSH Management
- **One 2FA per session**: Authenticate once, connection persists for 4 hours
- **Automatic reconnection**: Seamlessly reconnects when needed
- **Connection pooling**: All commands share the same connection
- **No manual SSH**: Everything through the CLI

### 📊 Deep WandB Integration
- **Automatic job tracking**: Submit with `--wandb` flag
- **Resource monitoring**: CPU, memory, disk usage logged
- **Artifact management**: Outputs, logs, checkpoints tracked
- **Runtime integration**: Use WandB SDK in your code
- **Sweep support**: Hyperparameter optimization with multiple agents

### 🗂️ Project-Based Workflow
- **Structured organization**: Code, data, jobs, results
- **Bidirectional sync**: Push code, pull results
- **Multi-project support**: Manage multiple research projects
- **Template system**: Quick start with examples

### 🐳 Container Support
- **Remote building**: Build on CHTC's interactive nodes
- **Automatic staging**: Containers go to /staging automatically
- **GPU support**: Pre-configured PyTorch + CUDA templates
- **Easy deployment**: One command to build and use

### 📈 Job Management
- **Template-based submission**: GPU, basic, WandB templates
- **Real-time monitoring**: Watch mode with auto-refresh
- **Log fetching**: Automatic download and WandB update
- **Resource optimization**: Track actual vs. requested resources

## System Architecture

```
Local Computer (Your Mac)
  ├── bin/chtc                    # Main CLI
  ├── lib/
  │   ├── utils.sh                # Logging, config, helpers
  │   └── ssh.sh                  # SSH ControlMaster management
  ├── scripts/
  │   ├── submit.sh               # Job submission + WandB
  │   ├── monitor.sh              # Real-time monitoring
  │   ├── fetch_logs.sh           # Log download + WandB update
  │   ├── container.sh            # Container management
  │   ├── project.sh              # Project scaffolding
  │   └── wandb_logger.py         # WandB SDK integration
  ├── templates/
  │   ├── basic.sub               # HTCondor templates
  │   ├── gpu.sub
  │   ├── wandb.sub
  │   ├── pytorch-gpu.def         # Container templates
  │   └── wandb_wrapper.sh        # Runtime wrapper
  └── examples/
      ├── train-wandb.py          # Complete example
      └── wandb-sweep.yaml        # Sweep config

Configuration
  ~/.chtcrc                       # Your credentials (pre-configured)
  ~/.chtc/ssh_control/            # SSH sockets
  ~/.chtc/wandb_mappings.txt      # Job-to-run links
  ~/chtc-workspace/
    ├── projects/                 # Your research projects
    └── logs/                     # Downloaded logs
```

## Complete Command Reference

### Connection
```bash
chtc connect              # Connect with 2FA
chtc disconnect           # Close connection
chtc status               # Check connection
chtc login                # Interactive SSH session
```

### Job Management
```bash
chtc submit job.sub [options]
  --wandb                 # Enable WandB tracking
  --project <name>        # WandB project
  --gpu                   # Request GPU
  --cpus <n>              # Request CPUs
  --memory <size>         # Request memory
  --disk <size>           # Request disk

chtc monitor              # Show job status
chtc monitor --watch      # Real-time monitoring
chtc queue                # HTCondor queue
chtc logs <job-id>        # Fetch logs + update WandB
```

### File Transfer
```bash
chtc upload <local> <remote>      # Upload files
chtc download <remote> <local>    # Download files
chtc quota                        # Check disk usage
```

### Projects
```bash
chtc project init <name>          # Create project
chtc project list                 # List projects
chtc project sync <name>          # Push to CHTC
chtc project pull <name>          # Pull results
```

### Containers
```bash
chtc container build <def>        # Build container
chtc container list               # List containers
chtc container upload <sif>       # Upload container
chtc container download <name>    # Download container
```

### Utilities
```bash
chtc exec "<command>"             # Run any command on CHTC
chtc help                         # Show help
```

## Installation & Setup

```bash
# 1. Install
cd chtc-tools
./install.sh

# 2. Reload shell
source ~/.bashrc  # or ~/.zshrc

# 3. Test installation
./test-system.sh

# 4. Connect to CHTC
chtc connect
# Enter password + Duo 2FA

# 5. Verify
chtc status
chtc quota
```

## Quick Start Example

```bash
# Create a project
chtc project init ml-experiment
cd ~/chtc-workspace/projects/ml-experiment

# Add your code
cp /path/to/train.py code/

# Edit job submit file
vim jobs/example.sub
# Update executable, resources, etc.

# Submit with WandB tracking
chtc submit jobs/example.sub --wandb --project ml-experiment

# Monitor
chtc monitor --watch

# When complete, fetch logs
chtc logs <job-id>

# View in WandB
# URL is shown in submit output and monitor
```

## WandB Integration Details

### Three Levels of Tracking

**Level 1: Automatic (via submit command)**
- Job submission metadata
- HTCondor job ID
- Resource requests
- Submit file as artifact
- No code changes needed

**Level 2: Runtime (in your code)**
```python
import wandb

wandb.init(project="my-project")
wandb.log({"loss": loss, "acc": acc})
wandb.log_artifact("model.pt")
```

**Level 3: Completion (via fetch logs)**
- Actual resource usage
- Job duration
- Exit status
- Output files as artifacts

### WandB Sweeps for CHTC

```bash
# 1. Create sweep config (see examples/wandb-sweep.yaml)
wandb sweep wandb-sweep.yaml

# 2. Get sweep ID (e.g., abc123)

# 3. Create submit file
cat > sweep.sub <<EOF
executable = /usr/bin/python3
arguments = -m wandb agent SWEEP_ID

request_cpus = 1
request_memory = 4GB
request_disk = 5GB

queue 10  # Run 10 parallel agents
EOF

# 4. Submit
chtc submit sweep.sub
```

## File Size Guidelines

| Size | Location | Transfer Method |
|------|----------|-----------------|
| < 1GB | `/home/nandwani2/` | `transfer_input_files = file.txt` |
| 1-30GB | `/staging/nandwani2/` | `transfer_input_files = osdf:///chtc/staging/nandwani2/file.tar.gz` |
| 30-100GB | `/staging/nandwani2/` | `transfer_input_files = file:///staging/nandwani2/big.tar.gz` |
| > 100GB | Contact CHTC | Special arrangements |

## Resource Quotas

- `/home`: 40GB
- `/staging`: 100GB (1000 files max)

Check with: `chtc quota`

## Best Practices

1. **Always use projects**: Keeps everything organized
2. **Enable WandB tracking**: Free visibility into all experiments
3. **Build containers on CHTC**: Don't build locally
4. **Use staging for large files**: Faster transfers
5. **Monitor resource usage**: Optimize future jobs
6. **Keep connection alive**: Persists for 4 hours
7. **Version control your code**: Projects work great with git

## Troubleshooting

### Connection Issues
```bash
chtc disconnect
chtc connect
```

### Job Won't Start
```bash
# Check why
chtc exec "condor_q -hold"
chtc exec "condor_q -better-analyze <job-id>"
```

### WandB Not Working
```bash
# Check API key
grep WANDB_API_KEY ~/.chtcrc

# Test locally
python3 -c "import wandb; wandb.login(key='YOUR_KEY')"
```

### Out of Quota
```bash
chtc quota
# Clean up old files
chtc exec "rm -rf /home/nandwani2/old_project"
```

## Example Use Cases

### 1. GPU Training with WandB
```bash
# Build PyTorch container
chtc container build templates/pytorch-gpu.def

# Submit training job
chtc submit train.sub --wandb --gpu --memory 16GB
```

### 2. Parameter Sweep
```bash
# Create submit file with multiple jobs
cat > sweep.sub <<EOF
executable = run.sh
arguments = --lr \$(lr) --batch \$(batch)

request_cpus = 1
request_memory = 4GB

queue lr,batch from (
  0.001,32
  0.01,32
  0.001,64
  0.01,64
)
EOF

chtc submit sweep.sub --wandb
```

### 3. Multi-Step Workflow (DAG)
```bash
cat > pipeline.dag <<EOF
JOB preprocess prep.sub
JOB train train.sub
JOB evaluate eval.sub

PARENT preprocess CHILD train
PARENT train CHILD evaluate
EOF

chtc exec "cd ~/jobs && condor_submit_dag pipeline.dag"
```

## Documentation

- **QUICKSTART.md**: Fast introduction
- **README.md**: Feature overview
- **ARCHITECTURE.md**: Deep dive into design
- **This file**: Complete reference

## What Makes This Special

1. **No more manual SSH**: Everything through one CLI
2. **2FA only once per session**: ControlMaster magic
3. **WandB everywhere**: Complete experiment tracking
4. **Project-based**: Professional organization
5. **Hybrid design**: Best of bash and Python
6. **Production-ready**: Error handling, logging, testing
7. **Extensible**: Easy to add new features

## Next Steps

1. **Run the test**: `./test-system.sh`
2. **Read quick start**: `cat QUICKSTART.md`
3. **Try example**: `examples/train-wandb.py`
4. **Create real project**: `chtc project init <your-research>`
5. **Submit first job**: `chtc submit --wandb`

## Support

- **CHTC Docs**: https://chtc.cs.wisc.edu/
- **CHTC Support**: chtc@cs.wisc.edu
- **WandB Docs**: https://docs.wandb.ai/
- **This System**: All scripts have `--help`

---

**You now have a complete, professional-grade CHTC management system with integrated experiment tracking. Everything you need is here.**

Happy researching! 🚀
