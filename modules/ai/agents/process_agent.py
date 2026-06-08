from memory.user_memory import UserMemory
from modules.ai.agents.base_agent import AgentResponse, BaseAgent
from modules.ai.llm.client import LLMClient
from modules.ai.prompts.agent_prompts import PROCESS_AGENT_PROMPT, build_user_context_block
from modules.ai.tools.registry import ToolRegistry
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import AgentName
from shared.exceptions import ToolExecutionError

_log = get_logger("process_agent")


class ProcessAgent(BaseAgent):
    def __init__(self, llm: LLMClient, tools: ToolRegistry, user_memory: UserMemory) -> None:
        self._llm = llm
        self._tools = tools
        self._user_memory = user_memory

    @property
    def name(self) -> str:
        return AgentName.PROCESS

    @property
    def description(self) -> str:
        return "Consulta informações de processos jurídicos via Projuris."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        session_id = context.get("session_id", "unknown")
        codigo_pessoa = context.get("user", {}).get("projuris_codigo_pessoa")
        system_prompt = PROCESS_AGENT_PROMPT + build_user_context_block(context)

        async with trace("process_agent.handle"):
            process_tools = [
                t for t in self._tools.get_tool_schemas()
                if t["function"]["name"] == "get_process_info"
            ]

            llm_response = await self._llm.generate_response(
                system_prompt=system_prompt,
                user_message=user_message,
                history=context.get("history", []),
                tools=process_tools,
            )

            if llm_response.tool_calls:
                # Trava 1: sem cadastro -> encaminhar para atendente, sem consultar.
                if not codigo_pessoa:
                    _log.info("process_no_identity", session_id=session_id)
                    return AgentResponse(
                        message=(
                            "Não localizei seu cadastro pelo número do WhatsApp. "
                            "Vou te encaminhar para um atendente para tratar do cadastro/demanda."
                        ),
                        escalate=True,
                    )

                for tc in llm_response.tool_calls:
                    try:
                        result = await self._tools.execute(tc["name"], **tc["arguments"])
                    except ToolExecutionError as exc:
                        _log.error("process_tool_error", error=str(exc))
                        if "404" in str(exc):
                            return AgentResponse(
                                message="Não encontrei o processo informado. Verifique o número e tente novamente."
                            )
                        return AgentResponse(
                            message="Sistema indisponível no momento. Tente novamente em alguns minutos."
                        )

                    # Trava 2: usuário precisa ser parte do processo.
                    partes = {e.get("codigo_pessoa") for e in result.get("envolvidos", [])}
                    if codigo_pessoa not in partes:
                        _log.info("process_access_denied", session_id=session_id, codigo_pessoa=codigo_pessoa)
                        return AgentResponse(
                            message=(
                                "Por segurança, só consigo te passar informações de processos em que "
                                "você é uma das partes. Se acredita que houve um engano, posso te "
                                "encaminhar para um atendente."
                            )
                        )

                    numero = tc["arguments"].get("numero_processo", "")
                    if numero:
                        await self._user_memory.remember_last_process(session_id, numero)

                    enriched = user_message + "\n\n[Dados do processo:]\n" + _format_processo(result)
                    final = await self._llm.generate_response(
                        system_prompt=system_prompt,
                        user_message=enriched,
                        history=context.get("history", []),
                    )
                    return AgentResponse(
                        message=final.content,
                        tool_calls=llm_response.tool_calls,
                        metadata={"processo_data": result},
                    )

        return AgentResponse(message=llm_response.content)


def _format_processo(data: dict) -> str:
    lines = []
    if numero := data.get("numeroProcesso"):
        lines.append(f"Número: {numero}")
    if assunto := data.get("nomeAssunto"):
        lines.append(f"Assunto: {assunto}")
    if orgao := data.get("nomeProcessoOrgao"):
        lines.append(f"Comarca/Órgão: {orgao}")
    if situacao := data.get("nomeSituacao"):
        lines.append(f"Situação: {situacao}")
    if instancia := data.get("tipoInstancia"):
        label = {"PRIMEIRA_INSTANCIA": "1ª Instância", "SEGUNDA_INSTANCIA": "2ª Instância"}.get(instancia, instancia)
        lines.append(f"Instância: {label}")
    if envolvidos := data.get("nomeEnvolvidos"):
        lines.append(f"Partes: {envolvidos}")
    if responsavel := data.get("nomeUsuariosResponsaveis"):
        lines.append(f"Advogado responsável: {responsavel}")
    return "\n".join(lines) if lines else "Dados do processo indisponíveis."
