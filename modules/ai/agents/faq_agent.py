from modules.ai.agents.base_agent import AgentResponse, BaseAgent
from modules.ai.llm.client import LLMClient
from modules.ai.prompts.agent_prompts import FAQ_AGENT_PROMPT
from modules.ai.tools.registry import ToolRegistry
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import AgentName

_log = get_logger("faq_agent")


class FAQAgent(BaseAgent):
    def __init__(self, llm: LLMClient, tools: ToolRegistry) -> None:
        self._llm = llm
        self._tools = tools

    @property
    def name(self) -> str:
        return AgentName.FAQ

    @property
    def description(self) -> str:
        return "Responde dúvidas frequentes usando a base de conhecimento."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        async with trace("faq_agent.handle"):
            tool_schemas = self._tools.get_tool_schemas()
            faq_tools = [t for t in tool_schemas if t["function"]["name"] == "search_knowledge"]

            llm_response = await self._llm.generate_response(
                system_prompt=FAQ_AGENT_PROMPT,
                user_message=user_message,
                history=context.get("history", []),
                tools=faq_tools,
            )

            if llm_response.tool_calls:
                tool_results = []
                for tc in llm_response.tool_calls:
                    result = await self._tools.execute(tc["name"], **tc["arguments"])
                    tool_results.append({"tool": tc["name"], "result": result})

                enriched_message = user_message + _format_tool_results(tool_results)
                final_response = await self._llm.generate_response(
                    system_prompt=FAQ_AGENT_PROMPT,
                    user_message=enriched_message,
                    history=context.get("history", []),
                )
                return AgentResponse(
                    message=final_response.content,
                    tool_calls=llm_response.tool_calls,
                    metadata={"tokens": final_response.output_tokens},
                )

        return AgentResponse(
            message=llm_response.content,
            metadata={"tokens": llm_response.output_tokens},
        )


def _format_tool_results(results: list[dict]) -> str:
    parts = ["\n\n[Resultados da base de conhecimento:]"]
    for r in results:
        items = r["result"].get("results", [])
        for item in items:
            parts.append(f"- {item.get('content', item)}")
    return "\n".join(parts)
