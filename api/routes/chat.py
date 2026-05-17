from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import get_conversation_service, get_orchestrator
from modules.conversations.schemas import ChatRequest, ChatResponse
from modules.conversations.service import ConversationService
from modules.ai.orchestrator import Orchestrator
from observability.logger import get_logger
from shared.constants import Platform

router = APIRouter(prefix="/chat", tags=["chat"])
_log = get_logger("chat_route")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    conv_service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    """
    Main SAC endpoint. Receives a message from any platform channel,
    runs the full AI pipeline, and returns the agent response.
    """
    _log.info(
        "chat_request",
        session_id=request.session_id,
        platform=request.platform,
        message_len=len(request.message),
    )

    conversation = await conv_service.get_or_create(request.session_id, request.platform)
    await conv_service.save_user_message(conversation.id, request.message)

    try:
        final_text, agent_response = await orchestrator.process(
            user_message=request.message,
            session_id=request.session_id,
        )
    except Exception as exc:
        _log.error("chat_pipeline_error", session_id=request.session_id, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno no processamento da mensagem.",
        ) from exc

    await conv_service.save_assistant_message(
        conversation.id,
        final_text,
        agent_used=agent_response.metadata.get("agent") if agent_response.metadata else None,
    )

    if agent_response.escalate:
        await conv_service.escalate(conversation.id)

    return ChatResponse(
        message=final_text,
        conversation_id=conversation.id,
        session_id=request.session_id,
        agent_used=None,
        escalated=agent_response.escalate,
        metadata=agent_response.metadata,
    )
