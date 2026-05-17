from modules.conversations.models import Conversation, Message
from modules.conversations.repository import ConversationRepository
from modules.conversations.schemas import MessageSchema
from shared.constants import ConversationStatus, MessageRole, Platform
from observability.logger import get_logger

_log = get_logger("conversation_service")


class ConversationService:
    def __init__(self, repo: ConversationRepository) -> None:
        self._repo = repo

    async def get_or_create(self, session_id: str, platform: Platform) -> Conversation:
        conv = await self._repo.get_by_session(session_id)
        if conv is None:
            conv = await self._repo.create(session_id, platform)
            _log.info("conversation_created", session_id=session_id, conversation_id=conv.id)
        return conv

    async def save_user_message(self, conversation_id: str, content: str) -> Message:
        return await self._repo.add_message(conversation_id, MessageRole.USER, content)

    async def save_assistant_message(
        self, conversation_id: str, content: str, agent_used: str | None = None
    ) -> Message:
        return await self._repo.add_message(
            conversation_id, MessageRole.ASSISTANT, content, agent_used
        )

    async def get_history(self, session_id: str, max_messages: int = 20) -> list[MessageSchema]:
        conv = await self._repo.get_by_session(session_id)
        if conv is None:
            return []
        messages = conv.messages[-max_messages:]
        return [MessageSchema.model_validate(m) for m in messages]

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        return await self._repo.get_by_id(conversation_id)

    async def list_by_session(self, session_id: str) -> list[Conversation]:
        return await self._repo.list_by_session(session_id)

    async def escalate(self, conversation_id: str) -> None:
        await self._repo.update_status(conversation_id, ConversationStatus.ESCALATED)
        _log.info("conversation_escalated", conversation_id=conversation_id)

    async def resolve(self, conversation_id: str) -> None:
        await self._repo.update_status(conversation_id, ConversationStatus.RESOLVED)
