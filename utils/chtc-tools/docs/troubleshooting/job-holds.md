# Job Holds - Troubleshooting Guide

Complete guide to understanding and fixing HTCondor job holds.

## What are Job Holds?

When a job goes on hold, HTCondor stops trying to run it. The job stays in the queue but won't be matched to resources until the problem is fixed and the job is released.

## Viewing Held Jobs

### Check if You Have Held Jobs

```bash
# Show all your jobs (look for "H" status)
chtc queue

# Show only held jobs
ssh chtc "condor_q -hold"

# Detailed info on specific job
ssh chtc "condor_q -hold JobID"
```

### Reading Hold Reasons

**From condor_q**:
```bash
ssh chtc "condor_q -hold 12345.0"
```

**From job log file**:
```bash
# Download and check log
chtc logs 12345
grep -i "hold" job_12345_0.log
```

## Common Hold Reasons and Solutions

### 1. Memory Exceeded

**Error**:
```
Error from slot: memory usage exceeded request_memory
Job was held because it used 8192 MB but only requested 4096 MB
```

**Cause**: Job used more memory than requested

**Solution**:
```bash
# Release job with more memory
ssh chtc "condor_qedit 12345 request_memory 16384"
ssh chtc "condor_release 12345"

# Or edit submit file and resubmit
request_memory = 16GB  # Increase this
```

**How to determine correct memory**:
1. Check log file for actual usage
2. Add 20-30% buffer
3. Common values: 4GB, 8GB, 16GB, 32GB, 64GB

### 2. Disk Space Exceeded

**Error**:
```
Error from slot: disk usage exceeded request_disk
Job was held because it used 15000000 KB but only requested 5000000 KB
```

**Cause**: Job wrote more data than requested disk space

**Solution**:
```bash
# Edit submit file
request_disk = 20GB  # Increase this

# Resubmit
condor_submit job.sub
```

**Prevention**:
- Don't write unnecessary temp files
- Compress large outputs
- Clean up intermediate files in your script

### 3. Job Duration Exceeded

**Error**:
```
Job was held because it exceeded allowed execute duration of 72:00:00
```

**Cause**: Job ran longer than 72-hour limit

**Solutions**:
1. **Optimize your code** (best option)
2. **Checkpoint and restart**:
   ```python
   # Save progress periodically
   if os.path.exists('checkpoint.pkl'):
       state = load_checkpoint()
   # ... work ...
   save_checkpoint(state)
   ```
3. **Break into smaller jobs** (use DAG)

### 4. File Transfer Failure

**Error**:
```
Error from starter: failed to transfer files
Transfer input files failure: reading from file /path/to/file: No such file or directory
```

**Cause**: Input file doesn't exist or path is wrong

**Solutions**:
```bash
# Verify file exists
ssh chtc "ls -lh /home/nandwani2/myfile.txt"
ssh chtc "ls -lh /staging/nandwani2/data.tar.gz"

# Check path in submit file
# Relative paths are relative to submit file location
transfer_input_files = ../data/input.csv  # Check this

# For staging files, verify syntax
transfer_input_files = osdf:///chtc/staging/nandwani2/data.tar.gz
Requirements = (Target.HasCHTCStaging == true)  # Don't forget this!
```

### 5. Job Killed by Signal

**Error**:
```
Job was held because it was killed by signal 9 (SIGKILL)
```

**Causes and Solutions**:

**Out of memory kill**:
- Check actual memory used in log
- Increase `request_memory`

**User/admin kill**:
- Check if you hit resource limits
- Contact CHTC support

**Node failure**:
- Usually transient
- Release and retry: `condor_release JobID`

### 6. Cannot Initialize User Log

**Error**:
```
Failed to initialize user log to /path/to/job.log
```

**Cause**: Can't create log file (permissions, path doesn't exist)

**Solution**:
```bash
# Check directory exists
ssh chtc "mkdir -p ~/logs"

# Fix submit file
log = logs/job_$(Cluster).log  # Ensure directory exists

# Or use absolute path
log = /home/nandwani2/logs/job_$(Cluster).log
```

### 7. Executable Not Found

**Error**:
```
Failed to execute '/path/to/script.sh': No such file or directory
```

**Solutions**:
```bash
# Make sure executable is transferred
transfer_input_files = script.sh, other_files

# Or if using container
container_image = osdf:///chtc/staging/username/container.sif
Requirements = (Target.HasCHTCStaging == true)

# Verify execute permission
chmod +x script.sh  # Before transferring
```

### 8. Shadow Exception

**Error**:
```
Error from shadow: SHADOW failed to receive file(s)
```

**Cause**: Network issue or output file problem

**Solutions**:
- Usually transient - release and retry
- Check output file size (< 4GB limit)
- For large outputs, use `transfer_output_remaps` to /staging

### 9. Periodic Hold

**Error**:
```
Job held due to periodic_hold expression
```

**Cause**: Custom periodic hold policy (resource monitoring)

**Check why**:
```bash
ssh chtc "condor_q -l JobID | grep -i hold"
```

**Common reasons**:
- Exceeded ImageSize limit
- Job idle too long
- Custom requirements not met

### 10. Submit File Error

**Error**:
```
ERROR: Failed to parse submit file
```

**Cause**: Syntax error in .sub file

