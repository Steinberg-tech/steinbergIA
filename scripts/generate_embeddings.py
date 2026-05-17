"""
Regenerates embeddings for all documents already stored in the database.
Useful after changing embedding models.
Run: python scripts/generate_embeddings.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config.settings import settings
from modules.knowledge.embeddings import EmbeddingGenerator
from modules.knowledge.repository import KnowledgeRepository
from modules.knowledge.vector_store import VectorStore


async def regenerate():
    engine = create_async_engine(settings.database_url)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    gen = EmbeddingGenerator()
    store = VectorStore()

    async with factory() as session:
        repo = KnowledgeRepository(session)
        docs = await repo.list_all()
        print(f"Found {len(docs)} documents. Regenerating embeddings...")
        for doc in docs:
            embedding = await gen.embed(doc.content)
            await store.add(
                doc_id=doc.id,
                content=doc.content,
                embedding=embedding,
                metadata={"title": doc.title, "source": doc.source or ""},
            )
            print(f"  Re-embedded: {doc.title}")

    await engine.dispose()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(regenerate())
