from src.config import settings
from src.stores.documents import DocumentStore, Chunk
from src.stores.vectors import VectorStore
from src.stores.graph import GraphStore


def test_round_trip():
    # Setup all three stores
    docs = DocumentStore(settings.sqlite_path, settings.data_dir / "processed")
    vecs = VectorStore(settings.chroma_path, settings.embedding_model, settings.ollama_host)
    graph = GraphStore(settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password)

    chunk = Chunk(
        chunk_id="test_chunk_001",
        text="C/Capt Sana Okafor is the Knowledge Management Officer at Det 999.",
        metadata={"doc_type": "test", "title": "Smoke test", "date": "2025-11-01"},
    )

    # Put into all three
    docs.put(chunk)
    vecs.index(chunk.chunk_id, chunk.text, chunk.metadata)
    graph.upsert_entity("Sana Okafor", "Person", [chunk.chunk_id])
    graph.upsert_entity("Det 999", "Organization", [chunk.chunk_id])
    graph.upsert_relationship("Sana Okafor", "Det 999", "MEMBER_OF", chunk.chunk_id)

    # Get back out of all three
    retrieved = docs.get(chunk.chunk_id)
    assert retrieved.text == chunk.text

    hits = vecs.search("who is the KM officer", k=3)
    assert any(h["chunk_id"] == chunk.chunk_id for h in hits)

    entity = graph.find_entity("Sana Okafor")
    assert entity is not None
    assert chunk.chunk_id in entity["chunk_ids"]

    # Cleanup
    docs.delete(chunk.chunk_id)
    vecs.delete(chunk.chunk_id)
    graph.clear()
    graph.close()

    print("All three stores round-trip cleanly. Step 2 done.")


if __name__ == "__main__":
    test_round_trip()