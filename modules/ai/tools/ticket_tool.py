from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.utils import generate_protocol


class TicketTool(BaseTool):
    """Opens a support ticket and returns a protocol number."""

    def __init__(self, support_service) -> None:
        self._support = support_service

    @property
    def name(self) -> str:
        return "create_ticket"

    @property
    def description(self) -> str:
        return (
            "Abre um chamado de suporte para o cliente. "
            "Retorna o número do protocolo e previsão de atendimento."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Identificador da sessão/contato do cliente.",
                },
                "subject": {
                    "type": "string",
                    "description": "Assunto resumido do chamado.",
                },
                "description": {
                    "type": "string",
                    "description": "Descrição detalhada do problema relatado.",
                },
                "order_id": {
                    "type": "string",
                    "description": "Número do pedido relacionado, se houver.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "default": "medium",
                },
            },
            "required": ["session_id", "subject", "description"],
        }

    async def execute(
        self,
        session_id: str,
        subject: str,
        description: str,
        order_id: str | None = None,
        priority: str = "medium",
    ) -> dict:
        async with trace("tool.create_ticket", session_id=session_id):
            ticket = await self._support.create_ticket(
                session_id=session_id,
                subject=subject,
                description=description,
                order_id=order_id,
                priority=priority,
            )
        return {
            "protocol": ticket.protocol,
            "ticket_id": ticket.id,
            "status": ticket.status,
            "sla": "até 24h úteis",
        }
