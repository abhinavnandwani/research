#!/bin/bash
# Test CHTC Tools installation and basic functionality

set -e

echo "=== CHTC Tools System Test ==="
echo ""

# Test 1: Check if chtc command is available
echo "[1/7] Checking chtc command..."
if command -v chtc &> /dev/null; then
    echo "✓ chtc command found"
else
    echo "✗ chtc command not found"
    echo "  Run: export PATH=\"$(pwd)/bin:\$PATH\""
    exit 1
fi

# Test 2: Check configuration
echo ""
echo "[2/7] Checking configuration..."
if [[ -f "${HOME}/.chtcrc" ]]; then
    echo "✓ Configuration file exists"

    # Source config
    source "${HOME}/.chtcrc"

    if [[ -n "${CHTC_USERNAME}" ]]; then
        echo "✓ CHTC_USERNAME set: ${CHTC_USERNAME}"
    else
        echo "✗ CHTC_USERNAME not set in ~/.chtcrc"
        exit 1
    fi

    if [[ -n "${WANDB_API_KEY}" ]]; then
        echo "✓ WANDB_API_KEY configured"
    else
        echo "⚠ WANDB_API_KEY not set (WandB features will not work)"
    fi
else
    echo "✗ Configuration file not found"
    echo "  Run: ./install.sh"
    exit 1
fi

# Test 3: Check Python dependencies
echo ""
echo "[3/7] Checking Python dependencies..."
if python3 -c "import wandb" 2>/dev/null; then
    echo "✓ wandb installed"
else
    echo "✗ wandb not installed"
    echo "  Run: pip3 install wandb pyyaml tabulate rich"
    exit 1
fi

if python3 -c "import yaml" 2>/dev/null; then
    echo "✓ pyyaml installed"
else
    echo "⚠ pyyaml not installed (recommended)"
fi

# Test 4: Check SSH connectivity (if connected)
echo ""
echo "[4/7] Checking SSH connectivity..."
if chtc status &>/dev/null; then
    echo "✓ Already connected to CHTC"
else
    echo "⚠ Not connected to CHTC"
    echo "  Run: chtc connect (you will need password + Duo 2FA)"
fi

# Test 5: Check workspace
echo ""
echo "[5/7] Checking workspace..."
if [[ -d "${CHTC_LOCAL_WORKSPACE}" ]]; then
    echo "✓ Workspace exists: ${CHTC_LOCAL_WORKSPACE}"
else
    echo "⚠ Workspace not found, creating..."
    mkdir -p "${CHTC_LOCAL_WORKSPACE}"/{projects,logs}
    echo "✓ Workspace created"
fi

# Test 6: Test WandB connectivity
echo ""
echo "[6/7] Testing WandB connectivity..."
if [[ -n "${WANDB_API_KEY}" ]]; then
    if python3 -c "import wandb; wandb.login(key='${WANDB_API_KEY}')" 2>/dev/null; then
        echo "✓ WandB authentication successful"
    else
        echo "✗ WandB authentication failed"
        echo "  Check your API key in ~/.chtcrc"
    fi
else
    echo "⚠ Skipping (no API key configured)"
fi

# Test 7: Check helper scripts
echo ""
echo "[7/7] Checking helper scripts..."
SCRIPTS=(
    "scripts/submit.sh"
    "scripts/monitor.sh"
    "scripts/fetch_logs.sh"
    "scripts/container.sh"
    "scripts/project.sh"
    "scripts/wandb_logger.py"
)

ALL_GOOD=true
for script in "${SCRIPTS[@]}"; do
    if [[ -f "${script}" ]] && [[ -x "${script}" ]]; then
        echo "✓ ${script}"
    else
        echo "✗ ${script} missing or not executable"
        ALL_GOOD=false
    fi
done

echo ""
echo "=== Test Summary ==="
echo ""

if [[ "${ALL_GOOD}" == true ]]; then
    echo "✓ All tests passed!"
    echo ""
    echo "Next steps:"
    echo "  1. Connect to CHTC: chtc connect"
    echo "  2. Create a project: chtc project init test-project"
    echo "  3. Submit a test job: chtc submit <job.sub> --wandb"
    echo ""
    echo "Quick reference: cat QUICKSTART.md"
else
    echo "✗ Some tests failed"
    echo "Please fix the issues above and try again"
    exit 1
fi
