import pytest
from unittest.mock import AsyncMock

from modules.ai.agents.faq_agent import FAQAgent
from modules.ai.agents.order_agent import OrderAgent
from modules.ai.agents.support_agent import SupportAgent
from modules.ai.agents.base_agent import AgentResponse
from modules.ai.llm.schemas import LLMResponse
from modules.ai.tools.registry import ToolRegistry
from shared.constants import AgentName


@pytest.mark.asyncio
async def test_faq_agent_returns_response(mock_llm, mock_registry, mock_context):
    agent = FAQAgent(mock_llm, mock_registry)
    assert agent.name == AgentName.FAQ
    response = await agent.handle("O que é política de troca?", mock_context)
    assert isinstance(response, AgentResponse)
    assert response.message


@pytest.mark.asyncio
async def test_order_agent_returns_response(mock_llm, mock_registry, mock_context):
    agent = OrderAgent(mock_llm, mock_registry)
    assert agent.name == AgentName.ORDER
    response = await agent.handle("Qual o status do pedido 123?", mock_context)
    assert isinstance(response, AgentResponse)
    assert response.message


@pytest.mark.asyncio
async def test_faq_agent_calls_llm(mock_llm, mock_registry, mock_context):
    agent = FAQAgent(mock_llm, mock_registry)
    await agent.handle("Como funciona a devolução?", mock_context)
    mock_llm.generate_response.assert_called()


@pytest.mark.asyncio
async def test_support_agent_without_tool_call(mock_llm, mock_registry, mock_context):
    mock_llm.generate_response.return_value = LLMResponse(
        content="Entendido, vou registrar seu chamado.",
        model="gpt-4o-mock",
        tool_calls=None,
    )
    agent = SupportAgent(mock_llm, mock_registry)
    response = await agent.handle("Meu produto chegou quebrado!", mock_context)
    assert isinstance(response, AgentResponse)
    assert not response.escalate
