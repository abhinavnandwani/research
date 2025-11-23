# MNIST GPU Training Example for CHTC

Complete example of training a neural network on CHTC GPUs with WandB tracking.

## What This Does

- Trains a simple CNN on MNIST dataset
- Uses your existing `scFoundation-container.sif` from staging
- Reports metrics to WandB project `chtc-mnist`
- Saves best model as WandB artifact
- Runs on CHTC GPU nodes

## Files

- `train_mnist.py` - PyTorch training script with WandB integration
- `run_mnist.sh` - Wrapper script that runs inside container
- `mnist.sub` - HTCondor submit file
- `submit_mnist.sh` - Helper script to submit from local machine

## Quick Start

### Method 1: Using CHTC Tools (Recommended)

```bash
cd ~/projects/research/chtc-tools/examples/mnist-gpu

# Create logs directory
mkdir -p logs

# Submit with WandB tracking
../../bin/chtc submit mnist.sub

# Monitor
../../bin/chtc monitor --watch
```

### Method 2: Manual SSH

```bash
# Upload files to CHTC
cd ~/projects/research/chtc-tools/examples/mnist-gpu
scp -r . chtc:~/mnist-example/

# SSH to CHTC
ssh chtc

# Submit
cd ~/mnist-example
mkdir -p logs
condor_submit mnist.sub

# Monitor
condor_q
watch -n 5 condor_q
```

## What Happens

1. **Job starts** on CHTC GPU node
2. **Container loads**: `scFoundation-container.sif` from staging
3. **Script runs**: Downloads MNIST, trains model
4. **WandB tracks**:
   - Training/test loss and accuracy per epoch
   - Batch-level metrics every 100 batches
   - Model architecture
   - GPU information
   - Best model saved as artifact
5. **Results**: View at https://wandb.ai/

## Customization

### Change Hyperparameters

Edit `mnist.sub`:
```bash
arguments = --batch-size 64 --epochs 20 --lr 0.0001
```

### Run Multiple Experiments

```bash
# In mnist.sub, replace queue line with:
queue lr,batch_size from (
    0.001,64
    0.001,128
    0.01,64
    0.01,128
)
```

### Use Different Container

If you want to use a different container:
```bash
# Build a custom one
cd ~/projects/research/chtc-tools
chtc container build templates/pytorch-gpu.def

# Update mnist.sub
container_image = osdf:///chtc/staging/nandwani2/pytorch-gpu.sif
```

## Monitor Training

### Check Queue
```bash
../../bin/chtc queue
# or
ssh chtc "condor_q"
```

### View Logs (while running)
```bash
# Fetch latest logs
../../bin/chtc logs <job-id>

# Or SSH and tail
ssh chtc "tail -f ~/mnist-example/logs/mnist_*.out"
```

### View in WandB
```bash
# Go to https://wandb.ai/
# Navigate to project "chtc-mnist"
# See real-time metrics!
```

## Expected Results

- **Training time**: ~5-10 minutes on GPU
- **Final accuracy**: ~99% on test set
- **GPU usage**: Will show in WandB
- **Outputs**:
  - Logs in `logs/` directory
  - Best model in WandB artifacts
  - Full metrics in WandB dashboard

## Troubleshooting

### Job Goes on Hold

```bash
# Check why
ssh chtc "condor_q -hold"

# Common issues:
# - GPU not available: Wait or reduce request_gpus
# - Memory exceeded: Increase request_memory
# - Disk exceeded: Increase request_disk
```

### Container Issues

```bash
# Verify container exists
ssh chtc "ls -lh /staging/nandwani2/scFoundation-container.sif"

# If missing, use a different container or build one
```

### WandB Not Logging

```bash
# Check API key in mnist.sub
environment = "WANDB_API_KEY=YOUR_KEY_HERE ..."

# Verify inside job
ssh chtc "cat ~/mnist-example/logs/mnist_*.out | grep -i wandb"
```

## Advanced Usage

### Hyperparameter Sweep

Create `sweep.yaml`:
```yaml
program: train_mnist.py
method: bayes
metric:
  name: test_acc
  goal: maximize
parameters:
  lr:
    distribution: log_uniform_values
    min: 0.0001
    max: 0.01
  batch_size:
    values: [32, 64, 128, 256]
```

Then:
```bash
# Initialize sweep
wandb sweep sweep.yaml
# Get sweep ID

# Run agents on CHTC
# Modify mnist.sub to run: wandb agent SWEEP_ID
# queue 10  # Run 10 parallel agents
```

### Longer Training

For longer experiments:
```bash
# Add checkpointing to train_mnist.py (already included!)
# Job will save checkpoint every epoch

# In mnist.sub, increase limits
arguments = --batch-size 128 --epochs 50
request_memory = 32GB
```

### Multi-GPU (if available)

```bash
# In mnist.sub
request_gpus = 2

# Modify train_mnist.py to use DataParallel
# model = nn.DataParallel(model)
```

## Files Generated

After job completes:
- `logs/mnist_XXXXX_0.log` - HTCondor log with resource usage
- `logs/mnist_XXXXX_0.out` - Standard output (training progress)
- `logs/mnist_XXXXX_0.err` - Standard error (if any)
- `best_model.pth` - Best model (also in WandB artifacts)

## WandB Dashboard

Your WandB project will show:
- Training curves (loss, accuracy)
- GPU utilization
- System metrics
- Model architecture
- Hyperparameters
- Job metadata (HTCondor job ID, GPU name, etc.)
- Model artifacts

## Next Steps

1. **Try it**: Submit the job and watch it train!
2. **Customize**: Modify hyperparameters, try different architectures
3. **Scale**: Run parameter sweeps with multiple jobs
4. **Optimize**: Use the metrics to improve your model

## Resources

- WandB Project: https://wandb.ai/ (project: `chtc-mnist`)
- CHTC GPU Guide: `../../docs/guides/gpu-jobs.md`
- Container Guide: `../../docs/guides/containers.md`
- Troubleshooting: `../../docs/troubleshooting/job-holds.md`
