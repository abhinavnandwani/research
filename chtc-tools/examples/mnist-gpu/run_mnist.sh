#!/bin/bash
# Wrapper script to run MNIST training in container

set -e

echo "=========================================="
echo "MNIST Training on CHTC GPU"
echo "=========================================="
echo "Hostname: $(hostname)"
echo "Date: $(date)"
echo "Job ID: ${CLUSTER:-local}.${PROCESS:-0}"
echo "=========================================="

# Check GPU
echo ""
echo "GPU Information:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
echo ""

# Check CUDA
echo "CUDA Version:"
nvcc --version || echo "nvcc not available (using runtime)"
echo ""

# Check Python and PyTorch
echo "Python Version:"
python3 --version
echo ""

echo "PyTorch Version:"
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')" || {
    echo "PyTorch not available, installing..."
    pip install --user torch torchvision wandb
}
echo ""

# Install WandB if not available
python3 -c "import wandb" 2>/dev/null || {
    echo "Installing WandB..."
    pip install --user wandb
    echo ""
}

# Run training
echo "=========================================="
echo "Starting Training..."
echo "=========================================="
echo ""

python3 train_mnist.py "$@"

EXIT_CODE=$?

echo ""
echo "=========================================="
echo "Training completed with exit code: ${EXIT_CODE}"
echo "Date: $(date)"
echo "=========================================="

exit ${EXIT_CODE}
