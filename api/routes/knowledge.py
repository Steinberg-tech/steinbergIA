from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel

from api.dependencies import get_knowledge_service
from modules.knowledge.service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class DocumentIn(BaseModel):
    title: str
    content: str
    source: str | None = None


class SearchQuery(BaseModel):
    query: str
    top_k: int = 3


@router.post("/documents", status_code=201)
async def add_document(
    doc: DocumentIn,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    doc_id = await service.add_document(doc.title, doc.content, doc.source)
    return {"doc_id": doc_id, "status": "indexed"}


@router.get("/documents")
async def list_documents(
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    return await service.list_documents()


@router.post("/search")
async def search(
    query: SearchQuery,
    service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
):
    results = await service.search(query.query, top_k=query.top_k)
    return {"query": query.query, "results": results}
