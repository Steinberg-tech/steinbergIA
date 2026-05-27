from memory.user_memory import UserMemory
from modules.ai.agents.base_agent import AgentResponse, BaseAgent
from modules.ai.llm.client import LLMClient
from modules.ai.prompts.agent_prompts import PROJURIS_AGENT_PROMPT, build_user_context_block
from modules.ai.tools.registry import ToolRegistry
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import AgentName

_log = get_logger("projuris_agent")

_PROJURIS_TOOL_NAMES = {
    "buscar_cliente",
    "consultar_dados_cliente",
    "consultar_processos_cliente",
}


class ProjurisAgent(BaseAgent):
    def __init__(self, llm: LLMClient, tools: ToolRegistry, user_memory: UserMemory) -> None:
        self._llm = llm
        self._tools = tools
        self._user_memory = user_memory

    @property
    def name(self) -> str:
        return AgentName.PROJURIS

    @property
    def description(self) -> str:
        return "Identifica o cliente no projurisADV e consulta dados cadastrais e processos."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        session_id = context.get("session_id", "unknown")
        system_prompt = (
            PROJURIS_AGENT_PROMPT
            + build_user_context_block(context)
            + f"\n\n## TELEFONE DO CLIENTE\n- {session_id} (use em buscar_cliente)"
        )

        async with trace("projuris_agent.handle"):
            projuris_tools = [
                t for t in self._tools.get_tool_schemas()
                if t["function"]["name"] in _PROJURIS_TOOL_NAMES
            ]

            llm_response = await self._llm.generate_response(
                system_prompt=system_prompt,
                user_message=user_message,
                history=context.get("history", []),
                tools=projuris_tools,
            )

            if llm_response.tool_calls:
                tool_results = []
                for tc in llm_response.tool_calls:
                    result = await self._tools.execute(tc["name"], **tc["arguments"])
                    tool_results.append(result)
                    person_id = _extract_person_id(result)
                    if person_id:
                        await self._user_memory.update(
                            session_id, projuris_person_id=person_id
                        )

                enriched = (
                    user_message
                    + "\n\n[Dados do projurisADV:]\n"
                    + str(tool_results)
                )
                final = await self._llm.generate_response(
                    system_prompt=system_prompt,
                    user_message=enriched,
                    history=context.get("history", []),
                )
                return AgentResponse(
                    message=final.content,
                    tool_calls=llm_response.tool_calls,
                    metadata={"projuris_results": tool_results},
                )

        return AgentResponse(message=llm_response.content)


def _extract_person_id(result: dict) -> str | None:
    """Extrai o id da pessoa do resultado de buscar_cliente, se houver um único match."""
    results = result.get("results")
    if isinstance(results, list) and len(results) == 1:
        return results[0].get("id")
    return None
