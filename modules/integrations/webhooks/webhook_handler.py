from observability.logger import get_logger

_log = get_logger("webhook_handler")


class WebhookHandler:
    """Normalizes incoming webhook payloads from different platforms into a standard format."""

    def parse(self, platform: str, payload: dict) -> dict:
        parser = getattr(self, f"_parse_{platform}", self._parse_generic)
        return parser(payload)

    def _parse_whatsapp(self, payload: dict) -> dict:
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [{}])
        msg = messages[0] if messages else {}
        return {
            "session_id": msg.get("from", ""),
            "message": msg.get("text", {}).get("body", ""),
            "platform": "whatsapp",
            "raw": payload,
        }

    def _parse_digisac(self, payload: dict) -> dict:
        # Digisac webhook payload uses "event" (not "type") at root level.
        # Text messages have data.type == "chat" and text in data.text.
        # Audio/image messages carry file info in data.file or data.mediaUrl.
        # Phone number is not included — contactId UUID is used as session identifier.
        data = payload.get("data", payload)
        event_type = payload.get("event", payload.get("type", ""))

        if event_type and event_type not in ("message", "message.created"):
            _log.info("digisac_event_ignored", type=event_type)
            return {}

        if data.get("isFromMe", False) or data.get("isFromBot", False):
            return {}

        contact_id = data.get("contactId") or data.get("fromId", "")
        # Phone number comes in data.contact.number or data.number
        contact = data.get("contact") or {}
        phone = contact.get("number") or data.get("number") or data.get("phone", "")
        message_type = data.get("type", "chat")

        text = ""
        file_id = None
        media_url = None
        mime_type = None

        if message_type in ("text", "chat"):
            text = data.get("text", "")
        elif message_type in ("audio", "ptt", "voice"):
            file_info = data.get("file") or {}
            file_id = file_info.get("id") or data.get("fileId")
            media_url = file_info.get("url") or data.get("mediaUrl")
            mime_type = file_info.get("mimeType", "audio/ogg")
        elif message_type in ("image", "photo"):
            file_info = data.get("file") or {}
            file_id = file_info.get("id") or data.get("fileId")
            media_url = file_info.get("url") or data.get("mediaUrl")
            mime_type = file_info.get("mimeType", "image/jpeg")
        elif message_type == "document":
            file_info = data.get("file") or {}
            file_id = file_info.get("id") or data.get("fileId")
            media_url = file_info.get("url") or data.get("mediaUrl")
            mime_type = file_info.get("mimeType", "application/pdf")

        return {
            "session_id": contact_id,
            "contact_id": contact_id,
            "phone": phone,
            "service_id": data.get("serviceId", ""),
            "message": text,
            "message_type": message_type,
            "file_id": file_id,
            "media_url": media_url,
            "mime_type": mime_type,
            "platform": "digisac",
            "raw": payload,
        }

    def _parse_generic(self, payload: dict) -> dict:
        return {
            "session_id": payload.get("session_id", payload.get("from", "")),
            "message": payload.get("message", payload.get("text", "")),
            "platform": payload.get("platform", "api"),
            "raw": payload,
        }
