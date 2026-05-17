from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.knowledge.models import Document
from shared.utils import generate_id, now_utc


class KnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, title: str, content: str, source: str | None = None, doc_type: str = "faq") -> Document:
        doc = Document(
            id=generate_id(),
            title=title,
            content=content,
            source=source,
            doc_type=doc_type,
            created_at=now_utc(),
        )
        self._session.add(doc)
        await self._session.flush()
        return doc

    async def get(self, doc_id: str) -> Document | None:
        result = await self._session.execute(select(Document).where(Document.id == doc_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Document]:
        result = await self._session.execute(select(Document).order_by(Document.created_at.desc()))
        return list(result.scalars().all())
