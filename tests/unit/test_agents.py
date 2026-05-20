import pytest
from unittest.mock import AsyncMock

from modules.ai.agents.faq_agent import FAQAgent
from modules.ai.agents.order_agent import OrderAgent
from modules.ai.agents.support_agent import SupportAgent
from modules.ai.agents.base_agent import AgentResponse
from modules.ai.llm.schemas import LLMResponse
from modules.ai.tools.registry import ToolRegistry
from modules.ai.prompts.agent_prompts import build_user_context_block
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


def test_build_user_context_block_with_full_user():
    context = {
        "user": {"name": "Maria Silva", "last_order_id": "PED-999"},
        "session": {},
    }
    result = build_user_context_block(context)
    assert "Maria Silva" in result
    assert "PED-999" in result


def test_build_user_context_block_with_empty_user():
    context = {"user": {}, "session": {}}
    result = build_user_context_block(context)
    assert result == ""


def test_build_user_context_block_with_missing_user():
    context = {"session": {}}
    result = build_user_context_block(context)
    assert result == ""


def test_build_user_context_block_partial_user():
    context = {"user": {"name": "João"}, "session": {}}
    result = build_user_context_block(context)
    assert "João" in result
    assert "last_order_id" not in result


@pytest.mark.asyncio
async def test_faq_agent_injects_user_name_in_prompt(mock_llm, mock_registry):
    context = {
        "session_id": "s1",
        "history": [],
        "session": {},
        "user": {"name": "Maria Silva"},
    }
    agent = FAQAgent(mock_llm, mock_registry)
    await agent.handle("Qual a política de devolução?", context)

    call_kwargs = mock_llm.generate_response.call_args_list[0].kwargs
    assert "Maria Silva" in call_kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_support_agent_injects_user_name_in_prompt(mock_llm, mock_registry):
    context = {
        "session_id": "s2",
        "history": [],
        "session": {},
        "user": {"name": "João Pereira"},
    }
    agent = SupportAgent(mock_llm, mock_registry)
    await agent.handle("Quero abrir um chamado.", context)

    call_kwargs = mock_llm.generate_response.call_args_list[0].kwargs
    assert "João Pereira" in call_kwargs["system_prompt"]
