# Demonstrates TodoListMiddleware for task planning and tracking in agents

import asyncio

from dotenv import load_dotenv, find_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware.todo import TodoListMiddleware
from langchain_core.messages import HumanMessage

# Load environment variables from .env file
load_dotenv(find_dotenv(), override=True)


agent = create_agent(
    model="openai:gpt-4o-mini",
    middleware=[TodoListMiddleware()],
)

# Agent now has access to write_todos tool and todo state tracking


async def main() -> None:
    result = await agent.ainvoke({
        "messages": [HumanMessage("Help me refactor my codebase")],
    })
    print("Final response:", result.get("messages", [])[-1].content if result.get("messages") else "N/A")
    print("\nTodos (task planning and status tracking):")
    for todo in result.get("todos", []):
        print(f"  - {todo}")


if __name__ == "__main__":
    asyncio.run(main())
