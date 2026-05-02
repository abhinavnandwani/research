#!/bin/bash
# WandB Management for CHTC
# Real-time monitoring and management of WandB runs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"

show_help() {
    cat << EOF
WandB Management for CHTC

Usage:
    chtc wandb <command> [options]

Commands:
    monitor, mon, m      Monitor WandB runs in real-time
    list, ls, l          List all runs in a project
    url                  Get URL for a project or run
    help, -h, --help     Show this help

Monitor Options:
    --project, -p <name>    Project name (required)
    --entity, -e <name>     WandB entity/username (optional)
    --run-name, -n <name>   Filter by run name
    --run-id <id>           Filter by run ID
    --interval, -i <sec>    Update interval (default: 3)

Examples:
    # Monitor all runs in chtc-mnist project
    chtc wandb monitor --project chtc-mnist

    # Monitor specific job
    chtc wandb monitor -p chtc-mnist -n mnist-job-4628778

    # List all runs
    chtc wandb list --project chtc-mnist

    # Get project URL
    chtc wandb url chtc-mnist

    # Monitor with faster updates (2 second interval)
    chtc wandb monitor -p chtc-mnist -i 2
EOF
}

monitor_runs() {
    local project=""
    local entity=""
    local run_name=""
    local run_id=""
    local interval=3

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --project|-p)
                project="$2"
                shift 2
                ;;
            --entity|-e)
                entity="$2"
                shift 2
                ;;
            --run-name|-n)
                run_name="$2"
                shift 2
                ;;
            --run-id)
                run_id="$2"
                shift 2
                ;;
            --interval|-i)
                interval="$2"
                shift 2
                ;;
            *)
                if [[ -z "$project" ]]; then
                    project="$1"
                fi
                shift
                ;;
        esac
    done

    if [[ -z "$project" ]]; then
        log_error "Project name required"
        echo ""
        echo "Usage: chtc wandb monitor --project <name>"
        exit 1
    fi

    log_info "Starting WandB monitor for project: $project"

    # Build command
    local cmd=("python3" "${CHTC_ROOT}/scripts/monitor_wandb.py" "--project" "$project" "--interval" "$interval")

    if [[ -n "$entity" ]]; then
        cmd+=("--entity" "$entity")
    fi

    if [[ -n "$run_name" ]]; then
        cmd+=("--run-name" "$run_name")
    fi

    if [[ -n "$run_id" ]]; then
        cmd+=("--run-id" "$run_id")
    fi

    # Execute monitor
    exec "${cmd[@]}"
}

list_runs() {
    local project=""
    local entity=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --project|-p)
                project="$2"
                shift 2
                ;;
            --entity|-e)
                entity="$2"
                shift 2
                ;;
            *)
                if [[ -z "$project" ]]; then
                    project="$1"
                fi
                shift
                ;;
        esac
    done

    if [[ -z "$project" ]]; then
        log_error "Project name required"
        echo ""
        echo "Usage: chtc wandb list --project <name>"
        exit 1
    fi

    # Build command
    local cmd=("python3" "${CHTC_ROOT}/scripts/monitor_wandb.py" "--project" "$project" "--list")

    if [[ -n "$entity" ]]; then
        cmd+=("--entity" "$entity")
    fi

    # Execute
    exec "${cmd[@]}"
}

get_url() {
    local project="$1"
    local entity="${2:-}"

    if [[ -z "$project" ]]; then
        log_error "Project name required"
        echo ""
        echo "Usage: chtc wandb url <project> [entity]"
        exit 1
    fi

    if [[ -n "$entity" ]]; then
        echo "https://wandb.ai/${entity}/${project}"
    else
        echo "https://wandb.ai/home"
        log_info "Without entity, navigate to your project from home"
        log_info "Or provide entity: chtc wandb url $project <your-username>"
    fi
}

# Main command dispatcher
COMMAND="${1:-help}"
shift || true

case "${COMMAND}" in
    monitor|mon|m)
        monitor_runs "$@"
        ;;
    list|ls|l)
        list_runs "$@"
        ;;
    url)
        get_url "$@"
        ;;
    help|-h|--help)
        show_help
        ;;
    *)
        log_error "Unknown command: ${COMMAND}"
        echo ""
        show_help
        exit 1
        ;;
esac
