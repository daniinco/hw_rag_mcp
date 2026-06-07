import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from fastembed import TextEmbedding

COLLECTION = "recipes"
CSV_PATH = "povarenok.csv"
QDRANT_PATH = "./qdrant_data"
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# mcp-server-qdrant формирует имя вектора как fast-{model_last_part_lower}
VECTOR_NAME = "fast-" + MODEL.split("/")[-1].lower()
CHUNK_SIZE = 400
CHUNK_OVERLAP = 50
LIMIT = 500  # сколько рецептов брать из 10k для демо (None = все)


def make_chunks(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i+size])
        chunks.append(chunk)
        i += size - overlap
    return chunks


def main():
    df = pd.read_csv(CSV_PATH)
    if LIMIT:
        df = df.head(LIMIT)
    df = df.dropna(subset=["text"])

    print(f"Загружено рецептов: {len(df)}")

    embedder = TextEmbedding(MODEL)
    client = QdrantClient(path=QDRANT_PATH)

    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(
        COLLECTION,
        vectors_config={VECTOR_NAME: VectorParams(size=384, distance=Distance.COSINE)},
    )

    points = []
    uid = 0
    for csv_idx, row in df.iterrows():
        name = str(row["name"])
        ingredients = str(row.get("ingredients", ""))
        text = str(row["text"])
        csv_row = csv_idx + 2  # 1-based, с учётом заголовка
        full_text = f"{name}\nИнгредиенты: {ingredients}\n{text}"
        chunks = make_chunks(full_text)
        for ci, chunk in enumerate(chunks):
            points.append({
                "id": uid,
                "text": chunk,
                "metadata": {
                    "document_id": str(csv_row),
                    "chunk_id": str(ci),
                    "source": f"povarenok.csv:{csv_row}",
                    "title": name,
                    "csv_row": csv_row,
                    "chunk_index": ci,
                    "total_chunks": len(chunks),
                }
            })
            uid += 1

    print(f"Всего фрагментов: {len(points)}")

    texts = [p["text"] for p in points]
    embeddings = list(embedder.embed(texts))

    batch_size = 256
    for i in range(0, len(points), batch_size):
        batch = points[i:i+batch_size]
        embs = embeddings[i:i+batch_size]
        structs = [
            PointStruct(
                id=p["id"],
                vector={VECTOR_NAME: embs[j].tolist()},
                payload={
                    "document": p["text"],
                    "metadata": p["metadata"],
                },
            )
            for j, p in enumerate(batch)
        ]
        client.upsert(COLLECTION, structs)
        print(f"  загружено {min(i+batch_size, len(points))}/{len(points)}")

    print("Индексация завершена.")
    info = client.get_collection(COLLECTION)
    print(f"Точек в коллекции: {info.points_count}")


if __name__ == "__main__":
    main()
