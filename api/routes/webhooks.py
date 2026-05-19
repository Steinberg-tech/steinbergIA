from typing import Annotated

from fastapi import APIRouter, Depends, Request, HTTPException

from api.dependencies import get_conversation_service, get_orchestrator
from modules.conversations.service import ConversationService
from modules.ai.orchestrator import Orchestrator
from modules.ai.media.audio_transcriber import AudioTranscriber
from modules.ai.media.image_analyzer import ImageAnalyzer
from modules.integrations.webhooks.webhook_handler import WebhookHandler
from modules.integrations.digisac.digisac_client import get_digisac_client
from config.settings import settings
from observability.logger import get_logger

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
_log = get_logger("webhook_route")
_handler = WebhookHandler()
_audio_transcriber = AudioTranscriber()
_image_analyzer = ImageAnalyzer()

_AUDIO_TYPES = {"audio", "ptt", "voice"}
_IMAGE_TYPES = {"image", "photo"}
_DOCUMENT_TYPES = {"document"}


@router.post("/digisac")
async def receive_digisac(
    request: Request,
    orchestrator: Annotated[Orchestrator, Depends(get_orchestrator)],
    conv_service: Annotated[ConversationService, Depends(get_conversation_service)],
):
    """
    Dedicated Digisac webhook. Handles text, audio, image, and document messages.
    Audio is transcribed via Whisper; images/documents are analyzed via GPT-4o Vision.
    """
    payload = await request.json()
    _log.info("digisac_webhook_received", raw_payload=payload)

    # DEBUG — imprime o payload bruto no terminal para facilitar diagnóstico
    if settings.debug:
        import json as _json
        print("\n===== DIGISAC RAW PAYLOAD =====")
        print(_json.dumps(payload, indent=2, ensure_ascii=False))
        print("================================\n")

    try:
        parsed = _handler.parse("digisac", payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc

    if not parsed:
        return {"status": "ignored", "reason": "event filtered by handler"}

    # DEBUG — imprime o resultado do parse
    if settings.debug:
        print(f"[DEBUG] parsed: event_type={payload.get('event', payload.get('type', '?'))} | message_type={parsed.get('message_type')} | session_id={parsed.get('session_id')} | phone={parsed.get('phone')} | file_id={parsed.get('file_id')} | media_url={parsed.get('media_url')}")

    session_id = parsed.get("session_id", "")
    contact_id = parsed.get("contact_id", "")
    message_id = parsed.get("message_id", "")
    phone = parsed.get("phone", "")
    message_type = parsed.get("message_type", "text")
    message = parsed.get("message", "")
    file_id = parsed.get("file_id")
    media_url = parsed.get("media_url")
    mime_type = parsed.get("mime_type", "")

    allowed = settings.digisac_allowed_senders_list
    if allowed:
        if not phone and contact_id:
            phone = await get_digisac_client().get_contact_phone(contact_id)
        if phone not in allowed:
            _log.info("digisac_sender_ignored", phone=phone)
            return {"status": "ignored", "reason": "sender not in allowlist"}

    # Resolve media to text when needed
    if message_type in _AUDIO_TYPES:
        digisac = get_digisac_client()
        try:
            # File URL may not be in the webhook payload (isDownloading=true).
            # Wait until Digisac finishes downloading, then fetch binary via GET /files/{messageId}.
            if not file_id and not media_url and message_id:
                await digisac.get_message(message_id)  # waits until isDownloading=False
                file_id = message_id
                mime_type = "audio/ogg"
                if settings.debug:
                    print(f"[DEBUG] using message_id as file_id: {file_id}")

            audio_bytes = await digisac.download_media(file_id=file_id, media_url=media_url)
            message = await _audio_transcriber.transcribe(audio_bytes, mime_type=mime_type)
            _log.info("digisac_audio_transcribed", session_id=session_id, chars=len(message))
        except Exception as exc:
            _log.error("digisac_audio_error", session_id=session_id, error=str(exc))
            message = "[Áudio recebido — não foi possível transcrever no momento]"

    elif message_type in _IMAGE_TYPES | _DOCUMENT_TYPES and (file_id or media_url):
        digisac = get_digisac_client()
        try:
            image_bytes = await digisac.download_media(file_id=file_id, media_url=media_url)
            description = await _image_analyzer.analyze(image_bytes, mime_type=mime_type)
            message = f"[Imagem enviada pelo cliente]\n{description}"
            _log.info("digisac_image_analyzed", session_id=session_id, chars=len(message))
        except Exception as exc:
            _log.error("digisac_image_error", session_id=session_id, error=str(exc))
            message = "[Imagem recebida — não foi possível analisar no momento]"

    if not message:
        _log.info("digisac_empty_message_ignored", message_type=message_type, session_id=session_id)
        return {"status": "ignored", "reason": "empty message"}

    _log.info("digisac_processing", session_id=session_id, message_type=message_type, message_len=len(message))

    conversation = await conv_service.get_or_create(session_id, "digisac")
    await conv_service.save_user_message(conversation.id, message)

    try:
        final_text, agent_response = await orchestrator.process(message, session_id)
    except Exception as exc:
        _log.error("digisac_pipeline_error", session_id=session_id, error=str(exc))
        return {"status": "error", "reason": "pipeline failure"}

    await conv_service.save_assistant_message(conversation.id, final_text)

    digisac = get_digisac_client()
    try:
        if settings.digisac_token:
            await digisac.send_text(contact_id=contact_id, text=final_text)
        else:
            await digisac.send_text_mock(contact_id=contact_id, text=final_text)
    except Exception as exc:
        _log.error("digisac_send_error", contact_id=contact_id, error=str(exc))

    return {"status": "processed", "session_id": session_id, "message_type": message_type}


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
