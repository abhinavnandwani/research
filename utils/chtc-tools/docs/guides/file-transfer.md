# File Transfer Guide

Complete guide to managing file transfers on CHTC HTC system.

## Overview

CHTC provides multiple file transfer methods optimized for different file sizes and use cases.

## File Size Decision Tree

```
Input File Size?
├── < 100 MB
│   └── Use: HTCondor standard transfer (transfer_input_files)
│       Location: /home/username/
│
├── 100 MB - 1 GB
│   └── Use: HTCondor standard transfer
│       Location: /home/username/
│       Consider: Moving to /staging/ for frequently used files
│
├── 1 GB - 30 GB
│   └── Use: OSDF protocol (osdf:///)
│       Location: /staging/username/
│       Syntax: osdf:///chtc/staging/username/file.tar.gz
│
├── 30 GB - 100 GB
│   └── Use: file:/// protocol
│       Location: /staging/username/
│       Syntax: file:///staging/username/large-file.tar
│
└── > 100 GB
    └── Contact CHTC facilitators (chtc@cs.wisc.edu)
        Special staging arrangements needed
```

## Storage Locations

### /home/username/

**Purpose**: Default workspace for small files and job submission
**Quota**: 40 GB
**Best for**:
- Submit files (.sub)
- Small scripts and executables
- Output files < 4 GB
- Many small files

**Characteristics**:
- Optimized for small file transfers
- Fast access
- Limited space

### /staging/username/

**Purpose**: Large file staging area
**Quota**: 100 GB, max 1000 files
**Best for**:
- Individual files > 1 GB
- Containers (.sif files)
- Large datasets
- Compressed archives

**Characteristics**:
- Optimized for large files
- Slower for many small files
- Not backed up - remove when done

## Transfer Methods

### 1. HTCondor Standard Transfer (< 1 GB)

**Best for**: Small files stored in /home/

**Submit file syntax**:
```bash
transfer_input_files = script.py, data.csv, config.json
should_transfer_files = YES
when_to_transfer_output = ON_EXIT
```

**Multiple files**:
```bash
transfer_input_files = file1.txt, file2.dat, directory/
```

**Example**:
```bash
# Simple job with small inputs
executable = process.sh
transfer_input_files = input.csv, parameters.json

log = job.log
error = job.err
output = job.out

request_cpus = 1
request_memory = 4GB
request_disk = 5GB

queue 1
```

### 2. OSDF Protocol (1-30 GB)

**Best for**: Large files with caching benefits

**Submit file syntax**:
```bash
transfer_input_files = osdf:///chtc/staging/username/large-data.tar.gz
Requirements = (Target.HasCHTCStaging == true)
```

**Advantages**:
- Automatic caching for frequently used files
- Faster repeated transfers
- Network optimization

**Caveats**:
- May cache older versions of frequently modified files
- Rename files or change paths to force fresh transfer

**Auto-unpacking** (< 30 GB compressed files):
```bash
transfer_input_files = osdf:///chtc/staging/username/archive.tar.gz?pack=auto
```
This automatically unpacks during transfer, saving disk space.

**Example**:
```bash
# Job using large dataset from staging
executable = train.sh
transfer_input_files = \
    osdf:///chtc/staging/nandwani2/training-data.tar.gz?pack=auto, \
    osdf:///chtc/staging/nandwani2/my-container.sif, \
    local-script.py

Requirements = (Target.HasCHTCStaging == true)

request_cpus = 4
request_memory = 16GB
request_disk = 50GB
request_gpus = 1

queue 1
```

### 3. file:/// Protocol (30-100 GB)

**Best for**: Very large files

**Submit file syntax**:
```bash
transfer_input_files = file:///staging/username/huge-dataset.tar
Requirements = (Target.HasCHTCStaging == true)
```

**Example**:
```bash
# Job with very large input
executable = analyze.sh
transfer_input_files = file:///staging/nandwani2/genomic-data.tar

Requirements = (Target.HasCHTCStaging == true)

request_cpus = 8
request_memory = 64GB
request_disk = 150GB

queue 1
```

### 4. Container Images

**Always use OSDF for containers**:
```bash
container_image = osdf:///chtc/staging/username/pytorch-gpu.sif
Requirements = (Target.HasCHTCStaging == true)
```

## Output Files

### Standard Output (< 4 GB)

Automatically transferred back:
```bash
# Anything created in job working directory comes back
output = job.out
error = job.err
```

### Large Output to /staging

Use `transfer_output_remaps`:
```bash
# Remap large outputs to staging
transfer_output_remaps = "large-results.tar=/staging/username/results-$(Cluster).tar"
```

**Size-based protocol**:
```bash
# For 1-30 GB outputs
transfer_output_remaps = "results.tar=osdf:///chtc/staging/username/results-$(Cluster).tar"

# For 30-100 GB outputs
transfer_output_remaps = "huge-output.tar=file:///staging/username/output-$(Cluster).tar"
```

## Managing Files in /staging

### Uploading to /staging

**From CHTC access point**:
```bash
# SSH to CHTC first
ssh chtc

# Copy from /home to /staging
cp /home/username/large-file.tar.gz /staging/username/
```

**From local machine using CHTC tools**:
```bash
# Upload directly to staging
chtc upload local-data.tar.gz /staging/nandwani2/
```

**Using rsync directly**:
```bash
rsync -avz large-dataset.tar user@ap2002.chtc.wisc.edu:/staging/username/
```

