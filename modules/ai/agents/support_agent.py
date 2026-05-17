from modules.ai.agents.base_agent import AgentResponse, BaseAgent
from modules.ai.llm.client import LLMClient
from modules.ai.prompts.agent_prompts import SUPPORT_AGENT_PROMPT
from modules.ai.prompts.templates import TICKET_CREATED_TEMPLATE, render
from modules.ai.tools.registry import ToolRegistry
from observability.audit import log_event
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import AgentName

_log = get_logger("support_agent")


class SupportAgent(BaseAgent):
    def __init__(self, llm: LLMClient, tools: ToolRegistry) -> None:
        self._llm = llm
        self._tools = tools

    @property
    def name(self) -> str:
        return AgentName.SUPPORT

    @property
    def description(self) -> str:
        return "Abre chamados de suporte e escala para atendimento humano quando necessário."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        session_id = context.get("session_id", "unknown")

        async with trace("support_agent.handle", session_id=session_id):
            support_tools = [
                t for t in self._tools.get_tool_schemas()
                if t["function"]["name"] == "create_ticket"
            ]

            llm_response = await self._llm.generate_response(
                system_prompt=SUPPORT_AGENT_PROMPT,
                user_message=user_message,
                history=context.get("history", []),
                tools=support_tools,
            )

            if llm_response.tool_calls:
                tool_results = []
                for tc in llm_response.tool_calls:
                    args = {**tc["arguments"], "session_id": session_id}
                    result = await self._tools.execute(tc["name"], **args)
                    tool_results.append(result)

                ticket_data = tool_results[0] if tool_results else {}
                log_event("ticket_created", session_id, agent=self.name, details=ticket_data)

                confirmation = render(
                    TICKET_CREATED_TEMPLATE,
                    protocol=ticket_data.get("protocol", "N/D"),
                    sla=ticket_data.get("sla", "até 24h úteis"),
                )
                return AgentResponse(
                    message=confirmation,
                    tool_calls=llm_response.tool_calls,
                    escalate=ticket_data.get("priority") == "urgent",
                    metadata={"ticket": ticket_data},
                )

        return AgentResponse(message=llm_response.content)
