# Power Inference Microservices (PIM)

⚠️ **Experimental Software** ⚠️ 

This project is currently in an experimental phase, and as such, the code is unstable and subject to change. We advise against using it in production environments. Additionally, there is no formal support provided for any issues encountered with this repository. If you encounter problems, please open a GitHub issue.

**Description:**

The PIM project enables the spinning up of an AI environment with very little user intervention, adjacent to other workloads running on IBM Power. These workloads might be running on any of the supported operating systems on IBM Power: IBMi, or Linux, as long as they are managed by a Hardware Management Console (HMC). The PIM solution leverages Bootable Containers (bootc), a modern tool for deploying and configuring immutable Linux systems.
PIM provides an end-to-end solution for AI stack installation by creating a Logical Partition (LPAR) with a specified AI stack image. This involves network and storage attachment, and the LPAR is then booted with the configured image.

![alt text](docs/architecture.png)

## Key highlights of the PIM solution
- Seamless Update: System updates are automatic if a newer version of the image is publicly available. Otherwise, when the user upgrades via PIM [upgrade command](docs/deployer-guide.md#upgrade) with the latest credentials, the system updates are pulled and applied from the configured private registry over a reboot of the system.
- Rollback: bootc preserves the state of the system. In case of a disruption in Updates, the system can be rolled back to a previous version.
- Makes admin's management simple by easing day 2 operations like monitoring, upgrading and managing.
- Provides end-to-end software lifecycle management operations like [launch](docs/deployer-guide.md#launch), [destroy](docs/deployer-guide.md#destroy), [update-config](docs/deployer-guide.md#update-config), [update-compute](docs/deployer-guide.md#update-config), [rollback](docs/deployer-guide.md#rollback) and [status](docs/deployer-guide.md#status).
- Provides AI inferencing capability on CPU currently. The intent is to provide inferencing-based accelerators available on the platform as and when they become available.

## PIM Personas
PIM has 2 personas, namely the builder and the deployer.
- **Builder:** Someone who builds a bootable AI container image to bring up the AI stack with the deployer flow. Refer to [builder-guide.md](docs/builder-guide.md) for more details.
- **Deployer:** Someone who deploys a PIM solution to bring up the AI stack in IBM core environments. Refer to [deployer-guide.md](docs/deployer-guide.md) for more details.

## Getting started
To get started, you can follow steps below to build and deploy a simple entity extraction application which uses vLLM.
### Builder steps
- **Step 1: Build the application**
    - ***vLLM:***
        - Open source [vLLM](https://github.com/vllm-project/vllm) application can be used.
    - ***Entity Extraction App:***
        - A sample entity extraction application is provided [here](examples/simple-entity-extraction/app/entity.py) that uses the OpenAI `/chat/completion` API to do entity extraction.
- **Step 2: Containerize the application**
    - ***vLLM:***
        - Follow the instructions in the [README](examples/vllm/app/README.md) to build the vLLM application's container image. It has a script that pulls open-source vLLM code base and builds a container image.
    - ***Entity Extraction App:***
        - [README](examples/simple-entity-extraction/app/README.md) for steps to build the container image for an entity extraction application.
- **Step 3: Build the Base image**
    - Follow base image building steps given [here](base-image/README.md).
- **Step 4: Build the AI image**
    - ***vLLM:***
        - Follow steps given [here](examples/vllm/README.md) to build the vLLM AI image, ensure that you use the image created in `step-3` as base image(FROM).
    - ***Entity Extraction App:***
        - Scripts and README to build the AI image are given [here](examples/simple-entity-extraction/README.md), ensure that you use the vLLM AI image created in the previous step as base image(FROM) here.
### Deployer steps
- **Step 1: Set up PIM**
    - You can follow the steps to set up PIM on your IBMi/Linux machine given [here](docs/deployer-guide.md#installation) and please go over the [Prerequisites](docs/deployer-guide.md#prerequisites) section here before deploying a AI partition.
- **Step 2: Configure your AI partition**
    - Read through this [guide](docs/configuration-guide.md) and fill appropriate values in [config.ini](config.ini).
    - Use final image built on builder step 4 in `ai.image` field.
- **Step 3: Run the Launch Command**
```shell
python cli/pim.py launch
```
- **Step 4: Access the application**
    - After the ```launch``` command successfully creates the partition, you can access the UI for the entity extraction application on port ```8501```, using the IP address provided during the launch configuration in config.ini.

## Supported Versions
To successfully deploy PIM, various components of the IBM Power software stack would at the minimum have to be at the levels listed below:

| Component                                    |           P10           |             P11           |
| -------------------------------------------- | ----------------------- | ------------------------- |
| Hardware Management Console(HMC)             | 1061                    | 1110                      |
| Partition Firmware(PFW)                      | 1050                    | 1110                      |
| Virtual IO Server(VIOS)                      | 4.1.1.0                 | 4.1.1.00                  |
| IBMi                                         | 7.5                     | 7.6                       |
