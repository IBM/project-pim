# AI agent to manage Power Infra using MCP Server built for HMC

This is a reference application built for PIM stack using MCP server leveraging HMC APIs.
this wraps HMC server and agent on top of [vLLM server](../../examples/vllm/README.md) built.

It bootstraps HMC server and HMC agent components. Steps to build and containerize them are [here](app/README.md)

## Configuration

Since vLLM AI image can be used as a base for many LLM inferencing applications like chatbot, entity extraction and many more.  Below provided configurations tune the vLLM engine as per the AI use case. 

This can be fed into the application via `config-json` explained [here](../../docs/configuration-guide.md#ai)

#### llmImage
vLLM container image built using app section [here](../vllm/app/README.md)
#### llmArgs
Args you can pass it to your vLLM inference engine like model name, maximum model length etc. model name passed as part of llmArgs will be used by HMC agent.
#### llmEnv
Environment variables that you intend to set while running vLLM inference engine
#### hmcConfig
HMC credential details like ip address, username and password used by HMC server to authenticate with HMC
#### mcpServerURL
MCP server URL endpoint which HMC agent uses to talk to HMC server. Make sure to pass host IP address in the URL

**Sample config:**
```ini
config-json = """
  {
    "llmImage": "na.artifactory.swg-devops.com/sys-pcloud-docker-local/devops/pim/apps/vllm",
    "llmArgs": "--model ibm-granite/granite-3.2-8b-instruct --max-model-len=26208 --enable-auto-tool-choice --tool-call-parser granite",
    "llmEnv": "OMP_NUM_THREADS=16",
    "openAIBaseURL": "http://9.100.9.3:8000/v1",
    "hmcConfig": "HMC_IP=9.100.9.90, HMC_USERNAME=hmcuser, HMC_PASSWORD=lab123",
    "mcpServerURL": "http://9.100.9.3:8003/sse"
  }
  """
```
