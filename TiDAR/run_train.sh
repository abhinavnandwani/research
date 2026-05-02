#!/bin/bash
# Wrapper script to run TiDAR training on CHTC

set -e

echo "=========================================="
echo "TiDAR Training on CHTC"
echo "=========================================="
echo "Job ID: ${CLUSTER:-local}"
echo "Process ID: ${PROCESS:-0}"
echo "Host: $(hostname)"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Check Python and PyTorch availability
echo "Checking Python environment..."
python3 --version
echo ""

echo "Checking PyTorch installation..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')"
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
if python3 -c "import torch; exit(0 if torch.cuda.is_available() else 1)"; then
    python3 -c "import torch; print(f'CUDA device: {torch.cuda.get_device_name(0)}')"
    python3 -c "import torch; print(f'CUDA version: {torch.version.cuda}')"
fi
echo ""

# Install dependencies if needed
echo "Checking dependencies..."
python3 -c "import wandb" 2>/dev/null || {
    echo "Installing WandB..."
    pip install --user wandb
}

python3 -c "import tqdm" 2>/dev/null || {
    echo "Installing tqdm..."
    pip install --user tqdm
}
echo ""

# Set WandB API key from environment
if [ -z "$WANDB_API_KEY" ]; then
    echo "WARNING: WANDB_API_KEY not set!"
else
    echo "WandB API key configured"
fi

# Run training
echo "Starting TiDAR training..."
echo ""

python3 train_tidar.py \
    --vocab-size 256 \
    --hidden-size 512 \
    --num-layers 8 \
    --num-heads 8 \
    --block-size 4 \
    --alpha 1.0 \
    --epochs 20 \
    --batch-size 64 \
    --seq-len 128 \
    --lr 3e-4 \
    --text-size 200000 \
    --wandb-project tidar-chtc \
    --save-dir ./checkpoints \
    "$@"

echo ""
echo "=========================================="
echo "Training completed!"
echo "=========================================="
