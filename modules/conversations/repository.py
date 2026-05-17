from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.conversations.models import Conversation, Message
from shared.constants import ConversationStatus, MessageRole
from shared.utils import generate_id, now_utc


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_session(self, session_id: str) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .where(Conversation.status == ConversationStatus.ACTIVE)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, conversation_id: str) -> Conversation | None:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def create(self, session_id: str, platform: str) -> Conversation:
        conv = Conversation(id=generate_id(), session_id=session_id, platform=platform)
        self._session.add(conv)
        await self._session.flush()
        return conv

    async def add_message(
        self,
        conversation_id: str,
        role: MessageRole,
        content: str,
        agent_used: str | None = None,
    ) -> Message:
        msg = Message(
            id=generate_id(),
            conversation_id=conversation_id,
            role=role,
            content=content,
            agent_used=agent_used,
            timestamp=now_utc(),
        )
        self._session.add(msg)
        await self._session.flush()
        return msg

    async def update_status(self, conversation_id: str, status: ConversationStatus) -> None:
        conv = await self.get_by_id(conversation_id)
        if conv:
            conv.status = status
            conv.updated_at = now_utc()
            await self._session.flush()

    async def list_by_session(self, session_id: str) -> list[Conversation]:
        result = await self._session.execute(
            select(Conversation)
            .where(Conversation.session_id == session_id)
            .options(selectinload(Conversation.messages))
            .order_by(Conversation.created_at.desc())
        )
        return list(result.scalars().all())
