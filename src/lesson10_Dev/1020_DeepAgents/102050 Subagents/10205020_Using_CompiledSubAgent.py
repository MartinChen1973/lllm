from deepagents import create_deep_agent, CompiledSubAgent
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from dotenv import load_dotenv, find_dotenv

# load the environment variables
load_dotenv(find_dotenv(), override=True)


# Initialize the model
model = init_chat_model("openai:gpt-4o-mini")

# Define specialized tools for the custom agent
# (Replace with your actual specialized tools)
specialized_tools = []

# Create a custom agent graph 
custom_graph = create_agent( ## ⬅️ Create a custom agent graph (See details in Langgraph documentation)
    model=model, ## ⬅️ Use a predefined model
    tools=specialized_tools, ## ⬅️ Use the specialized tools
    system_prompt="You are a specialized agent for data analysis..." ## ⬅️ Attention: this is a data analysis agent, not a research agent, not a researcher agent
)

# Use it as a custom subagent
custom_subagent = CompiledSubAgent(
    name="data-analyzer",
    description="Specialized agent for complex data analysis tasks",
    runnable=custom_graph
)

subagents = [custom_subagent] ## ⬅️ Add the custom subagent to the list of subagents

# Define main agent tools (if needed)
main_tools = []

# Define system prompt for the main agent
research_instructions = "You coordinate tasks and delegate to specialized subagents when needed."

agent = create_deep_agent(
    model="openai:gpt-4o-mini",
    tools=main_tools,
    system_prompt=research_instructions,
    subagents=subagents
)
