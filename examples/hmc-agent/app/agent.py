from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
import asyncio
import os

class MCPClient:
    def __init__(self, model, openai_base_url, mcp_server_url):
        self.model = ChatOpenAI(
            model=model,
            openai_api_base=openai_base_url,
            openai_api_key="xyz",
            temperature=0.6,
            streaming=False  # Disable streaming for better compatibility
        )
        self.mcp_client = MultiServerMCPClient(
            {
                "ibmhmcserver": {
                    "url": mcp_server_url,
                    "transport": "sse",
                }
            }
        )
    
        self.SYSTEM_PROMPT = """You are an AI assistant that helps users to list the systems managed by HMC, list the partitions under a specific system and get the version of HMC via available tools.
        
        When listing partitions under provided system, call list_partitions tool with an arg as system name and it return a list containing partition informations.
        
        When listing systems, call list_systems tool and it returns a list containing system names.
        
        When getting HMC version, call get_hmc_version tool and it returns a string containing the version information. 
        """

    async def initialize_agent(self):
        self.tools = await self.mcp_client.get_tools()
        self.agent = create_react_agent(
                        model=self.model,
                        tools=self.tools)
    
    async def process_message(self, user_input):
        input = {"messages": [{"role": "user", "content": self.SYSTEM_PROMPT + "\n" + user_input}]}
        response = await self.agent.ainvoke(input)
        return response["messages"][-1].content

    async def interactive_chat(self):
        while True:
            user_input = "get me the HMC version"
            if user_input.lower() == "exit":
                print("Ending chat session...")
                break
            
            response = await self.process_message(user_input)
            print("\nAgent:", response)

async def main():
    try:
        model = os.getenv("OLLAMA_MODEL")
        openai_base_url = os.getenv("OPEN_AI_BASE_URL")
        mcp_server_url = os.getenv("MCP_SERVER_URL")
        client = MCPClient(model, openai_base_url, mcp_server_url)
        print("\nInitializing agent...")
        await client.initialize_agent()
        
        print("\nStarting interactive chat...")
        await client.interactive_chat()
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
