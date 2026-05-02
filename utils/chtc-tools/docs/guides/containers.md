# Container Guide

Complete guide to using Apptainer (formerly Singularity) containers on CHTC.

## Why Use Containers?

Containers provide:
- **Portability**: Same software environment everywhere
- **Reproducibility**: Exact versions of all dependencies
- **Isolation**: No conflicts with system libraries
- **Flexibility**: Use any software, even if not installed on CHTC

## Container Basics

### What is Apptainer?

Apptainer (formerly Singularity) is a container system designed for HPC environments. Unlike Docker, it:
- Runs without root privileges
- Integrates with HPC schedulers (HTCondor)
- Supports GPU passthrough
- Uses a single .sif image file

### Container Image (.sif file)

A `.sif` (Singularity Image Format) file contains:
- Operating system (usually Ubuntu or similar)
- All software and libraries
- Python packages, CUDA libraries, etc.
- Your application code (optional)

## Quick Start

### Using an Existing Container

**Submit file**:
```bash
# Use container from staging
container_image = osdf:///chtc/staging/nandwani2/pytorch-gpu.sif

executable = train.sh
arguments = experiment-01

transfer_input_files = train.py, data.tar.gz

Requirements = (Target.HasCHTCStaging == true)

request_cpus = 4
request_memory = 16GB
request_disk = 40GB
request_gpus = 1

queue 1
```

Your job will run inside the container automatically!

## Building Containers on CHTC

### Why Build on CHTC?

- Building containers requires significant resources
- CHTC provides dedicated build nodes
- Ensures compatibility with CHTC execution nodes

### Building Process

**1. Create a Definition File (.def)**

Example `pytorch-gpu.def`:
```dockerfile
Bootstrap: docker
From: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

%post
    # Update system
    apt-get update && apt-get install -y \\
        git \\
        wget \\
        vim \\
        && rm -rf /var/lib/apt/lists/*

    # Install Python packages
    pip install --no-cache-dir \\
        wandb \\
        numpy \\
        pandas \\
        scikit-learn \\
        matplotlib \\
        seaborn \\
        tqdm

%environment
    export PYTHONUNBUFFERED=1
    export WANDB_DIR=/tmp/wandb

%runscript
    exec python "$@"

%labels
    Author Your Name
    Version 1.0

%help
    PyTorch 2.1.0 container with CUDA 12.1 and WandB.

    Usage:
        apptainer exec --nv container.sif python script.py
```

**2. Use CHTC Tools to Build**

```bash
# Build container on CHTC
chtc container build pytorch-gpu.def
```

This will:
1. Upload your .def file
2. Start an interactive build job
3. Build the container
4. Test it
5. Move it to /staging automatically

**3. Manual Building (Advanced)**

If you need more control:

```bash
# Connect to CHTC
ssh chtc

# Create build directory
mkdir -p ~/container-builds
cd ~/container-builds

# Upload your .def file
# (or create it directly on CHTC)

# Create build submit file
cat > build.sub <<EOF
universe = vanilla
executable = /usr/bin/hostname

transfer_input_files = pytorch-gpu.def

request_cpus = 4
request_memory = 16GB
request_disk = 16GB

+IsBuildJob = true

queue 1
EOF

# Submit interactive build job
condor_submit -i build.sub

# Once in interactive session:
apptainer build pytorch-gpu.sif pytorch-gpu.def

# Test the container
apptainer shell -e pytorch-gpu.sif
# Inside container, test your software

# Move to staging
mv pytorch-gpu.sif /staging/nandwani2/

# Exit interactive session
exit
```

## Container Definition Files

### Basic Structure

```dockerfile
Bootstrap: docker|library|shub
From: image:tag

%post
    # Commands run during build
    # Install software here

%environment
    # Environment variables

%runscript
    # Default command when running container

%labels
    # Metadata

%help
    # Help text
```

### Bootstrap Sources

**From Docker Hub**:
```dockerfile
Bootstrap: docker
From: ubuntu:22.04
```

**From NVIDIA NGC**:
```dockerfile
Bootstrap: docker
From: nvcr.io/nvidia/pytorch:24.02-py3
```

**From Rocker (R)**:
```dockerfile
Bootstrap: docker
From: rocker/tidyverse:4.3.0
```

