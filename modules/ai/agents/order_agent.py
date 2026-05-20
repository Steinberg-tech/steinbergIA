from memory.user_memory import UserMemory
from modules.ai.agents.base_agent import AgentResponse, BaseAgent
from modules.ai.llm.client import LLMClient
from modules.ai.prompts.agent_prompts import ORDER_AGENT_PROMPT, build_user_context_block
from modules.ai.prompts.templates import ORDER_STATUS_TEMPLATE, render
from modules.ai.tools.registry import ToolRegistry
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import AgentName

_log = get_logger("order_agent")


class OrderAgent(BaseAgent):
    def __init__(self, llm: LLMClient, tools: ToolRegistry, user_memory: UserMemory) -> None:
        self._llm = llm
        self._tools = tools
        self._user_memory = user_memory

    @property
    def name(self) -> str:
        return AgentName.ORDER

    @property
    def description(self) -> str:
        return "Consulta status de pedidos e informações de entrega via ERP."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        session_id = context.get("session_id", "unknown")
        system_prompt = ORDER_AGENT_PROMPT + build_user_context_block(context)

        async with trace("order_agent.handle"):
            order_tools = [
                t for t in self._tools.get_tool_schemas()
                if t["function"]["name"] == "get_order_status"
            ]

            llm_response = await self._llm.generate_response(
                system_prompt=system_prompt,
                user_message=user_message,
                history=context.get("history", []),
                tools=order_tools,
            )

            if llm_response.tool_calls:
                tool_results = []
                for tc in llm_response.tool_calls:
                    result = await self._tools.execute(tc["name"], **tc["arguments"])
                    tool_results.append(result)

                order_info = tool_results[0] if tool_results else {}
                order_id = order_info.get("order_id")
                if order_id:
                    await self._user_memory.remember_last_order(session_id, order_id)

                enriched = user_message + "\n\n[Dados do pedido:]\n" + _format_order(order_info)
                final = await self._llm.generate_response(
                    system_prompt=system_prompt,
                    user_message=enriched,
                    history=context.get("history", []),
                )
                return AgentResponse(
                    message=final.content,
                    tool_calls=llm_response.tool_calls,
                    metadata={"order_data": order_info},
                )

        return AgentResponse(message=llm_response.content)


def _format_order(data: dict) -> str:
    return render(
        ORDER_STATUS_TEMPLATE,
        order_id=data.get("order_id", "N/D"),
        status=data.get("status", "N/D"),
        estimated_delivery=data.get("estimated_delivery", "N/D"),
        carrier=data.get("carrier", "N/D"),
        tracking_code=data.get("tracking_code", "N/D"),
    )
