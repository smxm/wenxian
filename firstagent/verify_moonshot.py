from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os

load_dotenv()

chat = ChatOpenAI(
    model="deepseek-chat",
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1",
)

resp = chat.invoke([
    HumanMessage(content="请回复：Deepseek 连接成功")
])

print(resp.content)
