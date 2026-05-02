# CHTC Tools - System Architecture

## Overview

A hybrid bash/Python system for managing CHTC HTC operations locally with integrated WandB experiment tracking.

## Design Principles

1. **Local-First**: Everything managed from your computer, no manual SSH needed
2. **2FA Once**: SSH ControlMaster - authenticate once, reuse for 4 hours
3. **WandB Native**: Deep integration for automatic experiment tracking
4. **Project-Based**: Organized workspace for multiple research projects
5. **Hybrid Design**: Bash for CLI/SSH, Python for WandB/complex logic

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Computer                        │
│                                                         │
│  ┌───────────────────────────────────────────────┐     │
│  │          CHTC CLI (bin/chtc)                  │     │
│  │         Main bash dispatcher                  │     │
│  └─────────────┬─────────────────────────────────┘     │
│                │                                        │
│       ┌────────┴────────┐                              │
│       │                 │                              │
│  ┌────▼─────┐    ┌──────▼──────┐                      │
│  │ lib/     │    │  scripts/   │                      │
│  │ utils.sh │    │  *.sh & .py │                      │
│  │ ssh.sh   │    └──────┬──────┘                      │
│  └────┬─────┘           │                              │
│       │                 │                              │
│       │    ┌────────────┴──────────────┐              │
│       │    │                           │              │
│       │  ┌─▼──────────┐    ┌──────────▼─────┐        │
│       │  │ Project    │    │ WandB Logger   │        │
│       │  │ Manager    │    │ (Python)       │        │
│       │  └────────────┘    └────────┬───────┘        │
│       │                              │                │
│  ┌────▼─────────────────────────┐   │                │
│  │  SSH ControlMaster           │   │                │
│  │  ~/.chtc/ssh_control/        │   │                │
│  │  (Persistent connection)     │   │                │
│  └────┬─────────────────────────┘   │                │
│       │                              │                │
└───────┼──────────────────────────────┼────────────────┘
        │                              │
        │ SSH (rsync/exec)             │ HTTPS API
        │                              │
┌───────▼──────────────────────────────┼────────────────┐
│               CHTC Cluster           │                │
│  ap2002.chtc.wisc.edu                │                │
│                                      │                │
│  ┌─────────────────┐    ┌───────────▼──────────┐     │
│  │ /home/nandwani2/│    │     WandB Cloud      │     │
│  │  - projects/    │    │   wandb.ai           │     │
│  │  - jobs/        │    │  - Run tracking      │     │
│  └─────────────────┘    │  - Metrics           │     │
│                         │  - Artifacts         │     │
│  ┌─────────────────┐    └──────────────────────┘     │
│  │/staging/nandwani2│                                 │
│  │  - containers/   │                                 │
│  │  - large data/   │                                 │
│  └─────────────────┘                                  │
│                                                        │
│  ┌─────────────────────────────────┐                  │
│  │   HTCondor Job Scheduler        │                  │
│  │  - Job queue management         │                  │
│  │  - Resource allocation          │                  │
│  └─────────────────────────────────┘                  │
└────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. CLI Layer (bash)

**bin/chtc**
- Main entry point
- Command routing
- User interface

**lib/utils.sh**
- Logging functions
- Configuration loading
- Helper utilities

**lib/ssh.sh**
- SSH ControlMaster management
- Connection pooling
- File transfer (rsync)
- Remote execution

### 2. Feature Scripts (bash + Python)

**scripts/submit.sh** (bash)
- Parse submission arguments
- Upload files to CHTC
- Trigger WandB run creation
- Submit to HTCondor
- Track job-to-run mapping

**scripts/wandb_logger.py** (Python)
- WandB SDK integration
- Run initialization
- Metric logging
- Artifact management
- Log file parsing

**scripts/monitor.sh** (bash)
- Real-time job monitoring
- Queue status display
- WandB URL display

**scripts/fetch_logs.sh** (bash)
- Download job outputs
- Update WandB with results
- Local storage organization

**scripts/container.sh** (bash)
- Interactive build jobs
- Container upload/download
- Staging management

**scripts/project.sh** (bash)
- Project scaffolding
- Bidirectional sync
- Workspace organization

### 3. Templates

**HTCondor Submit Files**
- `basic.sub` - Simple jobs
- `gpu.sub` - GPU jobs
- `wandb.sub` - WandB-enabled jobs

**Container Definitions**
- `pytorch-gpu.def` - PyTorch + CUDA + WandB

