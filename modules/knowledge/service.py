from modules.knowledge.embeddings import EmbeddingGenerator
from modules.knowledge.repository import KnowledgeRepository
from modules.knowledge.vector_store import VectorStore
from observability.logger import get_logger
from shared.exceptions import KnowledgeBaseError

_log = get_logger("knowledge_service")


class KnowledgeService:
    def __init__(
        self,
        repo: KnowledgeRepository,
        vector_store: VectorStore,
        embeddings: EmbeddingGenerator,
    ) -> None:
        self._repo = repo
        self._store = vector_store
        self._embeddings = embeddings

    async def add_document(self, title: str, content: str, source: str | None = None) -> str:
        doc = await self._repo.save(title, content, source)
        embedding = await self._embeddings.embed(content)
        await self._store.add(
            doc_id=doc.id,
            content=content,
            embedding=embedding,
            metadata={"title": title, "source": source or ""},
        )
        _log.info("document_indexed", doc_id=doc.id, title=title)
        return doc.id

    async def search(self, query: str, top_k: int = 3) -> list[dict]:
        try:
            embedding = await self._embeddings.embed(query)
            return await self._store.search(embedding, top_k=top_k)
        except Exception as exc:
            _log.error("knowledge_search_error", error=str(exc))
            raise KnowledgeBaseError(f"Search failed: {exc}") from exc

    async def list_documents(self) -> list[dict]:
        docs = await self._repo.list_all()
        return [{"id": d.id, "title": d.title, "source": d.source} for d in docs]
