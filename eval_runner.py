import asyncio, json, re
import pandas as pd
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MCP_ENV = {
    "QDRANT_LOCAL_PATH": "./qdrant_data",
    "COLLECTION_NAME": "recipes",
    "EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "QDRANT_SEARCH_LIMIT": "5",
}


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


async def run_eval():
    df = pd.read_csv("eval_queries.csv")
    server_params = StdioServerParameters(
        command="/opt/homebrew/bin/uvx", args=["mcp-server-qdrant"], env=MCP_ENV
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            rows = []
            for _, row in df.iterrows():
                query = str(row["query"])
                expected = str(row.get("expected_source", ""))
                print(f"[{row['no']}] {query}")
                try:
                    result = await session.call_tool("qdrant-find", {"query": query})
                    entries = parse_entries(result)

                    first = entries[0] if entries else {}
                    meta = first.get("metadata", {})
                    first_chunk_id = meta.get("chunk_id", meta.get("document_id", "—"))
                    first_csv_row = meta.get("csv_row", "—")
                    first_title = meta.get("title", "—")
                    text_preview = first.get("content", "")[:80]

                    # in_top3: "?" для вопросов вне корпуса, иначе проверяем
                    # есть ли хоть один результат (ручная оценка всё равно нужна)
                    if expected == "нет ответа":
                        in_top3 = "?"
                    else:
                        in_top3 = "да" if entries else "нет"

                    print(f"  → {first_chunk_id} (csv_row={first_csv_row}, title={first_title[:40]})")
                except Exception as e:
                    first_chunk_id, first_csv_row, first_title = "ERROR", "—", "—"
                    text_preview, in_top3 = str(e)[:60], "нет"
                    print(f"  ошибка: {e}")

                rows.append({
                    **row.to_dict(),
                    "first_result": first_chunk_id,
                    "first_csv_row": first_csv_row,
                    "first_title": first_title,
                    "text_preview": text_preview,
                    "in_top3": in_top3,
                    "manual_judgement": row.get("manual_judgement", ""),
                    "comment": row.get("comment", ""),
                })

    out = pd.DataFrame(rows)
    out.to_csv("eval_queries.csv", index=False)
    print("\nРезультаты сохранены в eval_queries.csv")
    print(out[["no", "query", "first_result", "first_csv_row", "first_title", "in_top3"]].to_string(index=False))


if __name__ == "__main__":
    asyncio.run(run_eval())
