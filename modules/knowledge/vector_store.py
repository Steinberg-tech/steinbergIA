import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings
from observability.logger import get_logger
from shared.utils import generate_id

_log = get_logger("vector_store")


class VectorStore:
    """ChromaDB-backed vector store for semantic search over knowledge documents."""

    def __init__(self) -> None:
        self._client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection_name = settings.chroma_collection

    def _collection(self):
        return self._client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add(self, doc_id: str, content: str, embedding: list[float], metadata: dict | None = None) -> None:
        col = self._collection()
        col.upsert(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content],
            metadatas=[metadata or {}],
        )
        _log.info("vector_store_added", doc_id=doc_id)

    async def search(self, embedding: list[float], top_k: int = 3) -> list[dict]:
        col = self._collection()
        results = col.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        return [
            {"content": doc, "metadata": meta, "score": 1 - dist}
            for doc, meta, dist in zip(docs, metas, dists)
        ]

    async def delete(self, doc_id: str) -> None:
        self._collection().delete(ids=[doc_id])
