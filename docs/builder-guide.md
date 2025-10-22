# PIM Builder guide

This guide helps to build a PIM image for AI workloads of their choice in Linux environment.
A few Inferencing AI workloads like entity extraction, fraud detection are provided for PIM provisioning as reference [here](../examples/). LLM is not mandatory for applications based on machine learning models.

## Base image
Base PIM image can be built on RHEL/Fedora/CentOS bootc image. Officially, PIM uses RHEL bootc base image. It wraps the cloud-init tool to perform initial network/ssh configurations and base config service. To decouple/ease the building of AI workloads, the base image is built separately.
This base image is constant across different AI workloads/use cases.  
Steps to build PIM image are captured [here](../base-image/README.md).

**NOTE: Builder needs to use a RHEL/CentOS/Fedora-based VM/lpar to build the PIM base images and custom AI workload images. For the RHEL base image, the user needs to use an RHEL node with a subscription activated. Base image for remaining OSs can be built on either CentOS or Fedora VM**

## AI image
AI image holds steps to run the AI application when it is deployed on a partition via PIM. You need to pass this AI image only to the PIM deployer utility. It usually follows below [application structure](app_structure.png) to get it deployed via PIM. 

- app - AI application-specific business logic and contains build scripts to build the container image of the AI application.
- entity.container - A systemd service file to pull the AI workload image(entity extraction) from a registry during runtime and run the AI application(entity extraction) as a container. Ensure all container-related inputs are added in the `Container` block.
- Containerfile - Base image should be a PIM base image. Contains copy steps to copy the entity.container and configuration scripts to run them when the system starts.

Build the PIM based AI workload image using the `podman build` command

A reference guide on building an AI workload is here [examples](../examples/README.md)

## AI Application Bring-up Sequence

Before starting the AI application, it’s crucial to ensure that all required configurations and dependent services are up and running. This guarantees that all prerequisites are satisfied and the AI application can start smoothly without failures.

To define the startup sequence of services, the `.container` file uses two key directives: `Require` and `After`.

### Service Dependency Directives

* **Require:**
  Specifies the list of services that must be started before the given service. If any of the required services fail to start, the dependent service will not start.

* **After:**
  Defines the startup order of services. A service will start only after all services listed in its `After` directive have been started.

> **Note:**
> Ensure that your `.container` file is properly configured with the correct `Require` and `After` directives to maintain the correct service hierarchy.

### Example: HMC Agent Service Hierarchy

In the **HMC Agent** example, the bring-up sequence follows a layered dependency structure:

1. **base.service** – The starting point of the application, included in the base image.
2. **llm_config.service** – Declares `Require=base.service` and runs only after `base.service` has started.
3. **vllm.service** – Requires `llm_config.service` and waits until it completes before starting.
4. **llm_readiness.service** – Starts after `vllm.service` to verify that the vLLM service is fully operational.
5. **hmc_config.service** – Depends on `llm_readiness.service` to ensure the vLLM container is fully ready to handle incoming requests.
6. **hmc_server.service** – Requires `hmc_config.service` to complete successfully, ensuring that all HMC configurations are in place before the server starts.
7. **hmc_agent.service** – Depends on `hmc_server.service`, as the agent requires an active server to process requests, completing the bring-up chain.


This sequence ensures that each service starts only after its dependencies are in active state, resulting in a smooth and reliable startup process for the AI application.
