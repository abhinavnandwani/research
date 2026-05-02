#!/bin/bash
# Quick submission script for MNIST example

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "$(dirname "${SCRIPT_DIR}")")"

echo "=========================================="
echo "MNIST GPU Training - Quick Submit"
echo "=========================================="
echo ""

# Check if chtc command is available
if ! command -v "${CHTC_ROOT}/bin/chtc" &> /dev/null; then
    echo "Error: CHTC tools not found"
    echo "Expected at: ${CHTC_ROOT}/bin/chtc"
    exit 1
fi

# Create logs directory
mkdir -p "${SCRIPT_DIR}/logs"

echo "Files to upload:"
ls -lh "${SCRIPT_DIR}"/{train_mnist.py,run_mnist.sh,mnist.sub}
echo ""

echo "Container to use:"
ssh chtc "ls -lh /staging/nandwani2/scFoundation-container.sif"
echo ""

echo "Submitting job..."
echo ""

# Upload files to CHTC
echo "Uploading files to CHTC..."
ssh chtc "mkdir -p ~/mnist-example/logs"
scp "${SCRIPT_DIR}"/{train_mnist.py,run_mnist.sh,mnist.sub} chtc:~/mnist-example/

# Submit job
echo ""
echo "Submitting to HTCondor..."
JOB_OUTPUT=$(ssh chtc "cd ~/mnist-example && condor_submit mnist.sub")
echo "${JOB_OUTPUT}"

# Extract job ID
JOB_ID=$(echo "${JOB_OUTPUT}" | grep -oP 'submitted to cluster \K\d+' || echo "")

if [[ -n "${JOB_ID}" ]]; then
    echo ""
    echo "=========================================="
    echo "Job Submitted Successfully!"
    echo "=========================================="
    echo "Job ID: ${JOB_ID}"
    echo ""
    echo "Monitor with:"
    echo "  ${CHTC_ROOT}/bin/chtc monitor --watch"
    echo ""
    echo "Or:"
    echo "  ssh chtc \"condor_q\""
    echo ""
    echo "View logs:"
    echo "  ssh chtc \"tail -f ~/mnist-example/logs/mnist_${JOB_ID}_0.out\""
    echo ""
    echo "WandB Dashboard:"
    echo "  https://wandb.ai/ (project: chtc-mnist)"
    echo ""
    echo "Fetch results when done:"
    echo "  ${CHTC_ROOT}/bin/chtc logs ${JOB_ID}"
    echo "=========================================="
else
    echo ""
    echo "Error: Could not extract job ID"
    exit 1
fi
