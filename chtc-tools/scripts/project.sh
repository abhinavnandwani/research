#!/bin/bash
# Project management for CHTC

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"
source "${CHTC_ROOT}/lib/ssh.sh"

load_config || exit 1

PROJECTS_DIR="${CHTC_LOCAL_WORKSPACE}/projects"
mkdir -p "${PROJECTS_DIR}"

SUBCOMMAND="${1:-help}"
shift || true

case "${SUBCOMMAND}" in
    init)
        PROJECT_NAME="$1"

        if [[ -z "${PROJECT_NAME}" ]]; then
            log_error "Usage: chtc project init <project-name>"
            exit 1
        fi

        PROJECT_DIR="${PROJECTS_DIR}/${PROJECT_NAME}"

        if [[ -d "${PROJECT_DIR}" ]]; then
            log_error "Project already exists: ${PROJECT_NAME}"
            exit 1
        fi

        log_info "Initializing project: ${PROJECT_NAME}"

        mkdir -p "${PROJECT_DIR}"/{code,data,containers,jobs,results}

        # Create project config
        cat > "${PROJECT_DIR}/project.yaml" <<EOF
name: ${PROJECT_NAME}
created: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
description: ""

wandb:
  enabled: true
  project: ${PROJECT_NAME}

resources:
  default_cpus: ${DEFAULT_CPUS}
  default_memory: ${DEFAULT_MEMORY}
  default_disk: ${DEFAULT_DISK}

remote:
  sync_to: ${CHTC_HOME}/projects/${PROJECT_NAME}
  staging: ${CHTC_STAGING}/${PROJECT_NAME}
EOF

        # Create README
        cat > "${PROJECT_DIR}/README.md" <<EOF
# ${PROJECT_NAME}

CHTC Project

## Structure

- \`code/\` - Source code and scripts
- \`data/\` - Input data (small files < 1GB)
- \`containers/\` - Apptainer definition files
- \`jobs/\` - HTCondor submit files
- \`results/\` - Output data and logs

## Quick Start

\`\`\`bash
# Sync project to CHTC
chtc project sync ${PROJECT_NAME}

# Submit a job
chtc submit jobs/my_job.sub --wandb

# Monitor jobs
chtc monitor

# Fetch results
chtc project pull ${PROJECT_NAME}
\`\`\`
EOF

        # Create example submit file
        cat > "${PROJECT_DIR}/jobs/example.sub" <<EOF
# Example HTCondor submit file
# Edit this for your job

executable = ../code/run.sh
arguments = \$(Process)

transfer_input_files = ../code/

log = ../results/job_\$(Cluster)_\$(Process).log
error = ../results/job_\$(Cluster)_\$(Process).err
output = ../results/job_\$(Cluster)_\$(Process).out

request_cpus = ${DEFAULT_CPUS}
request_memory = ${DEFAULT_MEMORY}
request_disk = ${DEFAULT_DISK}

queue 1
EOF

        # Create example script
        cat > "${PROJECT_DIR}/code/run.sh" <<'EOF'
#!/bin/bash
# Example job script

echo "Starting job at $(date)"
echo "Running on $(hostname)"
echo "Process ID: $1"

# Your code here
echo "Hello from CHTC!"

echo "Job completed at $(date)"
EOF

        chmod +x "${PROJECT_DIR}/code/run.sh"

        log_success "Project initialized: ${PROJECT_DIR}"
        echo ""
        echo "Next steps:"
        echo "  1. Add your code to ${PROJECT_DIR}/code/"
        echo "  2. Edit ${PROJECT_DIR}/jobs/example.sub for your job"
        echo "  3. Sync to CHTC: chtc project sync ${PROJECT_NAME}"
        echo "  4. Submit job: chtc submit ${PROJECT_DIR}/jobs/example.sub --wandb"
        ;;

    list|ls)
        log_info "Local projects:"
        echo ""

        if [[ ! -d "${PROJECTS_DIR}" ]] || [[ -z "$(ls -A "${PROJECTS_DIR}" 2>/dev/null)" ]]; then
            echo "No projects found"
        else
            for project_dir in "${PROJECTS_DIR}"/*; do
                if [[ -d "${project_dir}" ]]; then
                    project_name="$(basename "${project_dir}")"
                    if [[ -f "${project_dir}/project.yaml" ]]; then
                        created=$(grep "created:" "${project_dir}/project.yaml" | cut -d' ' -f2-)
                        echo "  ${project_name} (created: ${created})"
                    else
                        echo "  ${project_name}"
                    fi
                fi
            done
        fi
        ;;

    sync|push)
        PROJECT_NAME="$1"

        if [[ -z "${PROJECT_NAME}" ]]; then
            log_error "Usage: chtc project sync <project-name>"
            exit 1
        fi

        PROJECT_DIR="${PROJECTS_DIR}/${PROJECT_NAME}"

        if [[ ! -d "${PROJECT_DIR}" ]]; then
            log_error "Project not found: ${PROJECT_NAME}"
            exit 1
        fi

        REMOTE_DIR="${CHTC_HOME}/projects/${PROJECT_NAME}"

        log_info "Syncing ${PROJECT_NAME} to CHTC..."

        # Create remote directory
        ssh_exec "mkdir -p ${REMOTE_DIR}"

        # Sync project files
        ssh_upload "${PROJECT_DIR}/" "${REMOTE_DIR}/"

        log_success "Project synced to ${REMOTE_DIR}"
        ;;

    pull)
        PROJECT_NAME="$1"

        if [[ -z "${PROJECT_NAME}" ]]; then
            log_error "Usage: chtc project pull <project-name>"
            exit 1
        fi

        PROJECT_DIR="${PROJECTS_DIR}/${PROJECT_NAME}"
        REMOTE_DIR="${CHTC_HOME}/projects/${PROJECT_NAME}"

        log_info "Pulling ${PROJECT_NAME} from CHTC..."

        # Download results and logs
        mkdir -p "${PROJECT_DIR}/results"
        ssh_download "${REMOTE_DIR}/results/" "${PROJECT_DIR}/results/" || {
            log_warn "No results directory found"
        }

        log_success "Project pulled to ${PROJECT_DIR}"
        ;;

    delete|rm)
        PROJECT_NAME="$1"

        if [[ -z "${PROJECT_NAME}" ]]; then
            log_error "Usage: chtc project delete <project-name>"
            exit 1
        fi

        PROJECT_DIR="${PROJECTS_DIR}/${PROJECT_NAME}"

        if [[ ! -d "${PROJECT_DIR}" ]]; then
            log_error "Project not found: ${PROJECT_NAME}"
            exit 1
        fi

        if confirm "Delete local project ${PROJECT_NAME}?" "n"; then
            rm -rf "${PROJECT_DIR}"
            log_success "Project deleted"
        else
            log_info "Cancelled"
        fi
        ;;

    help|*)
        cat <<EOF
Project Management

Usage: chtc project <command> [options]

Commands:
  init <name>        Initialize new project
  list, ls           List all projects
  sync <name>        Sync project to CHTC
  pull <name>        Pull results from CHTC
  delete <name>      Delete local project

Project Structure:
  code/              Source code and scripts
  data/              Input data
  containers/        Container definition files
  jobs/              HTCondor submit files
  results/           Output data and logs

Examples:
  # Create new project
  chtc project init my-research

  # Sync to CHTC
  chtc project sync my-research

  # Pull results back
  chtc project pull my-research
EOF
        ;;
esac
