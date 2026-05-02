#!/bin/bash
# Setup passwordless SSH to CHTC

set -e

echo "=== CHTC Passwordless SSH Setup ==="
echo ""

CHTC_USER="nandwani2"
CHTC_HOST="ap2002.chtc.wisc.edu"
KEY_FILE="${HOME}/.ssh/chtc_ed25519"

# Check if key exists
if [[ ! -f "${KEY_FILE}" ]]; then
    echo "Generating SSH key..."
    ssh-keygen -t ed25519 -f "${KEY_FILE}" -N "" -C "chtc-tools-$(hostname)"
    echo "✓ SSH key generated"
else
    echo "✓ SSH key already exists"
fi

echo ""
echo "Public key:"
cat "${KEY_FILE}.pub"
echo ""

# Add to SSH config
echo "Adding to SSH config..."
SSH_CONFIG="${HOME}/.ssh/config"
touch "${SSH_CONFIG}"

if ! grep -q "Host chtc" "${SSH_CONFIG}"; then
    cat >> "${SSH_CONFIG}" << EOF

# CHTC Configuration
Host chtc
    HostName ${CHTC_HOST}
    User ${CHTC_USER}
    IdentityFile ${KEY_FILE}
    ControlMaster auto
    ControlPath ~/.ssh/control-%r@%h:%p
    ControlPersist 4h
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF
    echo "✓ SSH config updated"
else
    echo "✓ SSH config already has CHTC entry"
fi

echo ""
echo "Now copying SSH key to CHTC..."
echo "You will be prompted for:"
echo "  1. Your password"
echo "  2. Duo 2FA (push notification or code)"
echo ""
read -p "Press Enter to continue..."

# Copy key using password authentication
ssh-copy-id -i "${KEY_FILE}.pub" -o PreferredAuthentications=keyboard-interactive,password "${CHTC_USER}@${CHTC_HOST}"

if [[ $? -eq 0 ]]; then
    echo ""
    echo "✓ SSH key copied successfully!"
    echo ""
    echo "Testing passwordless connection..."

    if ssh chtc "echo 'Connection successful!'" 2>/dev/null; then
        echo "✓ Passwordless SSH working!"
        echo ""
        echo "You can now connect with: ssh chtc"
        echo "Or use: chtc connect (no password needed)"
    else
        echo "✗ Test failed, but key might be installed"
        echo "Try: ssh chtc"
    fi
else
    echo ""
    echo "✗ Failed to copy SSH key"
    echo ""
    echo "Manual setup:"
    echo "1. Run: ssh ${CHTC_USER}@${CHTC_HOST}"
    echo "2. On CHTC, run: mkdir -p ~/.ssh && chmod 700 ~/.ssh"
    echo "3. On CHTC, run: nano ~/.ssh/authorized_keys"
    echo "4. Paste this line and save:"
    cat "${KEY_FILE}.pub"
    echo "5. On CHTC, run: chmod 600 ~/.ssh/authorized_keys"
fi
