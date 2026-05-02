#!/bin/bash
# Container management for CHTC

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"
source "${CHTC_ROOT}/lib/ssh.sh"

load_config || exit 1

SUBCOMMAND="${1:-help}"
shift || true

case "${SUBCOMMAND}" in
    build)
        DEF_FILE="$1"

        if [[ -z "${DEF_FILE}" ]]; then
            log_error "Usage: chtc container build <definition-file.def>"
            exit 1
        fi

        if [[ ! -f "${DEF_FILE}" ]]; then
            log_error "Definition file not found: ${DEF_FILE}"
            exit 1
        fi

        DEF_FILE="$(cd "$(dirname "${DEF_FILE}")" && pwd)/$(basename "${DEF_FILE}")"
        CONTAINER_NAME="$(basename "${DEF_FILE}" .def).sif"

        log_info "Building container: ${CONTAINER_NAME}"
        log_warn "This will start an interactive build job on CHTC (4 hour limit)"

        # Upload definition file
        REMOTE_BUILD_DIR="${CHTC_HOME}/container_builds/$(date +%Y%m%d_%H%M%S)"
        ssh_exec "mkdir -p ${REMOTE_BUILD_DIR}"

        log_info "Uploading definition file..."
        ssh_upload "${DEF_FILE}" "${REMOTE_BUILD_DIR}/"

        # Create build submit file
        BUILD_SUB="${REMOTE_BUILD_DIR}/build.sub"

        log_info "Creating build job..."
        ssh_exec "cat > ${BUILD_SUB}" <<EOF
# Container build job
universe = vanilla
executable = /usr/bin/hostname

transfer_input_files = $(basename "${DEF_FILE}")
should_transfer_files = YES
when_to_transfer_output = ON_EXIT

request_cpus = 4
request_memory = 16GB
request_disk = 16GB

+IsBuildJob = true

queue 1
EOF

        # Submit interactive build job
        log_info "Starting interactive build job..."
        log_warn "You will be prompted for 2FA to start the interactive session"

        ssh_exec "cd ${REMOTE_BUILD_DIR} && condor_submit -i build.sub" <<COMMANDS || {
            log_error "Interactive session ended or failed"
            exit 1
        }
apptainer build ${CONTAINER_NAME} $(basename "${DEF_FILE}")
echo "Build complete! Testing container..."
apptainer shell -e ${CONTAINER_NAME} <<TEST
echo "Container test successful"
exit
TEST
echo "Moving to staging..."
mv ${CONTAINER_NAME} ${CHTC_STAGING}/
echo "Container available at: ${CHTC_STAGING}/${CONTAINER_NAME}"
exit
COMMANDS

        log_success "Container built and moved to staging"
        echo "Container path: ${CHTC_STAGING}/${CONTAINER_NAME}"
        echo ""
        echo "Use in submit file with:"
        echo "  container_image = osdf:///chtc/staging/${CHTC_USERNAME}/${CONTAINER_NAME}"
        echo "  requirements = (HasCHTCStaging == true)"
        ;;

    list)
        log_info "Containers in staging:"
        ssh_exec "ls -lh ${CHTC_STAGING}/*.sif 2>/dev/null || echo 'No containers found'"
        ;;

    upload)
        SIF_FILE="$1"

        if [[ -z "${SIF_FILE}" ]]; then
            log_error "Usage: chtc container upload <container.sif>"
            exit 1
        fi

        if [[ ! -f "${SIF_FILE}" ]]; then
            log_error "Container file not found: ${SIF_FILE}"
            exit 1
        fi

        CONTAINER_NAME="$(basename "${SIF_FILE}")"

        log_info "Uploading ${CONTAINER_NAME} to staging..."
        ssh_upload "${SIF_FILE}" "${CHTC_STAGING}/${CONTAINER_NAME}"

        log_success "Container uploaded"
        echo "Container path: ${CHTC_STAGING}/${CONTAINER_NAME}"
        ;;

    download)
        CONTAINER_NAME="$1"
        LOCAL_PATH="${2:-.}"

        if [[ -z "${CONTAINER_NAME}" ]]; then
            log_error "Usage: chtc container download <container-name> [local-path]"
            exit 1
        fi

        log_info "Downloading ${CONTAINER_NAME}..."
        ssh_download "${CHTC_STAGING}/${CONTAINER_NAME}" "${LOCAL_PATH}/${CONTAINER_NAME}"

        log_success "Container downloaded to ${LOCAL_PATH}/${CONTAINER_NAME}"
        ;;

    delete|rm)
        CONTAINER_NAME="$1"

        if [[ -z "${CONTAINER_NAME}" ]]; then
            log_error "Usage: chtc container delete <container-name>"
            exit 1
        fi

        if confirm "Delete ${CONTAINER_NAME} from staging?" "n"; then
            ssh_exec "rm -f ${CHTC_STAGING}/${CONTAINER_NAME}"
            log_success "Container deleted"
        else
            log_info "Cancelled"
        fi
        ;;

    help|*)
        cat <<EOF
Container Management

Usage: chtc container <command> [options]

Commands:
  build <def-file>              Build container from definition file
  list                          List containers in staging
  upload <sif-file>             Upload container to staging
  download <name> [local-path]  Download container from staging
  delete <name>                 Delete container from staging

Examples:
  # Build container from definition file
  chtc container build pytorch.def

  # List all containers
  chtc container list

  # Upload pre-built container
  chtc container upload my-container.sif

  # Download container
  chtc container download my-container.sif ./local/

  # Delete container
  chtc container delete old-container.sif
EOF
        ;;
esac
