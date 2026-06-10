import chromadb
import google.generativeai as genai
from chromadb.config import Settings
import hashlib


COLLECTION_NAME = "finance_docs"


def _get_client() -> chromadb.Client:
    """Return a persistent ChromaDB client stored in ./chroma_db/"""
    return chromadb.PersistentClient(
        path="./chroma_db",
        settings=Settings(anonymized_telemetry=False),
    )


def _get_collection(client: chromadb.Client):
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed_texts(texts: list[str], api_key: str) -> list[list[float]]:
    """Embed a list of texts using Google text-embedding-004."""
    genai.configure(api_key=api_key)
    embeddings = []
    # Batch in groups of 100 (API limit)
    for i in range(0, len(texts), 100):
        batch = texts[i: i + 100]
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=batch,
            task_type="retrieval_document",
        )
        embeddings.extend(result["embedding"])
    return embeddings


def add_documents(chunks: list[dict], api_key: str) -> int:
    """
    Embed and store document chunks in ChromaDB.
    Skips chunks that already exist (by chunk_id).
    Returns number of new chunks added.
    """
    client = _get_client()
    collection = _get_collection(client)

    # Filter out already-stored chunks
    existing_ids = set(collection.get()["ids"])
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]

    if not new_chunks:
        return 0

    texts = [c["text"] for c in new_chunks]
    ids = [c["chunk_id"] for c in new_chunks]
    metadatas = [
        {"source": c["source"], "page": str(c.get("page") or "N/A")}
        for c in new_chunks
    ]

    embeddings = _embed_texts(texts, api_key)

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(new_chunks)


def query_documents(query: str, api_key: str, n_results: int = 5) -> list[dict]:
    """
    Retrieve top-k relevant chunks for a query.
    Returns list of {"text": str, "source": str, "page": str}
    """
    client = _get_client()
    collection = _get_collection(client)

    if collection.count() == 0:
        return []

    genai.configure(api_key=api_key)
    query_embedding = genai.embed_content(
        model="models/text-embedding-004",
        content=query,
        task_type="retrieval_query",
    )["embedding"]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta.get("source", "unknown"),
            "page": meta.get("page", "N/A"),
            "score": round(1 - dist, 3),  # cosine similarity
        })
    return chunks


def get_stored_sources(api_key: str = None) -> list[str]:
    """Return list of unique source filenames currently in the vector store."""
    try:
        client = _get_client()
        collection = _get_collection(client)
        metadatas = collection.get()["metadatas"]
        sources = sorted(set(m["source"] for m in metadatas if m))
        return sources
    except Exception:
        return []


def clear_store() -> None:
    """Delete all documents from the vector store."""
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass


def document_count() -> int:
    """Return total number of chunks stored."""
    try:
        client = _get_client()
        collection = _get_collection(client)
        return collection.count()
    except Exception:
        return 0
