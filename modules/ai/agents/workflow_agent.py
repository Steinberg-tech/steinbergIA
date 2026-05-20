from modules.ai.agents.base_agent import AgentResponse, BaseAgent
from modules.ai.llm.client import LLMClient
from modules.ai.prompts.agent_prompts import WORKFLOW_AGENT_PROMPT, build_user_context_block
from memory.session import SessionMemory
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import AgentName

_log = get_logger("workflow_agent")

_SUPPORTED_WORKFLOWS = {
    "troca": "Processo de troca de produto",
    "cancelamento": "Cancelamento de pedido",
    "reembolso": "Solicitação de reembolso",
    "devolucao": "Devolução de produto",
}


class WorkflowAgent(BaseAgent):
    """
    Handles multi-step conversational workflows (exchange, cancellation, refund).
    Tracks current step in SessionMemory so each message resumes where it left off.
    """

    def __init__(self, llm: LLMClient, session_memory: SessionMemory) -> None:
        self._llm = llm
        self._session = session_memory

    @property
    def name(self) -> str:
        return AgentName.WORKFLOW

    @property
    def description(self) -> str:
        return "Conduz fluxos multi-etapa: troca, cancelamento, reembolso, devolução."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        session_id = context.get("session_id", "unknown")

        async with trace("workflow_agent.handle", session_id=session_id):
            session_data = await self._session.get(session_id)
            active_workflow = session_data.get("active_workflow")

            workflow_context = _build_workflow_context(active_workflow, session_data)
            system_prompt = (
                WORKFLOW_AGENT_PROMPT
                + build_user_context_block(context)
                + workflow_context
            )

            llm_response = await self._llm.generate_response(
                system_prompt=system_prompt,
                user_message=user_message,
                history=context.get("history", []),
            )

            detected_workflow = _detect_workflow(user_message)
            if detected_workflow and not active_workflow:
                await self._session.update(
                    session_id,
                    active_workflow=detected_workflow,
                    workflow_step=1,
                )
                _log.info("workflow_started", session_id=session_id, workflow=detected_workflow)

        return AgentResponse(
            message=llm_response.content,
            metadata={"active_workflow": active_workflow or detected_workflow},
        )


def _detect_workflow(text: str) -> str | None:
    lower = text.lower()
    for key in _SUPPORTED_WORKFLOWS:
        if key in lower:
            return key
    return None


def _build_workflow_context(active_workflow: str | None, session_data: dict) -> str:
    if not active_workflow:
        return f"\n\nFluxos disponíveis: {', '.join(_SUPPORTED_WORKFLOWS.keys())}"
    step = session_data.get("workflow_step", 1)
    return (
        f"\n\nFluxo ativo: {_SUPPORTED_WORKFLOWS.get(active_workflow, active_workflow)}"
        f"\nEtapa atual: {step}"
        f"\nDados coletados: {session_data}"
    )
