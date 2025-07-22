# AI agent to manage Power Infra using MCP Server built for HMC 

# Setup
1. Clone this repository `git clone https://github.com/IBM/project-pim` and get into `examples/hmc-agent/app`
2. Create a virtual environment `uv venv` and activate it `source .venv/bin/activate`
3. Install the dependencies `uv sync`
Note: Make sure npm/nodejs dependency is installed to use `uv` functionalities 

# Usage

Run ollama in local wherever you are going to run your agent application

**Set env for server**
```
# HMC details
export HMC_IP=""
export HMC_USERNAME=""
export HMC_PASSWORD=""
```
**Run the server**
```
uv run server.py
```
Since this is an SSE transport server, which would be running on `http://127.0.0.1:8000` by default.
Agent can use this URL to bind the tools and do agent tools invocation

**Set env for agent**
```
# Model to use
export OLLAMA_MODEL="ollama_chat/granite3.2:8b"
```
**Run the agent**
```
uv run agent.py

ex:
$ (infra-agents) dharaneesh@Mac infra-agents % uv run agent.py
$
$ You: get me the HMC version
$ 
$ Agent: The HMC (Hardware Management Console) version is 10.0.1021. This includes a major version of 10, a minor version of 0, and a service pack version of 1021.
$
```

Sample prompts:
```
- get me the HMC version
- get me the systems managed by HMC
- get me the compute usage of system 'C340F2U01-ZZ'
- get me the logical partitions created under system 'C340F1U07-ICP-Dedicated'
- get me the stats of partition 'hamzy-bastion-f36de29b-00015f1f' under system 'C340F1U07-ICP-Dedicated'
```

Optionally you can run the inspector `uv run mcp dev server.py` to interact with the tools directly without LLM