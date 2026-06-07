import asyncio, json, re
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_CMD = "/opt/homebrew/bin/uvx"
MCP_ARGS = ["mcp-server-qdrant"]
MCP_ENV = {
    "QDRANT_LOCAL_PATH": "./qdrant_data",
    "COLLECTION_NAME": "recipes",
    "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "QDRANT_SEARCH_LIMIT": "5",
}

QUERIES = [
    ("Рецепт борща", 3),
    ("Как приготовить тесто для пиццы", 3),
    ("Десерт из шоколада", 3),
]


def parse_entries(result):
    raw = json.loads(result.content[0].text)
    entries = []
    for item in raw[1:]:
        content_m = re.search(r"<content>(.*?)</content>", item, re.DOTALL)
        meta_m = re.search(r"<metadata>(.*?)</metadata>", item, re.DOTALL)
        content = content_m.group(1).strip() if content_m else item
        try:
            meta = json.loads(meta_m.group(1)) if meta_m else {}
        except Exception:
            meta = {}
        entries.append({"content": content, "metadata": meta})
    return entries


async def main():
    server_params = StdioServerParameters(command=MCP_CMD, args=MCP_ARGS, env=MCP_ENV)

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("Инструменты:", [t.name for t in tools.tools])
            print()

            for query, k in QUERIES:
                print(f"Query: {query}")
                print(f"Top-k: {k}")
                result = await session.call_tool("qdrant-find", {"query": query})
                entries = parse_entries(result)

                for i, e in enumerate(entries[:k], 1):
                    meta = e["metadata"]
                    doc_id = meta.get("document_id", "—")
                    chunk_id = meta.get("chunk_id", "—")
                    source = meta.get("source", "—")
                    text = e["content"][:120]
                    print(f"{i}. document_id={doc_id}, chunk_id={chunk_id}")
                    print(f"   source={source}")
                    print(f"   text={text}...")
                print()


if __name__ == "__main__":
    asyncio.run(main())
