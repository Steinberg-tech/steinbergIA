from modules.ai.agents.base_agent import AgentResponse
from modules.ai.guardrails.input_guard import InputGuard
from modules.ai.guardrails.output_guard import OutputGuard
from modules.ai.llm.client import LLMClient
from modules.ai.router import IntentRouter
from memory.context_builder import ContextBuilder
from observability import metrics
from observability.audit import log_event
from observability.logger import get_logger
from observability.tracer import trace
from shared.exceptions import SACBaseError
from modules.ai.prompts.system_prompts import FALLBACK_MESSAGE

_log = get_logger("orchestrator")


class Orchestrator:
    """
    Central pipeline: receives a user message, classifies intent, routes to agent,
    executes tools, validates output, and returns the final response.
    """

    def __init__(
        self,
        llm: LLMClient,
        router: IntentRouter,
        input_guard: InputGuard,
        output_guard: OutputGuard,
        context_builder: ContextBuilder,
    ) -> None:
        self._llm = llm
        self._router = router
        self._input_guard = input_guard
        self._output_guard = output_guard
        self._context_builder = context_builder

    async def process(self, user_message: str, session_id: str) -> tuple[str, AgentResponse]:
        """
        Returns (final_text, agent_response) so callers can inspect escalation flags.
        """
        async with trace("orchestrator.process", session_id=session_id):
            # 1. Validate & sanitize input
            try:
                safe_input = self._input_guard.validate(user_message)
            except SACBaseError as exc:
                _log.warning("input_blocked", session_id=session_id, reason=str(exc))
                metrics.increment("guardrail.input_blocked")
                return str(exc), AgentResponse(message=str(exc))

            # 2. Build context (history + session + user memory)
            context = await self._context_builder.build(session_id)

            # 3. Classify intent via LLM
            async with trace("orchestrator.classify_intent"):
                classification = await self._llm.classify_intent(safe_input, context)

            _log.info(
                "intent_classified",
                session_id=session_id,
                intent=classification.intent,
                confidence=classification.confidence,
            )
            metrics.increment(f"intent.{classification.intent}")

            # 4. Route to agent
            agent = self._router.route(classification.intent)

            # 5. Agent processes message
            async with trace("orchestrator.agent_handle", agent=agent.name):
                try:
                    agent_response = await agent.handle(safe_input, context)
                except SACBaseError as exc:
                    _log.error("agent_error", agent=agent.name, error=str(exc))
                    metrics.increment("agent.error")
                    return FALLBACK_MESSAGE, AgentResponse(message=FALLBACK_MESSAGE)

            log_event(
                "message_processed",
                session_id,
                agent=agent.name,
                details={
                    "intent": classification.intent,
                    "escalate": agent_response.escalate,
                    "has_tool_calls": bool(agent_response.tool_calls),
                },
            )

            # 6. Validate output
            try:
                safe_output = self._output_guard.validate(agent_response.message)
            except SACBaseError as exc:
                _log.error("output_blocked", session_id=session_id, reason=str(exc))
                metrics.increment("guardrail.output_blocked")
                return FALLBACK_MESSAGE, AgentResponse(message=FALLBACK_MESSAGE)

            agent_response.message = safe_output
            metrics.increment("messages.processed")
            return safe_output, agent_response
