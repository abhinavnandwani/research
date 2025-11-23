#!/bin/bash
# Fetch job logs from CHTC

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"
source "${CHTC_ROOT}/lib/ssh.sh"

load_config || exit 1

JOB_ID="$1"

if [[ -z "${JOB_ID}" ]]; then
    log_error "Usage: chtc logs <job-id>"
    exit 1
fi

log_info "Fetching logs for job ${JOB_ID}..."

# Find the job directory
JOB_DIRS=$(ssh_exec "find ${CHTC_HOME}/jobs -type d -name '*' 2>/dev/null | head -20")

if [[ -z "${JOB_DIRS}" ]]; then
    log_error "No job directories found"
    exit 1
fi

# Search for log files matching job ID
LOG_FILES=$(ssh_exec "find ${CHTC_HOME}/jobs -name '*_${JOB_ID}_*.log' -o -name '*_${JOB_ID}_*.err' -o -name '*_${JOB_ID}_*.out' 2>/dev/null")

if [[ -z "${LOG_FILES}" ]]; then
    log_warn "No log files found for job ${JOB_ID}"
    echo "This might mean:"
    echo "  1. Job hasn't completed yet"
    echo "  2. Job ID is incorrect"
    echo "  3. Logs were already downloaded"
    exit 1
fi

# Create local logs directory
LOCAL_LOGS_DIR="${CHTC_LOCAL_WORKSPACE}/logs/${JOB_ID}"
mkdir -p "${LOCAL_LOGS_DIR}"

log_info "Downloading logs to ${LOCAL_LOGS_DIR}..."

# Download each log file
while IFS= read -r log_file; do
    if [[ -n "${log_file}" ]]; then
        BASENAME=$(basename "${log_file}")
        ssh_download "${log_file}" "${LOCAL_LOGS_DIR}/${BASENAME}"
    fi
done <<< "${LOG_FILES}"

log_success "Logs downloaded successfully"

# Display log summary
echo ""
echo -e "${CYAN}=== Log Files ===${NC}"
ls -lh "${LOCAL_LOGS_DIR}"

# Check if there's a WandB mapping for this job
MAPPING_FILE="${HOME}/.chtc/wandb_mappings.txt"
if [[ -f "${MAPPING_FILE}" ]]; then
    MAPPING=$(grep "^${JOB_ID}:" "${MAPPING_FILE}" || true)

    if [[ -n "${MAPPING}" ]]; then
        RUN_ID=$(echo "${MAPPING}" | cut -d: -f2)
        PROJECT=$(echo "${MAPPING}" | cut -d: -f3)

        log_info "Updating WandB run with logs..."

        # Parse .log file for resource usage and update WandB
        LOG_FILE=$(find "${LOCAL_LOGS_DIR}" -name "*.log" | head -1)

        if [[ -n "${LOG_FILE}" ]]; then
            python3 "${CHTC_ROOT}/scripts/wandb_logger.py" \
                --api-key "${WANDB_API_KEY}" \
                --entity "${WANDB_ENTITY}" \
                complete \
                --run-id "${RUN_ID}" \
                --log-file "${LOG_FILE}" \
                --output-files "${LOCAL_LOGS_DIR}"/*.out

            log_success "WandB run updated"
            echo "View at: https://wandb.ai/${WANDB_ENTITY}/${PROJECT}/runs/${RUN_ID}"
        fi
    fi
fi

# Offer to display logs
echo ""
if confirm "Display log file?" "y"; then
    LOG_FILE=$(find "${LOCAL_LOGS_DIR}" -name "*.log" | head -1)
    if [[ -n "${LOG_FILE}" ]]; then
        echo ""
        echo -e "${CYAN}=== Log Content ===${NC}"
        cat "${LOG_FILE}"
    fi
fi
