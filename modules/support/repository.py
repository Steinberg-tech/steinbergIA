from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.support.models import Ticket
from shared.constants import TicketStatus
from shared.utils import generate_id, generate_protocol, now_utc


class SupportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        session_id: str,
        subject: str,
        description: str,
        order_id: str | None = None,
        priority: str = "medium",
    ) -> Ticket:
        ticket = Ticket(
            id=generate_id(),
            protocol=generate_protocol(),
            session_id=session_id,
            subject=subject,
            description=description,
            order_id=order_id,
            priority=priority,
        )
        self._session.add(ticket)
        await self._session.flush()
        return ticket

    async def get_by_session(self, session_id: str) -> list[Ticket]:
        result = await self._session.execute(
            select(Ticket).where(Ticket.session_id == session_id).order_by(Ticket.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_status(self, ticket_id: str, status: TicketStatus) -> None:
        result = await self._session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = result.scalar_one_or_none()
        if ticket:
            ticket.status = status
            ticket.updated_at = now_utc()
