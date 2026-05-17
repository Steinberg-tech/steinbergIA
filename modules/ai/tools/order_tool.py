from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError


class OrderTool(BaseTool):
    """Queries order status from the ERP integration."""

    def __init__(self, erp_client) -> None:
        self._erp = erp_client

    @property
    def name(self) -> str:
        return "get_order_status"

    @property
    def description(self) -> str:
        return (
            "Consulta o status de um pedido pelo número do pedido. "
            "Retorna status atual, previsão de entrega e código de rastreio."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "Número ou ID do pedido a ser consultado.",
                },
            },
            "required": ["order_id"],
        }

    async def execute(self, order_id: str) -> dict:
        async with trace("tool.get_order_status", order_id=order_id):
            try:
                return await self._erp.get_order_status(order_id)
            except Exception as exc:
                raise IntegrationError(f"Falha ao consultar pedido {order_id}: {exc}") from exc
