# PIM Deployer guide

PIM deployer deploys custom-built PIM bootable container image composed of AI workloads like LLM inference engine or ML(Machine Learning) inference on Power environment with minimal effort.

## Setup Deployment environment

### Prerequisites
- P10 or higher power system host managed by HMC with VIOS to create a partition and provision the AI stack
- VIOS with an available disk size of at least 120GB (if physical disk is chosen to attach to LPAR) and media repository size of at least 2GB to host the bootstrap iso and cloud-init iso
  or
- An existing partition with an external storage managed by a SAN attached

### Installation
To ease the installation of dependencies, installer scripts are provided with PIM.

On IBMi run
```shell
source <(curl -sL https://raw.githubusercontent.com/IBM/project-pim/main/install_ibmi.sh)
```

On Linux(RHEL/Fedora/CentOS) run
```shell
source <(curl -sL https://raw.githubusercontent.com/IBM/project-pim/main/install_linux.sh)
```
### PIM Configurations
All PIM configurations are available in config.ini. How to configure key parameters is captured in [configuration-guide](configuration-guide.md)

### Run PIM solution
Python utility **pim.py** is used to perform various lifecycle operations like launch, update-config, update-compute, upgrade, rollback, status and destroy.

![alt text](pim_cli.png)

NOTE: 
- To run PIM in debug mode, pass `--debug` mode to the above command
- To pass a custom config file, set the value in `--config <path of config file>`, with this, if you want to do multiple AI use case deployments via PIM, different config.ini can be used.
### PIM Lifecycle management
PIM manages below listed lifecycles of partition provisioned with the AI stack.  

#### Launch
- This action provisions a new partition, attaches network, storage, loads the bootstrap and cloud-init iso to the VIOS media repositories and boots the partition with AI stack.
- If the deployer has a partition created with storage(SAN) attached, this flow continues to provision the AI stack similar to the fresh installation case.

```shell
export PYTHONPATH=.
python3 cli/pim.py launch
```

#### Upgrade
- This action upgrades the PIM AI workload image to the latest version available in the repository. If no latest image is available, it ignores the upgrade.
The user needs to note that image credentials should be updated in config.ini if the credentials used since the launch of the partition have expired.

```shell
export PYTHONPATH=.
python3 cli/pim.py upgrade
```

#### Rollback
- This action rolls back the current PIM AI workload image to the previous version of the image. 

```shell
export PYTHONPATH=.
python3 cli/pim.py rollback
```

#### Update-config
- This action updates PIM configuration(pim-config.json) like updating/changing the AI model, model related parameters(for eg: **--model** or **--max_model_len** in the case of vLLM) on an LPAR with AI stack already provisioned.
Edit attributes below to update PIM configurations
![alt text](update_conf.png)

```shell
export PYTHONPATH=.
python3 cli/pim.py update-config
```

#### Update-compute
- This action updates existing PIM partition's compute like CPU, memory. CPU mode can be switched from dedicated to shared mode.
Update the CPU/memory configurations either in T-shirt-sized config files(eg: [large](../cli/partition-flavor/large.ini)) or custom-config section of [config.ini](../config.ini)

```shell
export PYTHONPATH=.
python3 cli/pim.py update-compute
```

#### Status
- This action depicts the current booted version, rollback image version of the AI workload image and their corresponding checksum values.

```shell
export PYTHONPATH=.
python3 cli/pim.py status

● Booted image: quay.io/<account id>/pim:vllm

        Digest: sha256:21d2d46af19e4aaa6917571bd4e187d65e239e2a5c90d872c67a0c37e26ad4af (ppc64le)

       Version: 43.20250824.0 (2025-09-09T11:08:47Z)
 Rollback image: quay.io/<account id>/pim:vllm
     Digest: sha256:f9dddcf7220334401cf6f3447a6ff39db24bd392a1e7c3073f2e07578ecfbf61 (ppc64le)
     Version: 43.20250824.0 (2025-09-09T10:40:35Z)
```

#### Destroy
- This action cleans up the VIOS, storage mappings and destroys the partition if the LPAR is provisioned by the PIM solution.

```shell
export PYTHONPATH=.
python3 cli/pim.py destroy
```
