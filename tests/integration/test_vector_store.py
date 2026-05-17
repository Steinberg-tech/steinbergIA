"""
Integration tests for ChromaDB vector store.
Requires ChromaDB running at CHROMA_HOST:CHROMA_PORT.
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("CHROMA_HOST"),
    reason="ChromaDB not configured",
)


@pytest.mark.asyncio
async def test_vector_store_add_and_search():
    from modules.knowledge.vector_store import VectorStore

    store = VectorStore()
    embedding = [0.1] * 1536

    await store.add(
        doc_id="test-doc-001",
        content="Prazo de entrega é de 5 dias úteis.",
        embedding=embedding,
        metadata={"title": "FAQ Prazo"},
    )

    results = await store.search(embedding, top_k=1)
    assert len(results) >= 1
    assert results[0]["content"]

    await store.delete("test-doc-001")
