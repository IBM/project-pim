# AIS

AIS example allows you to deploy an AI application server on a partition which allows you to leverage AI capabilities on your on-prem environment.

## Architecture
[Add architecture diagram here]

## Steps to setup e2e flow

### Step 1: Preparing the images

#### Use Pre-built images
##### PIM Bootc Image
- Bootc image to bring up the AI partition that can run the above AI Services container.
- Build the PIM Bootc image using the instructions below.
```
<your-registry>/pim:ais
``` 

#### Build from source
If you wish to build your own version, you can follow below steps to build it.

##### Step 1: Build PIM Base image

Follow the steps provided [here](../../base-image) to build the base image or use the pre-built base-image `quay.io/powercloud/pim:base`

##### Step 2: Build PIM Bootc image

The Containerfile supports two methods for including the ai-services binary:

**Option 1: Build from source (default)**
```shell
# Build from main branch
podman build -t <your-registry>/pim:ais .

# Build from specific branch
podman build --build-arg BUILD_METHOD=build --build-arg BRANCH=feature/new-api -t <your-registry>/pim:ais .
```

**Option 2: Download from GitHub releases**
```shell
# Download specific release
podman build --build-arg BUILD_METHOD=download --build-arg RELEASE=v0.3.0 -t <your-registry>/pim:ais .

# Download for different architecture
podman build --build-arg BUILD_METHOD=download --build-arg RELEASE=v0.3.0 --build-arg ARCH=amd64 -t <your-registry>/pim:ais .
```

**Build Arguments:**
- `BUILD_METHOD`: `build` (default) or `download`
- `BRANCH`: Git branch to build from (default: `main`)
- `RELEASE`: Release version to download (default: `v0.3.0`)
- `ARCH`: Architecture for binary download (default: `ppc64le`, options: `ppc64le`, `amd64`, `arm64`, `s390x`)

##### Step 3: Push the image

```shell
podman push <your-registry>/pim:ais
```

### Step 2: Setting up PIM partition

Follow this [deployer guide](../../docs/deployer-guide.md) to setup PIM cli, configuring your AI partition and launching it.

## Configuration Parameters

The AIS example supports the following configuration parameters in your PIM config file:

#### aisAdminPassword
- Admin password for AI Services catalog (default: `admin123`)
- Used during the catalog configuration step

**Sample config:**
```ini
config-json = """
  {
        "aisAdminPassword": "your-secure-password"
  }
  """
```

## How It Works

The AIS setup uses a bootc-based architecture:

1. **PIM Bootc Image**:
   - Multi-stage build that includes the ai-services binary
   - Binary can be built from source or downloaded from GitHub releases
   - Includes all necessary configuration scripts and systemd services
   - Uses immutable ostree-based filesystem

2. **System-level setup** (`ais_config.service`):
   - Runs at partition boot time as a oneshot service
   - Uses the ai-services binary included in the bootc image
   - Executes `ai-services bootstrap --runtime podman`
   - Configures AI Services catalog with admin credentials
   - Waits for all 3 layers of catalog deployment to complete
   - Depends on: `base_config.service`, `network-online.target`, `cloud-config.target`

## Architecture Flow

```
Boot → ais_config.service (oneshot)
       ├─ Verify ai-services binary (included in bootc image)
       ├─ Setup Podman authentication
       ├─ Run: bootstrap --runtime podman
       └─ Run: catalog configure --runtime podman
              ├─ Layer 1: Secrets (catalog-secret, catalog-db-secret, auth-secret)
              ├─ Layer 2: Infrastructure (catalog-db, caddy)
              └─ Layer 3: Application (catalog-backend, catalog-ui)
```

**Key Features:**
- ai-services binary is included in the bootc image at build time (not downloaded at runtime)
- Supports both building from source and downloading from releases
- Immutable filesystem ensures consistency and reliability
- All configuration happens through systemd services
- Catalog pods (backend, UI, database) provide the AI Services functionality