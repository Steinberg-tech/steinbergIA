from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_conversation_service
from modules.conversations.schemas import ConversationSchema
from modules.conversations.service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/{session_id}", response_model=list[ConversationSchema])
async def list_conversations(
    session_id: str,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    conversations = await service.list_by_session(session_id)
    return [ConversationSchema.model_validate(c) for c in conversations]


@router.get("/{session_id}/history")
async def get_history(
    session_id: str,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    history = await service.get_history(session_id)
    return {"session_id": session_id, "messages": [m.model_dump() for m in history]}


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def resolve_conversation(
    conversation_id: str,
    service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    conv = await service.get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada.")
    await service.resolve(conversation_id)
