#!/bin/bash
# Get Started with CHTC Tools - Interactive setup

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         CHTC Tools - Getting Started                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "This will help you set up and test CHTC Tools."
echo ""

# Step 1: Installation
echo "Step 1: Installation"
echo "──────────────────────────────────────────────────────────"
if [[ -f ~/.chtcrc ]]; then
    echo "✓ Already installed"
else
    echo "Running installation..."
    ./install.sh
fi
echo ""

# Step 2: Configuration
echo "Step 2: Configuration Check"
echo "──────────────────────────────────────────────────────────"
source ~/.chtcrc

echo "CHTC Username: ${CHTC_USERNAME}"
echo "CHTC Host: ${CHTC_HOST}"
echo "WandB API Key: ${WANDB_API_KEY:0:20}..."
echo ""

read -p "Is this correct? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please edit ~/.chtcrc and run this script again"
    exit 1
fi

# Step 3: Test System
echo ""
echo "Step 3: System Test"
echo "──────────────────────────────────────────────────────────"
./test-system.sh
echo ""

# Step 4: Connect to CHTC
echo "Step 4: Connect to CHTC"
echo "──────────────────────────────────────────────────────────"
echo "This will establish SSH connection and prompt for 2FA."
echo ""
read -p "Connect now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./bin/chtc connect

    if [[ $? -eq 0 ]]; then
        echo ""
        echo "✓ Successfully connected!"
        echo ""
        ./bin/chtc quota
    else
        echo ""
        echo "✗ Connection failed. Please check:"
        echo "  1. Your password is correct"
        echo "  2. Duo 2FA is working"
        echo "  3. You're on campus network or VPN"
        exit 1
    fi
fi

# Step 5: Create test project
echo ""
echo "Step 5: Create Test Project"
echo "──────────────────────────────────────────────────────────"
read -p "Create a test project? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ./bin/chtc project init test-project
    echo ""
    echo "✓ Test project created at: ~/chtc-workspace/projects/test-project"
fi

# Final Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Setup Complete!                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next Steps:"
echo ""
echo "  1. Read the quick start guide:"
echo "     cat QUICKSTART.md"
echo ""
echo "  2. Try the example:"
echo "     cd ~/chtc-workspace/projects/test-project"
echo "     chtc submit jobs/example.sub --wandb"
echo ""
echo "  3. Monitor your job:"
echo "     chtc monitor --watch"
echo ""
echo "  4. View in WandB:"
echo "     https://wandb.ai/"
echo ""
echo "  5. Get help:"
echo "     chtc help"
echo ""
echo "Happy researching! 🚀"