**Solutions**:
```bash
# Check for common issues:
# - Missing quotes around paths with spaces
# - Unmatched quotes
# - Invalid attribute names
# - Missing equals signs

# Good
arguments = "input file.txt" output.txt

# Bad
arguments = input file.txt output.txt  # Needs quotes!

# Validate before submitting
ssh chtc "condor_submit -dry-run job.sub"
```

## Automatic Release

**CHTC Policy**: Jobs automatically released after 60 minutes in hold, up to 12 times.

**Check auto-release count**:
```bash
ssh chtc "condor_q -l JobID | grep NumJobStarts"
```

If `NumJobStarts >= 12`, job won't auto-release anymore.

## Manual Job Management

### Release Held Job

```bash
# Release specific job
ssh chtc "condor_release 12345.0"

# Release all your held jobs
ssh chtc "condor_release \$USER"

# Release specific cluster
ssh chtc "condor_release 12345"
```

### Remove Held Job

If unfixable, remove it:
```bash
# Remove specific job
ssh chtc "condor_rm 12345.0"

# Remove all held jobs
ssh chtc "condor_rm -constraint 'JobStatus == 5' \$USER"
```

### Edit Running/Held Job

```bash
# Change memory request
ssh chtc "condor_qedit 12345 request_memory 16384"

# Change disk request
ssh chtc "condor_qedit 12345 request_disk 20971520"  # In KB

# Then release
ssh chtc "condor_release 12345"
```

## Preventing Holds

### 1. Test with Small Jobs First

```bash
# Instead of queue 1000
queue 10  # Test first!

# Check if they complete
# Then scale up
queue 1000
```

### 2. Request Adequate Resources

**Memory**:
- Start conservative: 4GB
- Monitor actual usage in logs
- Add 20-30% buffer

**Disk**:
- Calculate: inputs + outputs + temp files
- Add 50% buffer for safety

**Example**:
```bash
# Inputs: 5GB
# Outputs: 3GB
# Temp files: 2GB
# Total: 10GB + 50% = 15GB
request_disk = 15GB
```

### 3. Validate Inputs Before Submitting

```bash
# Check files exist
ssh chtc "ls -lh /staging/nandwani2/my-data.tar.gz"

# Verify submit file syntax
ssh chtc "condor_submit -dry-run job.sub"
```

### 4. Handle Errors in Your Script

```bash
#!/bin/bash
set -e  # Exit on error

# Check prerequisites
if [ ! -f input.csv ]; then
    echo "ERROR: input.csv not found"
    exit 1
fi

# Your processing
python process.py input.csv

# Verify output created
if [ ! -f output.csv ]; then
    echo "ERROR: output.csv not created"
    exit 1
fi

echo "Success!"
exit 0
```

### 5. Use Checkpointing for Long Jobs

```python
import pickle
import os

CHECKPOINT_FILE = 'checkpoint.pkl'

# Load checkpoint if exists
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE, 'rb') as f:
        state = pickle.load(f)
    start_epoch = state['epoch'] + 1
else:
    start_epoch = 0

# Training loop
for epoch in range(start_epoch, total_epochs):
    # ... training ...

    # Save checkpoint every N epochs
    if epoch % 10 == 0:
        with open(CHECKPOINT_FILE, 'wb') as f:
            pickle.dump({
                'epoch': epoch,
                'model_state': model.state_dict(),
                # ... other state ...
            }, f)
```

## Debugging Workflow

When job goes on hold:

1. **Check hold reason**:
   ```bash
   ssh chtc "condor_q -hold JobID"
   ```

2. **Read log file**:
   ```bash
   chtc logs JobID
   grep -i "hold\\|error\\|fail" job.log
   ```

3. **Identify root cause** (use this guide)

4. **Fix the issue**:
   - Edit submit file if needed
   - Verify files exist
   - Increase resources

5. **Release or resubmit**:
   ```bash
   # If you can fix without resubmitting
   ssh chtc "condor_qedit JobID request_memory 16384"
   ssh chtc "condor_release JobID"

   # Otherwise
   ssh chtc "condor_rm JobID"
   # Edit job.sub
   condor_submit job.sub
   ```

6. **Monitor**:
   ```bash
   chtc monitor --watch
   ```

## Hold Reason Reference

| HoldReasonCode | Meaning |
|---|---|
| 1 | User request |
| 3 | Periodic hold expression |
| 6 | Error staging input files |
| 12 | Error running job |
| 13 | Unable to open input file |
| 16 | Input file transfer failure |
| 21 | Memory exceeded |
| 34 | Job policy expression held job |

## Getting Help

If you can't resolve a hold:

1. **Check CHTC documentation**
2. **Email CHTC support**: chtc@cs.wisc.edu
   - Include JobID
   - Include hold reason
   - Include submit file
   - Include log file

3. **Office hours**:
   - Tuesdays 10:30am-12pm
   - Thursdays 3-4:30pm

## Sources

- [HTCondor Troubleshooting Guide](https://htcondor.readthedocs.io/en/main/users-manual/troubleshooting.html)
- [CHTC Documentation](https://chtc.cs.wisc.edu/uw-research-computing/)
- [OSG Troubleshooting](https://osg-htc.org/user-school-2023/materials/troubleshooting/files/OSGUS2023_troubleshooting.pdf)
