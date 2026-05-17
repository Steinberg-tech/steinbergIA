from modules.conversations.schemas import MessageSchema
from modules.conversations.service import ConversationService
from shared.constants import MessageRole


class HistoryMemory:
    """Retrieves the recent conversation history for a session."""

    def __init__(self, conversation_service: ConversationService, max_messages: int = 20) -> None:
        self._service = conversation_service
        self._max = max_messages

    async def get(self, session_id: str) -> list[dict]:
        messages = await self._service.get_history(session_id, self._max)
        return [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]

    async def get_formatted(self, session_id: str) -> str:
        messages = await self.get(session_id)
        if not messages:
            return "Sem histórico anterior."
        lines = []
        for msg in messages:
            prefix = "Cliente" if msg["role"] == MessageRole.USER else "Assistente"
            lines.append(f"{prefix}: {msg['content']}")
        return "\n".join(lines)
