#!/bin/bash
# WandB wrapper script for CHTC jobs
# This script runs inside the CHTC job to log metrics to WandB

set -e

# Configuration from environment variables
WANDB_API_KEY="${WANDB_API_KEY:-}"
WANDB_PROJECT="${WANDB_PROJECT:-chtc-jobs}"
WANDB_RUN_ID="${WANDB_RUN_ID:-}"
WANDB_RUN_NAME="${WANDB_RUN_NAME:-}"
WANDB_ENTITY="${WANDB_ENTITY:-}"

# Job configuration
JOB_SCRIPT="$1"
shift  # Remaining args passed to script

if [[ -z "${JOB_SCRIPT}" ]]; then
    echo "Error: No job script specified" >&2
    exit 1
fi

if [[ ! -f "${JOB_SCRIPT}" ]]; then
    echo "Error: Job script not found: ${JOB_SCRIPT}" >&2
    exit 1
fi

# Install wandb if not available
if ! command -v wandb &> /dev/null; then
    echo "Installing wandb..."
    pip install --user wandb &>/dev/null || {
        echo "Warning: Could not install wandb, continuing without it"
        # Run job without wandb
        bash "${JOB_SCRIPT}" "$@"
        exit $?
    }
fi

# Initialize WandB run
if [[ -n "${WANDB_API_KEY}" ]]; then
    export WANDB_API_KEY

    # Resume or create run
    if [[ -n "${WANDB_RUN_ID}" ]]; then
        wandb online
        export WANDB_RESUME="must"
        export WANDB_RUN_ID
    fi

    echo "WandB initialized for project: ${WANDB_PROJECT}"
else
    echo "Warning: WANDB_API_KEY not set, running without WandB tracking"
fi

# Record start time
START_TIME=$(date +%s)

# Run the actual job script and capture exit code
set +e
bash "${JOB_SCRIPT}" "$@"
EXIT_CODE=$?
set -e

# Record end time
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Log completion metrics if wandb is available and configured
if command -v wandb &> /dev/null && [[ -n "${WANDB_API_KEY}" ]]; then
    python3 - <<EOF
import wandb
import os

run = wandb.init(
    project="${WANDB_PROJECT}",
    entity="${WANDB_ENTITY}" if "${WANDB_ENTITY}" else None,
    id="${WANDB_RUN_ID}" if "${WANDB_RUN_ID}" else None,
    resume="must" if "${WANDB_RUN_ID}" else None,
)

run.log({
    "exit_code": ${EXIT_CODE},
    "duration_seconds": ${DURATION},
    "success": ${EXIT_CODE} == 0,
})

# Get HTCondor job info if available
htcondor_job_id = os.environ.get('_CONDOR_JOB_AD')
if htcondor_job_id:
    run.config.update({"htcondor_job_ad": htcondor_job_id})

run.finish()
EOF
fi

echo "Job completed in ${DURATION} seconds with exit code ${EXIT_CODE}"
exit ${EXIT_CODE}
