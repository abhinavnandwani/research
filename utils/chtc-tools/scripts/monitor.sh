#!/bin/bash
# Job monitoring script with real-time updates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"
source "${CHTC_ROOT}/lib/ssh.sh"

load_config || exit 1

# Parse arguments
WATCH_MODE=false
INTERVAL=10

while [[ $# -gt 0 ]]; do
    case "$1" in
        -w|--watch)
            WATCH_MODE=true
            shift
            ;;
        -i|--interval)
            INTERVAL="$2"
            shift 2
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Function to display job status
show_status() {
    clear
    echo -e "${CYAN}=== CHTC Job Monitor ===${NC}"
    echo "Time: $(timestamp)"
    echo ""

    # Get job queue
    QUEUE_OUTPUT=$(ssh_exec "condor_q -nobatch")

    if echo "${QUEUE_OUTPUT}" | grep -q "0 jobs; 0 completed, 0 removed, 0 idle, 0 running, 0 held"; then
        echo -e "${GREEN}No jobs in queue${NC}"
    else
        echo "${QUEUE_OUTPUT}"
    fi

    echo ""
    echo -e "${CYAN}=== Job Summary ===${NC}"

    # Parse job counts
    TOTAL=$(echo "${QUEUE_OUTPUT}" | grep -oP '\d+(?= jobs)' | head -1 || echo "0")
    COMPLETED=$(echo "${QUEUE_OUTPUT}" | grep -oP '\d+(?= completed)' || echo "0")
    IDLE=$(echo "${QUEUE_OUTPUT}" | grep -oP '\d+(?= idle)' || echo "0")
    RUNNING=$(echo "${QUEUE_OUTPUT}" | grep -oP '\d+(?= running)' || echo "0")
    HELD=$(echo "${QUEUE_OUTPUT}" | grep -oP '\d+(?= held)' || echo "0")

    echo "Total: ${TOTAL} | Running: ${RUNNING} | Idle: ${IDLE} | Held: ${HELD}"

    # Check for WandB tracked jobs
    MAPPING_FILE="${HOME}/.chtc/wandb_mappings.txt"
    if [[ -f "${MAPPING_FILE}" ]]; then
        ACTIVE_JOBS=$(echo "${QUEUE_OUTPUT}" | grep -oP '^\s*\K\d+\.\d+' || true)

        if [[ -n "${ACTIVE_JOBS}" ]]; then
            echo ""
            echo -e "${CYAN}=== WandB Tracked Jobs ===${NC}"

            while IFS=: read -r job_id run_id project timestamp; do
                # Check if job is still active
                JOB_CLUSTER=$(echo "${job_id}" | cut -d. -f1)

                if echo "${ACTIVE_JOBS}" | grep -q "^${JOB_CLUSTER}"; then
                    echo "Job ${job_id}: https://wandb.ai/${WANDB_ENTITY}/${project}/runs/${run_id}"
                fi
            done < "${MAPPING_FILE}"
        fi
    fi

    if [[ "${WATCH_MODE}" == true ]]; then
        echo ""
        echo -e "${YELLOW}Watching (refresh every ${INTERVAL}s, Ctrl+C to exit)${NC}"
    fi
}

if [[ "${WATCH_MODE}" == true ]]; then
    # Watch mode - continuous updates
    while true; do
        show_status
        sleep "${INTERVAL}"
    done
else
    # Single shot
    show_status
fi
