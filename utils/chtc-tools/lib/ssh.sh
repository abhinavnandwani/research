#!/bin/bash
# SSH connection management with ControlMaster for persistent connections

# Source utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/utils.sh
source "${SCRIPT_DIR}/utils.sh"

# Initialize SSH ControlMaster connection
ssh_connect() {
    local control_socket
    control_socket=$(get_control_socket)

    # Check if already connected
    if is_connected; then
        log_debug "SSH connection already active"
        return 0
    fi

    log_info "Establishing SSH connection to ${CHTC_HOST}..."
    log_warn "You will be prompted for your password and Duo 2FA"

    # Establish ControlMaster connection
    ssh -fNT \
        -o ControlMaster=yes \
        -o ControlPath="${control_socket}" \
        -o ControlPersist="${SSH_CONTROL_PERSIST:-4h}" \
        -o ServerAliveInterval="${SSH_KEEPALIVE:-60}" \
        -o ServerAliveCountMax=3 \
        -p "${CHTC_PORT}" \
        "${CHTC_USERNAME}@${CHTC_HOST}"

    local exit_code=$?

    if [[ ${exit_code} -eq 0 ]]; then
        log_success "SSH connection established (will persist for ${SSH_CONTROL_PERSIST:-4h})"
        log_info "All future commands will reuse this connection (no more 2FA prompts)"
        return 0
    else
        log_error "Failed to establish SSH connection"
        return ${exit_code}
    fi
}

# Close SSH ControlMaster connection
ssh_disconnect() {
    local control_socket
    control_socket=$(get_control_socket)

    if ! is_connected; then
        log_warn "No active SSH connection"
        return 0
    fi

    log_info "Closing SSH connection..."
    ssh -O exit -S "${control_socket}" "${CHTC_USERNAME}@${CHTC_HOST}" 2>/dev/null

    log_success "SSH connection closed"
    return 0
}

# Execute command on CHTC via SSH
ssh_exec() {
    local control_socket
    control_socket=$(get_control_socket)

    # Auto-connect if not connected
    if ! is_connected; then
        log_debug "No active connection, establishing one..."
        ssh_connect || return $?
    fi

    log_debug "Executing: $*"

    ssh -S "${control_socket}" \
        -o ControlMaster=no \
        -p "${CHTC_PORT}" \
        "${CHTC_USERNAME}@${CHTC_HOST}" \
        "$@"

    return $?
}

# Upload file/directory to CHTC
ssh_upload() {
    local local_path="$1"
    local remote_path="$2"
    local control_socket
    control_socket=$(get_control_socket)

    if [[ -z "${local_path}" ]] || [[ -z "${remote_path}" ]]; then
        log_error "Usage: ssh_upload <local_path> <remote_path>"
        return 1
    fi

    if [[ ! -e "${local_path}" ]]; then
        log_error "Local path does not exist: ${local_path}"
        return 1
    fi

    # Auto-connect if not connected
    if ! is_connected; then
        ssh_connect || return $?
    fi

    log_info "Uploading ${local_path} to ${remote_path}..."

    rsync -avz --progress \
        -e "ssh -S ${control_socket} -p ${CHTC_PORT}" \
        "${local_path}" \
        "${CHTC_USERNAME}@${CHTC_HOST}:${remote_path}"

    local exit_code=$?

    if [[ ${exit_code} -eq 0 ]]; then
        log_success "Upload complete"
    else
        log_error "Upload failed"
    fi

    return ${exit_code}
}

# Download file/directory from CHTC
ssh_download() {
    local remote_path="$1"
    local local_path="$2"
    local control_socket
    control_socket=$(get_control_socket)

    if [[ -z "${remote_path}" ]] || [[ -z "${local_path}" ]]; then
        log_error "Usage: ssh_download <remote_path> <local_path>"
        return 1
    fi

    # Auto-connect if not connected
    if ! is_connected; then
        ssh_connect || return $?
    fi

    log_info "Downloading ${remote_path} to ${local_path}..."

    rsync -avz --progress \
        -e "ssh -S ${control_socket} -p ${CHTC_PORT}" \
        "${CHTC_USERNAME}@${CHTC_HOST}:${remote_path}" \
        "${local_path}"

    local exit_code=$?

    if [[ ${exit_code} -eq 0 ]]; then
        log_success "Download complete"
    else
        log_error "Download failed"
    fi

    return ${exit_code}
}

# Interactive SSH session
ssh_login() {
    local control_socket
    control_socket=$(get_control_socket)

    # Auto-connect if not connected
    if ! is_connected; then
        ssh_connect || return $?
    fi

    log_info "Starting interactive session..."

    ssh -S "${control_socket}" \
        -o ControlMaster=no \
        -p "${CHTC_PORT}" \
        -t \
        "${CHTC_USERNAME}@${CHTC_HOST}"

    return $?
}

# Get SSH connection status
ssh_status() {
    if is_connected; then
        log_success "Connected to ${CHTC_HOST}"

        # Get connection details
        local control_socket
        control_socket=$(get_control_socket)

        if [[ -S "${control_socket}" ]]; then
            local file_age
            file_age=$(( $(date +%s) - $(stat -f %m "${control_socket}" 2>/dev/null || stat -c %Y "${control_socket}") ))
            local hours=$((file_age / 3600))
            local minutes=$(( (file_age % 3600) / 60 ))

            echo "  Connection age: ${hours}h ${minutes}m"
            echo "  Control socket: ${control_socket}"
        fi
    else
        log_warn "Not connected to ${CHTC_HOST}"
        return 1
    fi
}
