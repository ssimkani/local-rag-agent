from pathlib import Path
import chromadb
from langchain_ollama import OllamaEmbeddings


class VectorStore:
    def __init__(self, persist_path: Path, embedding_model: str, ollama_host: str):
        self.client = chromadb.PersistentClient(path=str(persist_path))
        self.collection = self.client.get_or_create_collection("chunks")
        self.embedder = OllamaEmbeddings(model=embedding_model, base_url=ollama_host)

    def index(self, chunk_id: str, text: str, metadata: dict) -> None:
        vector = self.embedder.embed_query(text)
        # Chroma metadata must be flat scalars; flatten if needed
        flat_md = {k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))}
        self.collection.upsert(
            ids=[chunk_id],
            embeddings=[vector],
            documents=[text],
            metadatas=[flat_md],
        )

    def search(self, query: str, k: int = 5, filters: dict | None = None) -> list[dict]:
        vector = self.embedder.embed_query(query)
        results = self.collection.query(
            query_embeddings=[vector],
            n_results=k,
            where=filters or None,
        )
        return [
            {"chunk_id": cid, "score": dist, "metadata": md}
            for cid, dist, md in zip(
                results["ids"][0], results["distances"][0], results["metadatas"][0]
            )
        ]

    def delete(self, chunk_id: str) -> None:
        self.collection.delete(ids=[chunk_id])