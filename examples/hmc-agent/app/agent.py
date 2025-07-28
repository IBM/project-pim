from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import asyncio
import streamlit as st

st.set_page_config(page_title="Infra agent Chat", page_icon="🤖", layout="centered")
st.title("HMC Agent Chat  💬")
st.markdown(
    """
    <p style='text-align: center; font-size: 20px;'>
    Interact with the HMC apis to get answers for the queries
    </p>
    """,
    unsafe_allow_html=True
)

if "history" not in st.session_state:
    st.session_state.history = []


class MCPClient:
    def __init__(self, mcp_server_url="http://127.0.0.1:8000/sse"):
        self.model = ChatOpenAI(
            model="ibm-granite/granite-3.2-8b-instruct",
            openai_api_base="",
            openai_api_key="",
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
        
        When listing partitions under provided system, call list_partitions tool with an arg as system name and it return a list containing partition information.
        
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
        """Streamlit-based interactive chat interface."""

        user_input = st.chat_input("What HMC task would you like help with?")
        if user_input:
             # Show spinner while processing
            st.session_state.history.append(("User", user_input))
            with st.spinner("⚙️ Working on your HMC request..."):
                response = await self.process_message(user_input)
                st.session_state.history.append(("Agent", response))
            
        self.populate_chat_history()
    
    def populate_chat_history(self):
        for sender, message in st.session_state.history:
            if sender == "User":
                st.chat_message("user").write(message)
            else:
                st.chat_message("assistant").write(message)

async def main():
    try:
        if "mcp_client" not in st.session_state:
            client = MCPClient()
            print("\nInitializing agent...")
            await client.initialize_agent()

            st.session_state.mcp_client = client
            print("\nStarting interactive chat...")
            await client.interactive_chat()
        else:
            await st.session_state.mcp_client.interactive_chat()        
    except Exception as e:
        print(f"\nUnexpected error: {type(e).__name__} - {str(e)}")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 
