from modules.support.models import Ticket
from modules.support.repository import SupportRepository
from observability.logger import get_logger

_log = get_logger("support_service")


class SupportService:
    def __init__(self, repo: SupportRepository) -> None:
        self._repo = repo

    async def create_ticket(
        self,
        session_id: str,
        subject: str,
        description: str,
        order_id: str | None = None,
        priority: str = "medium",
    ) -> Ticket:
        ticket = await self._repo.create(
            session_id=session_id,
            subject=subject,
            description=description,
            order_id=order_id,
            priority=priority,
        )
        _log.info(
            "ticket_created",
            ticket_id=ticket.id,
            protocol=ticket.protocol,
            session_id=session_id,
        )
        return ticket

    async def get_tickets(self, session_id: str) -> list[Ticket]:
        return await self._repo.get_by_session(session_id)
