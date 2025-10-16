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
- **Builder:** Someone who builds a bootable AI container image to bring up the AI stack with the deployer flow. We have provided pre-built PIM Bootc images for various example applications, it is recommended to use them. If you want to create and deploy a new application or you want to build the PIM bootc images by yourself please refer to [builder-guide.md](docs/builder-guide.md) for more details.
- **Deployer:** Someone who deploys a PIM solution to bring up the AI stack in IBM core environments. Refer to [deployer-guide.md](docs/deployer-guide.md) for more details.

## Getting started
To get started, you can use the default [config.ini](config.ini) which has pre-built PIM Bootc images loaded to deploy an vLLM stack. 
- **Step 1: Set up PIM**
    - You can follow the steps given [here](docs/deployer-guide.md#installation) to set up PIM Cli on your IBMi/Linux machine and please go over the [Prerequisites](docs/deployer-guide.md#prerequisites) section here before deploying the AI partition.
- **Step 2: Configure your AI partition**
    - Read through this [guide](docs/configuration-guide.md) and fill appropriate values in [config.ini](config.ini).
    - You can skip the AI portion since the default configuration provided will just work fine. Instructions to build your own AI stack via PIM is detailed [here](#build-your-own-pim-stack)
- **Step 3: Run the Launch Command**
```shell
python cli/pim.py launch
```
- **Step 4: Access the application**
    - After the ```launch``` command successfully creates the partition, vLLM’s OpenAI API server will be available to use on port 8000 on the IP you have configured.

## Build your own PIM AI stack
This section details how to build your own PIM AI stack, for example we have taken one of our AI examples provided, simple-entity-extraction. Simple entity extraction is an AI tool designed to extract entities from the given text with the help of vLLM. 

This AI stack contains two components
1. **Entity Extraction Python app** - An UI framework to get input from user, build prompt and send it to vLLM for processing it. 
2. **vLLM** - Run the prompt to extract entities.

Steps to build the AI Image:
- **Step 1: Build the application**
    - ***vLLM:***
        - Open source [vLLM](https://github.com/vllm-project/vllm) application will be used.
    - ***Entity Extraction App:***
        - A sample entity extraction application is provided [here](examples/simple-entity-extraction/app/entity.py) that uses the vLLM's OpenAI `/chat/completion` API to do the entity extraction.
- **Step 2: Containerize the application**
    - ***vLLM:***
        - Recommended to use below vLLM application image built and published [here](https://community.ibm.com/community/user/blogs/priya-seth/2023/04/05/open-source-containers-for-power-in-icr) by IBM on Linux Power team.
        ```
        icr.io/ppc64le-oss/vllm-ppc64le:0.10.1.dev852.gee01645db.d20250827
        ```
        - Or you can use your own image or use the script provided [here](examples/vllm/app) to build it from source
    - ***Entity Extraction App:***
        - [README](examples/simple-entity-extraction/app) for steps to build the container image for the entity extraction application.
- **Step 3: Build the PIM Bootc image**
    Step 2 details the process of containarizing the applications involved in the AI stack. This step is required to build the Bootc image required to bringup the AI stack. It orchestrates the vLLM and Entity Extraction Python applications in separate containers when we create the AI partition out of this built image. 
    - ***vLLM:***
        - Recommended to use below PIM Bootc image built by PIM team
        ```
        quay.io/powercloud/pim:vllm
        ```
        - Or you can build your own image by following the [README](examples/vllm/README.md#build-from-source)
    - ***Entity Extraction App:***
        - Application, build scripts and README to build the AI image are given [here](examples/simple-entity-extraction), ensure that you use the vLLM AI image mentioned in the previous step as base image(FROM) here.
    
    **Note:** In the example used here uses vLLM in its functionality, hence used vLLM as a base image for building the Entity Extraction PIM Bootc image. In case vLLM is not required use cases like traditional ML use case, you can use the [base-image](base-image/).

Once your final PIM Bootc image is built with the above steps, you can deploy PIM stack via deployer flow documented [here](docs/deployer-guide.md).

## Supported Versions
To successfully deploy PIM, various components of the IBM Power software stack would at the minimum have to be at the levels listed below:

| Component                                    |           P10           |             P11           |
| -------------------------------------------- | ----------------------- | ------------------------- |
| Hardware Management Console(HMC)             | 1061                    | 1110                      |
| Partition Firmware(PFW)                      | 1050.50, 1060.50        | 1110.00                   |
| Virtual IO Server(VIOS)                      | 4.1.1.0                 | 4.1.1.00                  |
| IBMi                                         | 7.5                     | 7.6                       |
