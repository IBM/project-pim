# AIS

The AIS example demonstrates how to deploy AI Services on a PowerVM partition, enabling you to run AI workloads in your on-premises environment.

## Architecture

[Add architecture diagram here]

## Steps to setup e2e flow

### Step 1: Preparing the images

#### Use Pre-built images
##### PIM Bootc Image

- Bootc image to bring up the AI partition that can run the above AI Services application.
- Recommended to use the pre-built PIM Bootc image and its available to consume directly via below image.

```
quay.io/powercloud/pim:ais
```

#### Build from source

If you wish to build your own version, you can follow below steps to build it.

##### Step 1: Build PIM Base image

Follow the steps provided [here](../../base-image) to build the base image or use the pre-built base-image `quay.io/powercloud/pim:base`

##### Step 2: Build PIM Bootc image

```shell
podman build -t <your-registry>/pim:ais .
```

The ai-services binary will be built or downloaded at runtime based on the configuration in your config.ini file (see Configuration Parameters below).

##### Step 3: Push the image

```shell
podman push <your-registry>/pim:ais
```

### Step 2: Setting up PIM partition

Follow this [deployer guide](../../docs/deployer-guide.md) to setup PIM cli, configuring your AI partition and launching it.

## Configuration Parameters

The AIS example supports the following configuration parameters in your PIM config file:

#### release

- Specifies the AI Services version to use (default: `main`)
- Set to `main` to build from the latest source code
- Set to a specific version tag (e.g., `v0.3.0`) to download a pre-built binary from GitHub releases

#### adminPassword

- Admin password for AI Services catalog (default: `admin123`)
- Used during the catalog configuration step

**Sample config:**

```ini
config-json = """
  {
        "release": "v0.3.0",
        "adminPassword": "your-secure-password"
  }
  """
```

## How It Works

The AIS setup uses a bootc-based architecture:

1. **PIM Bootc Image**:
   - Includes all necessary configuration scripts and systemd services
   - Contains build tools (git, make, golang) and download tools (curl)
   - Uses immutable ostree-based filesystem

2. **System-level setup** (`ais_config.service`):
   - Runs at partition boot time as a oneshot service
   - Acquires ai-services binary based on config.ini settings:
     - **Build method**: Clones repository and builds from source
     - **Download method**: Downloads pre-built binary from GitHub releases
   - Executes `ai-services bootstrap --runtime podman`
   - Configures AI Services catalog with admin credentials
   - Waits for all 3 layers of catalog deployment to complete
   - Depends on: `base_config.service`, `network-online.target`, `cloud-config.target`

## Architecture Flow

```
Boot → ais_config.service (oneshot)
       ├─ Acquire ai-services binary (build from source OR download from release)
       ├─ Setup Podman authentication
       ├─ Run: bootstrap --runtime podman
       └─ Run: catalog configure --runtime podman
              ├─ Layer 1: Secrets (catalog-secret, catalog-db-secret, auth-secret)
              ├─ Layer 2: Infrastructure (catalog-db, caddy)
              └─ Layer 3: Application (catalog-backend, catalog-ui)
```

**Key Features:**

- ai-services binary is acquired at runtime based on config.ini settings
- Supports both building from source and downloading from releases
- Flexible configuration allows switching between build methods without rebuilding the image
- Immutable filesystem ensures consistency and reliability
- All configuration happens through systemd services
- Catalog pods (backend, UI, database) provide the AI Services functionality

