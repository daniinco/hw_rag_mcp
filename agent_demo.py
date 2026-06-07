import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

MCP_CONFIG = {
    "qdrant": {
        "transport": "stdio",
        "command": "/opt/homebrew/bin/uvx",
        "args": ["mcp-server-qdrant"],
        "env": {
            "QDRANT_LOCAL_PATH": "./qdrant_data",
            "COLLECTION_NAME": "recipes",
            "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
            "QDRANT_SEARCH_LIMIT": "5",
        },
    }
}

DEMO_QUERIES = [
    "Найди топ-3 рецепта с клубникой",
    "Как приготовить борщ? Найди рецепты",
    "Найди рецепты десертов с шоколадом",
]


async def main():
    model = ChatOllama(model="qwen2.5:7b", temperature=0)
    client = MultiServerMCPClient(MCP_CONFIG)
    tools = await client.get_tools()
    print(f"Инструменты агента: {[t.name for t in tools]}\n")

    agent = create_react_agent(model, tools)

    for query in DEMO_QUERIES:
        print(f"----- Запрос: {query} -----------------")
        result = await agent.ainvoke({"messages": [{"role": "user", "content": query}]})
        last = result["messages"][-1]
        print(f"Ответ агента:\n{last.content}\n")


if __name__ == "__main__":
    asyncio.run(main())
