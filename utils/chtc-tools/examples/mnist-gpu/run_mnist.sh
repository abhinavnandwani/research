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

# Check Python and PyTorch
echo ""
echo "Python Version:"
python3 --version
echo ""

echo "PyTorch Version:"
python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device count: {torch.cuda.device_count()}'); print(f'CUDA device name: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" || {
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
