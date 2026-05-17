from modules.ai.agents.base_agent import BaseAgent
from observability.logger import get_logger
from shared.constants import AgentName, Intent, TemplateMessage
from shared.exceptions import AgentNotFoundError

_log = get_logger("intent_router")

_INTENT_TO_AGENT: dict[str, str] = {
    Intent.FAQ: AgentName.FAQ,
    Intent.ORDER_STATUS: AgentName.ORDER,
    Intent.SUPPORT: AgentName.SUPPORT,
    Intent.WORKFLOW: AgentName.WORKFLOW,
}

# Maps intents to the message template the agent should use as basis for the response.
# Intents without an explicit template fall back to None (agent uses its default prompt).
_INTENT_TO_TEMPLATE: dict[str, str | None] = {
    Intent.FAQ: None,
    Intent.ORDER_STATUS: TemplateMessage.CONTATO_INFORMACAO_PROCESSO,
    Intent.SUPPORT: TemplateMessage.CONTATO_URGENTE_OK,
    Intent.WORKFLOW: TemplateMessage.SOLICITACAO_DOCUMENTOS,
}


class IntentRouter:
    """Maps classified intents to the responsible agent and message template."""

    def __init__(self, agents: list[BaseAgent]) -> None:
        self._agents: dict[str, BaseAgent] = {a.name: a for a in agents}

    def route(self, intent: str) -> BaseAgent:
        agent_name = _INTENT_TO_AGENT.get(intent, AgentName.FAQ)
        agent = self._agents.get(agent_name)
        if agent is None:
            raise AgentNotFoundError(f"Agent '{agent_name}' not registered.")
        _log.info("intent_routed", intent=intent, agent=agent_name)
        return agent

    def resolve_template(self, intent: str) -> str | None:
        """Return the message template name associated with the intent, or None."""
        return _INTENT_TO_TEMPLATE.get(intent)