### Checking /staging Usage

```bash
# From CHTC
du -sh /staging/username/

# Using CHTC tools
chtc exec "du -sh /staging/nandwani2/"
```

### Cleaning Up /staging

**IMPORTANT**: Remove files from /staging when no longer needed!

```bash
# On CHTC
rm /staging/username/old-data.tar.gz

# Using CHTC tools
chtc exec "rm /staging/nandwani2/old-data.tar.gz"
```

## Best Practices

### 1. Compress Large Files

```bash
# Tar and compress before uploading
tar -czf dataset.tar.gz dataset/

# Submit file
transfer_input_files = osdf:///chtc/staging/username/dataset.tar.gz?pack=auto
```

### 2. Bundle Small Files

Don't transfer many small files individually:
```bash
# Bad - slow!
transfer_input_files = file1.txt, file2.txt, ..., file1000.txt

# Good - fast!
# First: tar -czf inputs.tar.gz *.txt
transfer_input_files = inputs.tar.gz
```

Then unpack in your job script:
```bash
#!/bin/bash
tar -xzf inputs.tar.gz
# Now process files
```

### 3. Never Submit from /staging

```bash
# WRONG - Don't do this!
cd /staging/username/
condor_submit job.sub

# CORRECT - Always submit from /home
cd /home/username/
condor_submit job.sub
```

### 4. Use Relative Paths

```bash
# In submit file, use relative paths
transfer_input_files = ../data/input.csv

# Or explicit /staging paths
transfer_input_files = osdf:///chtc/staging/username/data.tar.gz
```

### 5. Verify File Presence

Before submitting, verify files exist:
```bash
# Check if file is in staging
ssh chtc "ls -lh /staging/nandwani2/my-data.tar.gz"

# Or using tools
chtc exec "test -f /staging/nandwani2/my-data.tar.gz && echo 'File exists' || echo 'File missing'"
```

## Common Transfer Patterns

### Pattern 1: Small Code + Large Data

```bash
executable = train.py
transfer_input_files = \
    osdf:///chtc/staging/username/training-data.tar.gz?pack=auto, \
    requirements.txt, \
    config.yaml

Requirements = (Target.HasCHTCStaging == true)
```

### Pattern 2: Container + Data

```bash
container_image = osdf:///chtc/staging/username/ml-container.sif
transfer_input_files = \
    file:///staging/username/huge-dataset.tar, \
    run-script.sh

Requirements = (Target.HasCHTCStaging == true)
```

### Pattern 3: Multiple Datasets (One Per Job)

```bash
executable = process.sh
arguments = $(dataset)

transfer_input_files = osdf:///chtc/staging/username/$(dataset)

Requirements = (Target.HasCHTCStaging == true)

queue dataset from (
    data-part1.tar.gz
    data-part2.tar.gz
    data-part3.tar.gz
)
```

## Monitoring Transfers

### Check Transfer Status in Logs

Job log files show transfer timing:
```
005 (12345.000.000) 2025-11-23 16:30:00 Job submitted
...
001 (12345.000.000) 2025-11-23 16:35:00 Job executing on host
    Transferring input files: 5.2 GB (took 45 seconds)
...
```

### Debug Transfer Failures

If transfer fails, check:
1. File exists: `ssh chtc "ls -lh /path/to/file"`
2. Path is correct (absolute vs relative)
3. Quota not exceeded: `chtc quota`
4. Permissions: `ssh chtc "ls -l /path/to/file"`

## Quota Management

### Check Current Usage

```bash
# Home directory
chtc quota

# Staging directory
chtc exec "du -sh /staging/nandwani2/"
```

### Approaching Limits

If near quota:
1. Remove old job files
2. Clean up /staging
3. Move large files to external storage
4. Compress files

```bash
# Find large files in home
chtc exec "find /home/nandwani2 -type f -size +100M -exec ls -lh {} \\;"

# Find large files in staging
chtc exec "find /staging/nandwani2 -type f -size +1G -exec ls -lh {} \\;"
```

## Advanced Topics

### Shared Group Staging

If you have group staging access:
```bash
transfer_input_files = file:///staging/groups/group_name/shared-data.tar
```

### Multiple Transfer Protocols

Mix protocols as needed:
```bash
transfer_input_files = \
    local-script.sh, \
    osdf:///chtc/staging/username/medium-data.tar.gz, \
    file:///staging/username/huge-data.tar, \
    osdf:///chtc/staging/username/container.sif
```

### Checksums and Verification

Verify large transfers:
```bash
# Create checksum before upload
md5sum large-file.tar.gz > large-file.md5

# After upload to CHTC
ssh chtc "cd /staging/username && md5sum -c large-file.md5"
```

## Troubleshooting

See [File Transfer Troubleshooting](../troubleshooting/file-transfer.md) for common issues and solutions.

## Sources and Further Reading

- [CHTC File Transfer Documentation](https://chtc.cs.wisc.edu/uw-research-computing/htc-job-file-transfer)
- [CHTC Staging Guide](https://chtc.cs.wisc.edu/uw-research-computing/file-avail-largedata)
- [OSDF Transfer Documentation](https://portal.osg-htc.org/documentation/htc_workloads/managing_data/osdf/)
- [HTCondor File Transfer](https://htcondor.readthedocs.io/en/latest/users-manual/submitting-a-job.html#transferring-files)
