import os
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

load_dotenv(override=True)

def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}天气晴朗"

model = ChatOpenAI(
    model="moonshot-v1-8k",
    api_key=os.getenv("MOONSHOT_API_KEY"),
    base_url=os.getenv("MOONSHOT_BASE_URL"),
)

agent = create_agent(
    model=model,
    tools=[get_weather],
    system_prompt="你是一个天气助手，可以回答用户关于天气的问题"
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "北京天气怎么样？"}]}
)

print(result)