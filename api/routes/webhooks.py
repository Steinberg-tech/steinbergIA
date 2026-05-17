from typing import Annotated

from fastapi import APIRouter, Depends, Request, HTTPException

from api.dependencies import get_conversation_service, get_orchestrator
from modules.conversations.service import ConversationService
from modules.ai.orchestrator import Orchestrator
from modules.integrations.webhooks.webhook_handler import WebhookHandler
from modules.integrations.digisac.digisac_client import DigisacClient, get_digisac_client
from config.settings import settings
from observability.logger import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
_log = get_logger("webhook_route")
_handler = WebhookHandler()


@router.post("/digisac")
async def receive_digisac(
    request: Request,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    conv_service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    """
    Dedicated Digisac webhook. Filters by allowed senders, runs the AI pipeline,
    and sends the response back via the Digisac API.
    """
    payload = await request.json()
    _log.info("digisac_webhook_received", raw_payload=payload)

    try:
        parsed = _handler.parse("digisac", payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc

    session_id = parsed.get("session_id", "")
    message = parsed.get("message", "")
    contact_id = parsed.get("contact_id", "")
    message_type = parsed.get("message_type", "text")

    # Only process messages from allowed senders
    if session_id not in settings.digisac_allowed_senders_list:
        _log.info("digisac_sender_ignored", phone=session_id)
        return {"status": "ignored", "reason": "sender not in allowlist"}

    if not message:
        if message_type != "text":
            _log.info("digisac_non_text_ignored", type=message_type, phone=session_id)
        return {"status": "ignored", "reason": "empty or non-text message"}

    _log.info("digisac_processing", phone=session_id, message_len=len(message))

    conversation = await conv_service.get_or_create(session_id, "digisac")
    await conv_service.save_user_message(conversation.id, message)

    try:
        final_text, agent_response = await orchestrator.process(message, session_id)
    except Exception as exc:
        _log.error("digisac_pipeline_error", phone=session_id, error=str(exc))
        return {"status": "error", "reason": "pipeline failure"}

    await conv_service.save_assistant_message(conversation.id, final_text)

    # Send response back through Digisac
    digisac = get_digisac_client()
    try:
        if settings.digisac_token:
            await digisac.send_text(contact_id=contact_id, text=final_text)
        else:
            await digisac.send_text_mock(contact_id=contact_id, text=final_text)
    except Exception as exc:
        _log.error("digisac_send_error", contact_id=contact_id, error=str(exc))

    return {"status": "processed", "session_id": session_id}


@router.post("/{platform}")
async def receive_webhook(
    platform: str,
    request: Request,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    conv_service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    """
    Generic webhook for other platforms (WhatsApp Cloud API, etc.).
    Normalizes the payload and runs through the same pipeline as /chat.
    """
    payload = await request.json()
    _log.info("webhook_received", platform=platform)

    try:
        parsed = _handler.parse(platform, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc

    session_id = parsed.get("session_id")
    message = parsed.get("message")

    if not session_id or not message:
        return {"status": "ignored", "reason": "empty message or session"}

    conversation = await conv_service.get_or_create(session_id, platform)
    await conv_service.save_user_message(conversation.id, message)

    final_text, agent_response = await orchestrator.process(message, session_id)
    await conv_service.save_assistant_message(conversation.id, final_text)

    return {"status": "processed", "session_id": session_id, "response": final_text}
