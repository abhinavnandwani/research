#!/bin/bash
# Import existing CHTC projects to local workspace

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"
source "${CHTC_ROOT}/lib/ssh.sh"

load_config || exit 1

log_info "Importing existing CHTC projects..."
echo ""

# Ensure local workspace exists
mkdir -p "${CHTC_LOCAL_WORKSPACE}/projects"

# List directories on CHTC
log_info "Finding existing projects on CHTC..."
PROJECTS=$(ssh chtc "find ~/ -maxdepth 2 -type d \( -name 'chtc-scripts' -o -name 'scLLM' -o -name 'fault-models' -o -name 'nvbitfi' \) 2>/dev/null")

if [[ -z "${PROJECTS}" ]]; then
    log_warn "No existing projects found"
    exit 0
fi

echo -e "${CYAN}Found projects:${NC}"
echo "${PROJECTS}" | while read -r project; do
    BASENAME=$(basename "${project}")
    echo "  - ${BASENAME} (${project})"
done
echo ""

# Import each project
while IFS= read -r remote_project; do
    if [[ -z "${remote_project}" ]]; then
        continue
    fi

    PROJECT_NAME=$(basename "${remote_project}")
    LOCAL_PROJECT="${CHTC_LOCAL_WORKSPACE}/projects/${PROJECT_NAME}"

    if [[ -d "${LOCAL_PROJECT}" ]]; then
        log_warn "Project ${PROJECT_NAME} already exists locally, skipping..."
        continue
    fi

    log_info "Importing ${PROJECT_NAME}..."

    # Create project structure
    mkdir -p "${LOCAL_PROJECT}"/{code,jobs,results,docs}

    # Download the project
    ssh_download "${remote_project}/" "${LOCAL_PROJECT}/code/"

    # Look for submit files in parent directory
    PARENT_DIR=$(dirname "${remote_project}")
    SUBMIT_FILES=$(ssh chtc "find ${PARENT_DIR} -maxdepth 1 -name '*.sub' 2>/dev/null | grep -i ${PROJECT_NAME}" || true)

    if [[ -n "${SUBMIT_FILES}" ]]; then
        mkdir -p "${LOCAL_PROJECT}/jobs"
        while IFS= read -r submit_file; do
            if [[ -n "${submit_file}" ]]; then
                ssh_download "${submit_file}" "${LOCAL_PROJECT}/jobs/"
            fi
        done <<< "${SUBMIT_FILES}"
    fi

    # Create project metadata
    cat > "${LOCAL_PROJECT}/project.yaml" << EOF
name: ${PROJECT_NAME}
imported: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
source: ${remote_project}

wandb:
  enabled: false
  project: ${PROJECT_NAME}

remote:
  original_path: ${remote_project}
  sync_to: ${CHTC_HOME}/projects/${PROJECT_NAME}
EOF

    # Create README
    cat > "${LOCAL_PROJECT}/README.md" << EOF
# ${PROJECT_NAME}

Imported from CHTC: \`${remote_project}\`

## Structure

- \`code/\` - Imported source code
- \`jobs/\` - HTCondor submit files
- \`results/\` - Job outputs
- \`docs/\` - Documentation

## Sync

To sync changes back to CHTC:
\`\`\`bash
chtc project sync ${PROJECT_NAME}
\`\`\`

To pull results:
\`\`\`bash
chtc project pull ${PROJECT_NAME}
\`\`\`
EOF

    log_success "Imported ${PROJECT_NAME} to ${LOCAL_PROJECT}"

done <<< "${PROJECTS}"

echo ""
log_success "Import complete!"
echo ""
echo "Projects imported to: ${CHTC_LOCAL_WORKSPACE}/projects/"
echo ""
echo "Next steps:"
echo "  1. Review imported projects: ls ${CHTC_LOCAL_WORKSPACE}/projects/"
echo "  2. Enable WandB tracking: Edit project.yaml files"
echo "  3. Submit jobs: chtc submit jobs/your-job.sub --wandb"