### Common Base Images

**Python**:
```dockerfile
Bootstrap: docker
From: python:3.10-slim
```

**PyTorch with GPU**:
```dockerfile
Bootstrap: docker
From: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
```

**TensorFlow with GPU**:
```dockerfile
Bootstrap: docker
From: tensorflow/tensorflow:2.15.0-gpu
```

**Conda-based**:
```dockerfile
Bootstrap: docker
From: continuumio/miniconda3:latest
```

## GPU Containers

### CUDA Version Compatibility

**Critical**: Container CUDA version must match or be lower than host driver version.

Check CHTC GPU node drivers:
```bash
# Typical CHTC GPU nodes support CUDA 12.x
```

**Safe approach**: Use slightly older CUDA versions (11.8, 12.0, 12.1)

### GPU Container Requirements

**Submit file must include**:
```bash
# Container with GPU support
container_image = osdf:///chtc/staging/username/gpu-container.sif

# Request GPU
request_gpus = 1

# Ensure CUDA capability
Requirements = (Target.HasCHTCStaging == true) && (TARGET.CUDACapability >= 5.0)

request_cpus = 1
request_memory = 16GB
request_disk = 40GB
```

### GPU Container Definition

```dockerfile
Bootstrap: docker
From: nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

%post
    # Install Python
    apt-get update && apt-get install -y \\
        python3 \\
        python3-pip \\
        && rm -rf /var/lib/apt/lists/*

    # Install CUDA-enabled packages
    pip3 install --no-cache-dir \\
        torch torchvision torchaudio \\
            --index-url https://download.pytorch.org/whl/cu121 \\
        transformers \\
        accelerate

%environment
    export CUDA_VISIBLE_DEVICES=${CUDA_VISIBLE_DEVICES:-0}
    export PYTHONUNBUFFERED=1

%runscript
    exec python3 "$@"
```

### Testing GPU Access

Inside container:
```python
import torch
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA device: {torch.cuda.get_device_name(0)}")
```

## Advanced Container Topics

### Installing Conda in Container

```dockerfile
Bootstrap: docker
From: ubuntu:22.04

%post
    # Install Miniconda
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda
    rm Miniconda3-latest-Linux-x86_64.sh

    # Update PATH
    export PATH="/opt/conda/bin:$PATH"

    # Create environment
    conda create -n myenv python=3.10 -y
    conda activate myenv
    conda install pytorch torchvision -c pytorch -y

%environment
    export PATH="/opt/conda/bin:$PATH"

%runscript
    #!/bin/bash
    source /opt/conda/etc/profile.d/conda.sh
    conda activate myenv
    exec python "$@"
```

### Multi-Stage Builds

For smaller final images:
```dockerfile
# Build stage (not possible in Apptainer - use Docker then convert)
# See "Converting Docker to Apptainer" section
```

### Adding Your Code

**Option 1: Include in container**:
```dockerfile
%files
    /path/on/build-system/code /opt/myapp/

%post
    cd /opt/myapp
    pip install -e .
```

**Option 2: Transfer separately (recommended)**:
```bash
# Submit file
container_image = osdf:///chtc/staging/username/env-only.sif
transfer_input_files = mycode.tar.gz, run.sh
```

This keeps container reusable and code flexible.

## Converting Docker to Apptainer

If you have a Docker image:

**Method 1: Direct conversion (on CHTC build node)**:
```bash
# In interactive build job
apptainer build mycontainer.sif docker://username/image:tag
```

**Method 2: Pull from Docker Hub**:
```bash
apptainer build pytorch.sif docker://pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime
```

**Method 3: Pull from NVIDIA NGC**:
```bash
apptainer build tensorflow.sif docker://nvcr.io/nvidia/tensorflow:24.02-tf2-py3
```

## Best Practices

### 1. Keep Containers Small

- Use slim base images
- Clean up after installs:
  ```dockerfile
  %post
      apt-get install -y package \\
          && rm -rf /var/lib/apt/lists/*
  ```
- Don't include data in container

### 2. Pin Versions

```dockerfile
%post
    pip install --no-cache-dir \\
        torch==2.1.0 \\
        transformers==4.35.0 \\
        wandb==0.16.0
```

