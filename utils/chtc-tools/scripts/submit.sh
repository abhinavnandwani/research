#!/bin/bash
# Job submission script with WandB integration

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"
source "${CHTC_ROOT}/lib/ssh.sh"

load_config || exit 1

# Parse arguments
SUBMIT_FILE=""
USE_WANDB=false
WANDB_PROJECT="${WANDB_PROJECT:-chtc-jobs}"
USE_GPU=false
CPUS="${DEFAULT_CPUS}"
MEMORY="${DEFAULT_MEMORY}"
DISK="${DEFAULT_DISK}"
GPUS="1"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --wandb)
            USE_WANDB=true
            shift
            ;;
        --project)
            WANDB_PROJECT="$2"
            shift 2
            ;;
        --gpu)
            USE_GPU=true
            shift
            ;;
        --gpus)
            GPUS="$2"
            shift 2
            ;;
        --cpus)
            CPUS="$2"
            shift 2
            ;;
        --memory)
            MEMORY="$2"
            shift 2
            ;;
        --disk)
            DISK="$2"
            shift 2
            ;;
        -*)
            log_error "Unknown option: $1"
            exit 1
            ;;
        *)
            if [[ -z "${SUBMIT_FILE}" ]]; then
                SUBMIT_FILE="$1"
            else
                log_error "Multiple submit files specified"
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "${SUBMIT_FILE}" ]]; then
    log_error "No submit file specified"
    echo "Usage: chtc submit <submit_file> [options]"
    exit 1
fi

if [[ ! -f "${SUBMIT_FILE}" ]]; then
    log_error "Submit file not found: ${SUBMIT_FILE}"
    exit 1
fi

# Get absolute path
SUBMIT_FILE="$(cd "$(dirname "${SUBMIT_FILE}")" && pwd)/$(basename "${SUBMIT_FILE}")"
SUBMIT_DIR="$(dirname "${SUBMIT_FILE}")"
SUBMIT_BASENAME="$(basename "${SUBMIT_FILE}")"

log_info "Submitting job: ${SUBMIT_BASENAME}"

# Upload submit file and related files to CHTC
log_info "Uploading files to CHTC..."

# Create temporary directory on CHTC
REMOTE_JOB_DIR="${CHTC_HOME}/jobs/$(basename "${SUBMIT_FILE}" .sub)_$(date +%Y%m%d_%H%M%S)"
ssh_exec "mkdir -p ${REMOTE_JOB_DIR}"

# Upload submit directory
ssh_upload "${SUBMIT_DIR}/" "${REMOTE_JOB_DIR}/"

# If using WandB, upload wrapper and initialize run
WANDB_RUN_ID=""
if [[ "${USE_WANDB}" == true ]]; then
    log_info "Initializing WandB tracking..."

    # Upload WandB wrapper
    ssh_upload "${CHTC_ROOT}/templates/wandb_wrapper.sh" "${REMOTE_JOB_DIR}/"
    ssh_exec "chmod +x ${REMOTE_JOB_DIR}/wandb_wrapper.sh"

    # Create WandB run and get run ID (using Python script)
    WANDB_RUN_ID=$(python3 "${CHTC_ROOT}/scripts/wandb_logger.py" \
        --api-key "${WANDB_API_KEY}" \
        --entity "${WANDB_ENTITY}" \
        submit \
        --project "${WANDB_PROJECT}" \
        --submit-file "${SUBMIT_FILE}" \
        --job-id "pending")

    log_success "WandB run initialized: ${WANDB_RUN_ID}"

    # Modify submit file to use WandB wrapper
    # This is a simple approach - for production, you'd want proper submit file parsing
    log_debug "Run ID: ${WANDB_RUN_ID}"
fi

# Submit the job
log_info "Submitting to HTCondor..."

JOB_OUTPUT=$(ssh_exec "cd ${REMOTE_JOB_DIR} && condor_submit ${SUBMIT_BASENAME}")
log_debug "Condor output: ${JOB_OUTPUT}"

# Extract job ID from output
JOB_ID=$(echo "${JOB_OUTPUT}" | grep -oP 'submitted to cluster \K\d+' || echo "")

if [[ -z "${JOB_ID}" ]]; then
    log_error "Failed to extract job ID from condor_submit output"
    echo "${JOB_OUTPUT}"
    exit 1
fi

log_success "Job submitted successfully!"
echo ""
echo "  Job ID: ${JOB_ID}"
echo "  Remote dir: ${REMOTE_JOB_DIR}"

if [[ "${USE_WANDB}" == true ]]; then
    echo "  WandB Run: ${WANDB_RUN_ID}"
    echo "  WandB URL: https://wandb.ai/${WANDB_ENTITY}/${WANDB_PROJECT}/runs/${WANDB_RUN_ID}"

    # Store job-to-run mapping
    MAPPING_FILE="${HOME}/.chtc/wandb_mappings.txt"
    mkdir -p "$(dirname "${MAPPING_FILE}")"
    echo "${JOB_ID}:${WANDB_RUN_ID}:${WANDB_PROJECT}:$(timestamp)" >> "${MAPPING_FILE}"
fi

echo ""
echo "Monitor with: chtc monitor"
echo "Check queue: chtc queue"
echo "Fetch logs: chtc logs ${JOB_ID}"
