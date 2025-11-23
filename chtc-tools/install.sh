#!/bin/bash
# CHTC Tools Installation Script

set -e

CHTC_TOOLS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== CHTC Tools Installation ==="
echo ""

# Check for required commands
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "Error: $1 is not installed"
        echo "Please install $1 and try again"
        exit 1
    fi
}

echo "Checking dependencies..."
check_command ssh
check_command rsync
check_command python3

echo "✓ All required commands found"
echo ""

# Check for Python packages
echo "Checking Python dependencies..."
if ! python3 -c "import wandb" 2>/dev/null; then
    echo "Installing WandB and dependencies..."
    pip3 install wandb pyyaml tabulate rich || {
        echo "Error: Failed to install Python packages"
        echo "Please run: pip3 install wandb pyyaml tabulate rich"
        exit 1
    }
    echo "✓ Python packages installed"
else
    echo "✓ Python packages already installed"
fi

echo ""

# Setup configuration
if [[ ! -f "${HOME}/.chtcrc" ]]; then
    echo "Setting up configuration..."
    cp "${CHTC_TOOLS_DIR}/.chtcrc.example" "${HOME}/.chtcrc"
    echo "✓ Configuration file created at ~/.chtcrc"
    echo ""
    echo "IMPORTANT: Edit ~/.chtcrc with your CHTC username and settings"
    echo ""
else
    echo "✓ Configuration file already exists at ~/.chtcrc"
fi

# Create workspace directory
WORKSPACE_DIR="${HOME}/chtc-workspace"
mkdir -p "${WORKSPACE_DIR}"/{projects,logs}
echo "✓ Workspace created at ${WORKSPACE_DIR}"

# Create .chtc directory for metadata
mkdir -p "${HOME}/.chtc/ssh_control"
chmod 700 "${HOME}/.chtc/ssh_control"
echo "✓ Metadata directory created at ~/.chtc"

# Add to PATH
SHELL_RC=""
if [[ -f "${HOME}/.bashrc" ]]; then
    SHELL_RC="${HOME}/.bashrc"
elif [[ -f "${HOME}/.zshrc" ]]; then
    SHELL_RC="${HOME}/.zshrc"
fi

if [[ -n "${SHELL_RC}" ]]; then
    if ! grep -q "chtc-tools/bin" "${SHELL_RC}"; then
        echo "" >> "${SHELL_RC}"
        echo "# CHTC Tools" >> "${SHELL_RC}"
        echo "export PATH=\"${CHTC_TOOLS_DIR}/bin:\$PATH\"" >> "${SHELL_RC}"
        echo "✓ Added to PATH in ${SHELL_RC}"
        echo ""
        echo "Run: source ${SHELL_RC}"
        echo "Or start a new terminal session"
    else
        echo "✓ Already in PATH"
    fi
else
    echo "⚠ Could not find shell rc file"
    echo "Add this to your shell configuration:"
    echo "  export PATH=\"${CHTC_TOOLS_DIR}/bin:\$PATH\""
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit ~/.chtcrc with your CHTC username"
echo "  2. Reload your shell or run: source ${SHELL_RC}"
echo "  3. Connect to CHTC: chtc connect"
echo "  4. Create a project: chtc project init my-project"
echo ""
echo "For help: chtc help"
echo "Documentation: ${CHTC_TOOLS_DIR}/README.md"
