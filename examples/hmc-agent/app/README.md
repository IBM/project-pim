# HMC Server
HMC Server is an MCP server with several tools to interact or perform action on HMC. HMC server is built using FastMCP server that listens on port 8001.

**NOTE: If user wants to run HMC server on a port other than default 8001, make sure to update same port in variable `MCP_SERVER_URL` in agent.py**

## Steps to build HMC server container image
1. Enter into hmc-agent app directory containing [HMC Server Containerfile](./Containerfile-server)
2. Build HMC server container image using podman
```
podman build -f Containerfile-server -t <your_registry>/hmc_server
```
3. Push the HMC server container image to container registry
```
podman push <your_registry>/hmc_server
```

# HMC agent
HMC agent is an MCP client which interacts with MCP server to get a response to user prompt. Its built using langgraph and has an user interface to accept user prompts and display the response.

## Steps to build HMC server container image
1. Enter into hmc-agent app directory containing [HMC Agent Containerfile](./Containerfile-agent)
2. Build HMC agent container image using podman
```
podman build -f Containerfile-agent -t <your_registry>/hmc_agent
```
3. Push the HMC agent container image to container registry
```
podman push <your_registry>/hmc_agent
```

### Sample prompts:
HMC Agent supports various tools which perform operations on HMC server and returns response to user prompts.  
Currently it supports tools to `Get HMC version`, `Get systems managed by HMC`, `Get compute usage of a Power server`, `Get logical partitions created under a power server`, `Get partition stats of a specific lpar`.  
Support for tools to Read and Write HMC operations will be added subsequently.

Below are sample prompts triggered from user interface
```
- get me the HMC version
- get me the systems managed by HMC
- get me the compute usage of system 'C340F2U01-ZZ'
- get me the logical partitions created under system 'C340F1U07-ICP-Dedicated'
- get me the stats of partition 'hamzy-bastion-f36de29b-00015f1f' under system 'C340F1U07-ICP-Dedicated'
```
