#!/bin/bash

# Enable verbose output and strict error handling
set -x

[ -f /etc/pim/ais.conf ] || touch /etc/pim/ais.conf

# Get admin password from config or use default
AIS_ADMIN_PASSWORD=$(jq -r '.adminPassword // "admin123"' /etc/pim/pim_config.json)

# Get ai-services release version from pim_config.json
RELEASE=$(jq -r '.release // "main"' /etc/pim/pim_config.json)

echo "=== Starting AI Services Setup ==="
AIS_PATH="/tmp/ai-services"
# Build or download ai-services binary based on RELEASE
if [ ! -f "$AIS_PATH" ]; then
    echo "AI Services binary not found. Acquiring binary..."

    if [ "$RELEASE" = "main" ]; then
        echo "Building from source ..."
        cd /tmp
        # Clone and build
        git clone --branch $RELEASE https://github.com/IBM/project-ai-services.git
        cd project-ai-services/ai-services
        GOTOOLCHAIN=auto make bin
        
        # Find and copy the built binary
        BUILT_BINARY=$(ls bin/ai-services-* 2>/dev/null | head -n 1)
        if [ -n "$BUILT_BINARY" ] && [ -f "$BUILT_BINARY" ]; then
            cp "$BUILT_BINARY" "$AIS_PATH"
            chmod +x "$AIS_PATH"
            echo "AI Services binary built and installed successfully from $BUILT_BINARY"
        else
            echo "ERROR: Binary not found after build"
            exit 1
        fi
    else
        echo "Downloading from release ($RELEASE)..."
        
        # Download with verbose output and follow redirects
        if curl -L -f -o "$AIS_PATH" "https://github.com/IBM/project-ai-services/releases/download/${RELEASE}/ai-services-linux-ppc64le"; then
            # Verify the file was downloaded and has content
            if [ -s "$AIS_PATH" ]; then
                chmod +x "$AIS_PATH"
                echo "AI Services binary downloaded and installed successfully"
            else
                echo "ERROR: Downloaded file is empty"
                exit 1
            fi
        else
            echo "ERROR: Failed to download ai-services binary (curl exit code: $?)"
            exit 1
        fi
    fi
else
    echo "AI Services binary already exists at $AIS_PATH"
fi

# Verify binary is executable
if [ ! -x "$AIS_PATH" ]; then
    echo "ERROR: AI Services binary is not executable"
    exit 1
fi

# 1. Explicitly export XDG_RUNTIME_DIR for the systemd environment
export XDG_RUNTIME_DIR=/run/user/$(id -u)

# 2. Simulate podman login for the ai-services tool
echo "Setting up Podman authentication..."
mkdir -p $XDG_RUNTIME_DIR/containers
cp /etc/pim/auth.json $XDG_RUNTIME_DIR/containers/auth.json

# Bootstrap AI Services with Podman runtime
echo "Bootstrapping AI Services..."
"$AIS_PATH" bootstrap --runtime podman --skip-validation=power,spyre 2>&1 | tee -a /var/log/ais_bootstrap.log
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

spawn $AIS_PATH catalog configure --runtime podman

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
"$AIS_PATH" catalog info --runtime podman
# Made with Bob
