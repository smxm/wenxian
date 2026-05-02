from dataclasses import dataclass

from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from langchain.agents import create_agent
from langchain_deepseek import ChatDeepSeek
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents.structured_output import ToolStrategy

system_prompt = """You are an expert weather forecaster, who speaks in puns.

You have access to two tools:

- get_weather_for_location: use this to get the weather for a specific location
- get_user_location: use this to get the user's location

If a user asks for the weather, you should first try to get the user's location using get_user_location. If that fails, you should ask the user for their location.

"""
# Define context schema
@dataclass
class Context:
    """Context for the agent"""
    user_id: str

# Define tools
@tool
def get_weather_for_location(city: str) -> str:
    """Get the weather for a specific location"""
    return f"The weather in {city} is sunny."

@tool
def get_user_location(user_id: str) -> str:
    """Get the user's location"""
    return "Beijing" if user_id == "1" else "Shanghai"

# Configure model
model = ChatDeepSeek(
    model="deepseek-chat",
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    max_retries=1,
    timeout=10,
    base_url="https://api.deepseek.com/v1",
)

# Define response format
@dataclass
class ResponseFormat:
    """Response format for the agent"""
    # A punny response
    punny_response: str
    # Any intersting information about the weather if available
    wether_conditions: str | None = None

# Set up memory
checkpointer = InMemorySaver()

# Create agent
agent = create_agent(
    model=model,
    system_prompt=system_prompt,
    tools=[get_weather_for_location, get_user_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=checkpointer
)

# Run agent
# 'thread_id' is used to identify a conversation

config = {"configurable": {"thread_id": "1"}}

response = agent.invoke(
    {"messages": [{"role": "user", "content": "What is the weather like?"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])

response = agent.invoke(
    {"messages": [{"role": "user", "content": "Thank you!"}]},
    config=config,
    context=Context(user_id="1")
)

print(response['structured_response'])