### 3. Use Environment Variables

```dockerfile
%environment
    export PYTHONUNBUFFERED=1
    export TOKENIZERS_PARALLELISM=false
    export OMP_NUM_THREADS=1
```

### 4. CUDA Version Strategy

For maximum compatibility:
```dockerfile
# Use slightly older CUDA
Bootstrap: docker
From: nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
```

### 5. Test Locally First (if possible)

If you have Docker locally:
```bash
# Build with Docker first
docker build -t test:latest -f Dockerfile.

# Test
docker run --gpus all test:latest python test.py

# Convert to Apptainer on CHTC
```

### 6. Document Your Container

```dockerfile
%labels
    Author "Your Name"
    Version "1.0"
    Description "PyTorch 2.1 with CUDA 12.1"
    CUDA_Version "12.1"
    Python_Version "3.10"

%help
    This container provides PyTorch 2.1.0 with CUDA 12.1 support.

    Usage in HTCondor submit file:
        container_image = osdf:///chtc/staging/username/pytorch.sif
        request_gpus = 1
        Requirements = (HasCHTCStaging == true) && (CUDACapability >= 5.0)

    Test GPU access:
        apptainer exec --nv pytorch.sif python -c "import torch; print(torch.cuda.is_available())"
```

## Container Management

### List Containers

```bash
# Using CHTC tools
chtc container list

# Manually
ssh chtc "ls -lh /staging/nandwani2/*.sif"
```

### Download Container

```bash
# To local machine
chtc container download pytorch-gpu.sif ./containers/
```

### Delete Old Containers

```bash
chtc container delete old-container.sif
```

## Common Container Patterns

### Pattern 1: Python Data Science

```dockerfile
Bootstrap: docker
From: python:3.10-slim

%post
    pip install --no-cache-dir \\
        numpy pandas scikit-learn \\
        matplotlib seaborn \\
        jupyter notebook

%environment
    export PYTHONUNBUFFERED=1
```

### Pattern 2: R with Tidyverse

```dockerfile
Bootstrap: docker
From: rocker/tidyverse:4.3.0

%post
    R -e "install.packages(c('caret', 'randomForest'))"
```

### Pattern 3: PyTorch Research

```dockerfile
Bootstrap: docker
From: pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime

%post
    pip install --no-cache-dir \\
        transformers accelerate \\
        datasets tokenizers \\
        wandb tensorboard \\
        scikit-learn pandas

%environment
    export PYTHONUNBUFFERED=1
    export TRANSFORMERS_CACHE=/tmp/transformers
    export HF_HOME=/tmp/huggingface
```

### Pattern 4: TensorFlow ML

```dockerfile
Bootstrap: docker
From: tensorflow/tensorflow:2.15.0-gpu

%post
    pip install --no-cache-dir \\
        keras-tuner \\
        tensorflow-datasets \\
        wandb

%environment
    export TF_CPP_MIN_LOG_LEVEL=2
    export PYTHONUNBUFFERED=1
```

## Troubleshooting

### Container Won't Build

**Error**: "FATAL: Unable to build from URI"
- Check internet connection on build node
- Verify Docker image exists
- Try different base image

**Error**: "insufficient space"
- Request more disk: `request_disk = 32GB`
- Clean up before building: `rm -rf /var/lib/apt/lists/*`

### Container Won't Run

See [Container Troubleshooting](../troubleshooting/container-issues.md)

### GPU Not Detected

**Check**:
1. Submit file has `request_gpus = 1`
2. CUDA version compatible
3. Using `--nv` flag (HTCondor does this automatically)

## Sources and Further Reading

- [CHTC Apptainer Guide](https://chtc.cs.wisc.edu/uw-research-computing/apptainer-htc)
- [CHTC Container Building](https://chtc.cs.wisc.edu/uw-research-computing/apptainer-build)
- [Apptainer User Guide](https://apptainer.org/docs/user/latest/)
- [GPU Container Guide](https://apptainer.org/docs/user/1.0/gpu.html)
- [NVIDIA NGC Containers](https://catalog.ngc.nvidia.com/)
- [CHTC GPU Jobs](https://chtc.cs.wisc.edu/uw-research-computing/gpu-jobs)
