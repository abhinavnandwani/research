#!/bin/bash
# Utility functions for CHTC CLI

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_debug() {
    if [[ "${CHTC_DEBUG}" == "1" ]]; then
        echo -e "${MAGENTA}[DEBUG]${NC} $1"
    fi
}

# Load configuration
load_config() {
    local config_file="${HOME}/.chtcrc"

    if [[ ! -f "${config_file}" ]]; then
        log_error "Configuration file not found: ${config_file}"
        log_info "Copy .chtcrc.example to ~/.chtcrc and configure it"
        return 1
    fi

    # shellcheck source=/dev/null
    source "${config_file}"

    # Validate required variables
    if [[ -z "${CHTC_USERNAME}" ]] || [[ -z "${CHTC_HOST}" ]]; then
        log_error "CHTC_USERNAME and CHTC_HOST must be set in ~/.chtcrc"
        return 1
    fi

    log_debug "Configuration loaded successfully"
    return 0
}

# Get SSH control socket path
get_control_socket() {
    local control_dir="${HOME}/.chtc/ssh_control"
    mkdir -p "${control_dir}"
    chmod 700 "${control_dir}"
    echo "${control_dir}/${CHTC_USERNAME}@${CHTC_HOST}:${CHTC_PORT}"
}

# Check if SSH connection is active
is_connected() {
    local control_socket
    control_socket=$(get_control_socket)

    if [[ -S "${control_socket}" ]]; then
        ssh -O check -S "${control_socket}" "${CHTC_USERNAME}@${CHTC_HOST}" 2>/dev/null
        return $?
    fi
    return 1
}

# Pretty print table
print_table() {
    column -t -s $'\t'
}

# Get current timestamp
timestamp() {
    date +"%Y-%m-%d %H:%M:%S"
}

# Human readable file sizes
human_size() {
    local bytes=$1
    if [[ ${bytes} -lt 1024 ]]; then
        echo "${bytes}B"
    elif [[ ${bytes} -lt 1048576 ]]; then
        echo "$(( bytes / 1024 ))KB"
    elif [[ ${bytes} -lt 1073741824 ]]; then
        echo "$(( bytes / 1048576 ))MB"
    else
        echo "$(( bytes / 1073741824 ))GB"
    fi
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Confirm action
confirm() {
    local prompt="$1"
    local default="${2:-n}"

    if [[ "${default}" == "y" ]]; then
        prompt="${prompt} [Y/n] "
    else
        prompt="${prompt} [y/N] "
    fi

    read -r -p "${prompt}" response
    response=${response:-${default}}

    case "${response}" in
        [yY][eE][sS]|[yY])
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}
