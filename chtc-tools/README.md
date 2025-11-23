# CHTC Tools

A comprehensive, local-first management system for CHTC (Center for High Throughput Computing) with integrated WandB tracking.

## Features

- **Persistent SSH Connections**: Single 2FA authentication with ControlMaster (connections persist for 4 hours)
- **Project-Based Workflow**: Manage multiple projects with automatic sync
- **Job Management**: Submit, monitor, and track HTCondor jobs from your local machine
- **WandB Integration**: Automatic experiment tracking, metrics logging, and artifact management
- **Container Support**: Build and manage Apptainer containers remotely
- **Smart File Transfer**: Automatically selects optimal transfer method (local, OSDF, staging)
- **DAG Workflows**: Build and submit complex multi-step workflows
- **Real-time Monitoring**: Track job status, resource usage, and logs

## Architecture

```
chtc-tools/
├── bin/
│   └── chtc                 # Main CLI entry point (bash)
├── lib/
│   ├── utils.sh             # Common utilities
│   └── ssh.sh               # SSH connection management
├── scripts/
│   ├── wandb_logger.py      # WandB integration
│   ├── job_monitor.py       # Job monitoring daemon
│   └── container_builder.py # Container automation
├── templates/
│   ├── basic.sub            # HTCondor submit templates
│   ├── gpu.sub
│   ├── wandb.sub            # WandB-enabled job template
│   └── build.sub
└── local/                   # Local workspace (git-ignored)
```

## Installation

1. Clone or download this repository
2. Copy `.chtcrc.example` to `~/.chtcrc` and configure
3. Add `bin/` to your PATH or create an alias
4. Install Python dependencies (for WandB features):
   ```bash
   pip install wandb pyyaml tabulate rich
   ```

## Quick Start

```bash
# Connect to CHTC (will prompt for 2FA once)
chtc connect

# Check connection status
chtc status

# Submit a job with WandB tracking
chtc submit --wandb --project my-research job.sub

# Monitor jobs in real-time
chtc monitor

# Fetch job logs
chtc logs <job-id>

# Build a container
chtc container build my-container.def

# Disconnect
chtc disconnect
```

## WandB Integration

All jobs submitted with `--wandb` automatically:
- Create WandB runs with CHTC metadata
- Log resource usage (CPU, memory, disk)
- Track job status and duration
- Store artifacts (outputs, logs)
- Link to HTCondor job IDs

## Usage Examples

See individual command help:
```bash
chtc help
chtc submit --help
chtc container --help
```
