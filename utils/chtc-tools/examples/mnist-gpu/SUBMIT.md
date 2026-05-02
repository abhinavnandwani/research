# How to Submit MNIST Job to CHTC

## The Point

Everything runs on CHTC using your existing `scFoundation-container.sif` container.
**No local installation needed!**

## Quick Submit

```bash
cd ~/projects/research/chtc-tools/examples/mnist-gpu

# Just run this:
./submit_mnist.sh
```

That's it! The script will:
1. Upload files to CHTC
2. Submit the job
3. Give you the job ID and monitoring commands

## What Happens on CHTC

1. Job starts on GPU node
2. Loads your container: `/staging/nandwani2/scFoundation-container.sif`
3. Container has PyTorch + CUDA already installed
4. Runs `train_mnist.py` inside container
5. Logs to WandB project `chtc-mnist`

## Monitor

```bash
# Watch queue
../../bin/chtc monitor --watch

# Or manually
ssh chtc "condor_q"

# View WandB
open https://wandb.ai/
```

## Files Submitted to CHTC

- `train_mnist.py` - Training script
- `run_mnist.sh` - Wrapper that runs inside container
- `mnist.sub` - HTCondor submit file

**Container is already on CHTC** - not uploaded!

## Customization

Edit arguments in `mnist.sub`:
```bash
arguments = --batch-size 128 --epochs 15 --lr 0.001
```

Then resubmit:
```bash
./submit_mnist.sh
```