**Job Wrappers**
- `wandb_wrapper.sh` - Runtime WandB integration

### 4. Configuration

**~/.chtcrc**
- User credentials
- Path configurations
- Default resources
- WandB API key (already configured)

**~/.chtc/**
- `ssh_control/` - Control sockets
- `wandb_mappings.txt` - Job-to-run links

**~/chtc-workspace/**
- `projects/` - Local project workspace
- `logs/` - Downloaded logs

## Data Flow

### Job Submission Flow

```
1. User: chtc submit job.sub --wandb
                │
2. submit.sh    │
   ├─ Parse args
   ├─ Upload files (SSH)
   ├─ Call wandb_logger.py
   │  └─ Create WandB run → Run ID
   ├─ Submit to HTCondor → Job ID
   └─ Store mapping (Job ID:Run ID)
                │
3. CHTC         │
   ├─ Schedule job
   ├─ Execute with wrapper
   │  └─ Log metrics to WandB
   └─ Save outputs
                │
4. User: chtc logs <job-id>
                │
5. fetch_logs.sh
   ├─ Download logs (SSH)
   ├─ Parse resource usage
   └─ Update WandB run
                │
6. WandB Dashboard
   └─ Complete view of experiment
```

### SSH Connection Management

```
First command:
  chtc connect
    ├─ Prompt for password
    ├─ Duo 2FA
    └─ Establish ControlMaster
       └─ Socket created in ~/.chtc/ssh_control/

Subsequent commands (next 4 hours):
  chtc <any-command>
    └─ Reuse existing socket (no 2FA!)

After 4 hours or disconnect:
  Socket expires → Reconnect on next command
```

## Key Features Explained

### 1. SSH ControlMaster

**Problem**: Every SSH command requires password + 2FA
**Solution**: Master connection persists, slaves reuse it

```bash
# First connection
ssh -fNT -o ControlMaster=yes \
         -o ControlPath=~/.chtc/ssh_control/socket \
         -o ControlPersist=4h \
         user@host

# All future commands
ssh -S ~/.chtc/ssh_control/socket user@host "command"
# ↑ No authentication needed!
```

### 2. WandB Integration Layers

**Layer 1: Submission Tracking**
- Create run when job submitted
- Log submit file, job ID, resources
- Store job-to-run mapping

**Layer 2: Runtime Tracking** (optional)
- User code calls `wandb.init()`
- Logs metrics, checkpoints
- Detects HTCondor environment

**Layer 3: Completion Tracking**
- Fetch logs parses resource usage
- Updates run with actual CPU/memory/time
- Stores outputs as artifacts

### 3. Smart File Transfer

Based on file size, automatically selects:

- **< 1GB**: `transfer_input_files = file.txt`
- **1-30GB**: `transfer_input_files = osdf:///chtc/staging/user/file.tar.gz`
- **30-100GB**: `transfer_input_files = file:///staging/user/big.tar.gz`

### 4. Project Organization

```
~/chtc-workspace/projects/my-research/
├── code/           # Scripts (synced)
├── data/           # Small data (synced)
├── jobs/           # Submit files (synced)
├── results/        # Outputs (pulled)
├── containers/     # Def files (for building)
└── project.yaml    # Metadata
```

Syncs to: `/home/nandwani2/projects/my-research/`

## Security Considerations

1. **WandB API Key**: Stored in `~/.chtcrc` (local file)
2. **SSH Keys**: Can use SSH keys instead of password
3. **Control Socket**: Secured with 0700 permissions
4. **Credentials**: Never logged or transmitted to WandB

## Extension Points

The system is designed to be extended:

1. **Add commands**: Create new script in `scripts/`, add case to `bin/chtc`
2. **Custom templates**: Add `.sub` files to `templates/`
3. **WandB hooks**: Extend `wandb_logger.py` for custom tracking
4. **Container images**: Add `.def` files to `templates/`

## Performance Optimizations

1. **Connection pooling**: Single SSH connection for all ops
2. **Lazy connection**: Only connect when needed
3. **Parallel uploads**: rsync with compression
4. **Local caching**: Job metadata stored locally

## Future Enhancements

Possible additions:
- DAG workflow builder (visual or YAML-based)
- WandB sweep automation for CHTC
- Auto-scaling based on queue depth
- Checkpoint sync during long jobs
- Cost/resource usage analytics
- Multi-cluster support (HTC + HPC)

---

**Philosophy**: Keep it simple. Bash for glue, Python where it makes sense. Local-first, cloud-enhanced.
