#!/bin/bash
# Discover and catalog CHTC environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHTC_ROOT="$(dirname "${SCRIPT_DIR}")"

source "${CHTC_ROOT}/lib/utils.sh"

load_config || exit 1

log_info "Discovering CHTC environment for ${CHTC_USERNAME}@${CHTC_HOST}..."
echo ""

# Create inventory directory
INVENTORY_DIR="${HOME}/.chtc/inventory"
mkdir -p "${INVENTORY_DIR}"

INVENTORY_FILE="${INVENTORY_DIR}/environment.yaml"

log_info "Scanning home directory..."
HOME_SIZE=$(ssh chtc "du -sh ~/ 2>/dev/null | cut -f1")
HOME_FILES=$(ssh chtc "find ~/ -maxdepth 1 -type f -name '*.sub' 2>/dev/null | wc -l")

log_info "Scanning staging directory..."
STAGING_SIZE=$(ssh chtc "du -sh /staging/${CHTC_USERNAME} 2>/dev/null | cut -f1" || echo "0")
STAGING_CONTAINERS=$(ssh chtc "find /staging/${CHTC_USERNAME} -name '*.sif' 2>/dev/null | wc -l" || echo "0")

log_info "Checking quota..."
QUOTA_INFO=$(ssh chtc "quota -s 2>/dev/null | tail -1" || echo "N/A")

log_info "Scanning for containers..."
CONTAINERS=$(ssh chtc "find ~/ /staging/${CHTC_USERNAME} -name '*.sif' 2>/dev/null | sort")

log_info "Scanning for existing projects..."
PROJECTS=$(ssh chtc "find ~/ -maxdepth 2 -type d -name 'chtc-scripts' -o -name 'scLLM' -o -name 'fault-models' 2>/dev/null | sort")

log_info "Checking software..."
PYTHON_VERSION=$(ssh chtc "python3 --version 2>&1 | cut -d' ' -f2")
CONDOR_VERSION=$(ssh chtc "condor_version 2>&1 | head -1 | grep -oP 'CondorVersion: \K[0-9.]+'" || echo "unknown")

# Generate inventory
cat > "${INVENTORY_FILE}" << EOF
# CHTC Environment Inventory
# Generated: $(date)

user: ${CHTC_USERNAME}
host: ${CHTC_HOST}

storage:
  home:
    path: /home/${CHTC_USERNAME}
    size: ${HOME_SIZE}
    quota: $(echo "${QUOTA_INFO}" | awk '{print $3}')
    used: $(echo "${QUOTA_INFO}" | awk '{print $2}')
  staging:
    path: /staging/${CHTC_USERNAME}
    size: ${STAGING_SIZE}

software:
  python: ${PYTHON_VERSION}
  condor: ${CONDOR_VERSION}

files:
  submit_files: ${HOME_FILES}
  containers: ${STAGING_CONTAINERS}

containers:
EOF

# Add container list
while IFS= read -r container; do
    if [[ -n "${container}" ]]; then
        SIZE=$(ssh chtc "ls -lh '${container}' 2>/dev/null | awk '{print \$5}'")
        echo "  - path: ${container}" >> "${INVENTORY_FILE}"
        echo "    size: ${SIZE}" >> "${INVENTORY_FILE}"
    fi
done <<< "${CONTAINERS}"

cat >> "${INVENTORY_FILE}" << EOF

existing_projects:
EOF

# Add project list
while IFS= read -r project; do
    if [[ -n "${project}" ]]; then
        echo "  - ${project}" >> "${INVENTORY_FILE}"
    fi
done <<< "${PROJECTS}"

log_success "Environment discovery complete!"
echo ""

# Display summary
echo -e "${CYAN}=== CHTC Environment Summary ===${NC}"
echo ""
echo "User: ${CHTC_USERNAME}"
echo "Host: ${CHTC_HOST}"
echo ""
echo "Storage:"
echo "  Home: ${HOME_SIZE} / $(echo "${QUOTA_INFO}" | awk '{print $3}')"
echo "  Staging: ${STAGING_SIZE}"
echo ""
echo "Software:"
echo "  Python: ${PYTHON_VERSION}"
echo "  HTCondor: ${CONDOR_VERSION}"
echo ""
echo "Resources:"
echo "  Submit files in home: ${HOME_FILES}"
echo "  Containers found: ${STAGING_CONTAINERS}"
echo ""

if [[ "${STAGING_CONTAINERS}" -gt 0 ]]; then
    echo -e "${CYAN}=== Available Containers ===${NC}"
    while IFS= read -r container; do
        if [[ -n "${container}" ]]; then
            BASENAME=$(basename "${container}")
            SIZE=$(ssh chtc "ls -lh '${container}' 2>/dev/null | awk '{print \$5}'")
            echo "  ${BASENAME} (${SIZE})"
        fi
    done <<< "${CONTAINERS}"
    echo ""
fi

if [[ -n "${PROJECTS}" ]]; then
    echo -e "${CYAN}=== Existing Projects ===${NC}"
    while IFS= read -r project; do
        if [[ -n "${project}" ]]; then
            echo "  ${project}"
        fi
    done <<< "${PROJECTS}"
    echo ""
fi

echo "Full inventory saved to: ${INVENTORY_FILE}"
echo ""

# Offer to import existing projects
if [[ -n "${PROJECTS}" ]]; then
    echo -e "${YELLOW}Would you like to import existing projects to local workspace?${NC}"
    echo "This will download your existing CHTC projects for local management."
    echo ""
    read -p "Import projects? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        "${CHTC_ROOT}/scripts/import_existing.sh"
    fi
fi
