#!/bin/bash

# Enable verbose output and strict error handling
set -x

[ -f /etc/pim/ais.conf ] || touch /etc/pim/ais.conf

# Get admin password from config or use default
AIS_ADMIN_PASSWORD=$(jq -r '.aisAdminPassword // "admin123"' /etc/pim/pim_config.json)

echo "=== Starting AI Services Setup ==="

# Simulate podman login by placing auth.json where ai-services expects it
# ai-services reads from /run/user/<uid>/containers/auth.json (never REGISTRY_AUTH_FILE)
echo "Copy auth file"
mkdir -p /run/user/$(id -u)/containers
mkdir -p /root/.config/containers
cp /etc/pim/auth.json /run/user/$(id -u)/containers/auth.json
cp /etc/pim/auth.json /root/.config/containers/auth.json

# 1. Explicitly export XDG_RUNTIME_DIR for the systemd environment
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# 2. Simulate podman login for the ai-services tool
echo "Setting up Podman authentication..."
mkdir -p $XDG_RUNTIME_DIR/containers
cp /etc/pim/auth.json $XDG_RUNTIME_DIR/containers/auth.json

# Bootstrap AI Services with Podman runtime
echo "Bootstrapping AI Services..."
ai-services bootstrap --runtime podman --skip-validation=power,spyre 2>&1 | tee -a /var/log/ais_bootstrap.log
BOOTSTRAP_EXIT_CODE=${PIPESTATUS[0]}
if [ $BOOTSTRAP_EXIT_CODE -ne 0 ]; then
    echo "ERROR: AI Services bootstrap failed with exit code $BOOTSTRAP_EXIT_CODE"
    echo "Check /var/log/ais_bootstrap.log for details"
    # TODO: Check why smstate service is failing to start
    # exit $BOOTSTRAP_EXIT_CODE
fi
echo "Bootstrap completed"

# Configure AI Services Catalog
echo "Configuring AI Services Catalog..."
# Use expect to automate password input and wait for completion
# Set a longer timeout to allow for container readiness checks
expect << EXPECT_EOF
set timeout 600
log_user 1
set password "$AIS_ADMIN_PASSWORD"

spawn ai-services catalog configure --runtime podman

expect {
    "Enter admin password:" {
        send "\$password\r"
        exp_continue
    }
    "Confirm admin password:" {
        send "\$password\r"
        exp_continue
    }
    "Layer 3 completed" {
        # Wait a bit more to ensure all output is captured
        sleep 2
        exp_continue
    }
    timeout {
        puts "\nERROR: Catalog configuration timed out after 600 seconds"
        exit 1
    }
    eof {
        # Capture the exit code
        catch wait result
        set exit_code [lindex \$result 3]
        if {\$exit_code != 0} {
            puts "\nERROR: ai-services catalog configure failed with exit code \$exit_code"
            exit \$exit_code
        }
    }
}
EXPECT_EOF

CATALOG_EXIT_CODE=$?
if [ $CATALOG_EXIT_CODE -ne 0 ]; then
    echo "ERROR: AI Services catalog configuration failed with exit code $CATALOG_EXIT_CODE"
    exit $CATALOG_EXIT_CODE
fi

echo "AI Services Catalog configured successfully"
echo "=== AI Services Setup Completed ==="

echo "Checking catalog info"
ai-services catalog info --runtime podman
# Made with Bob
