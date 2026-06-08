import pytest
from unittest.mock import AsyncMock

from memory.user_memory import UserMemory
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
    user_mem = AsyncMock(spec=UserMemory)
    agent = OrderAgent(mock_llm, mock_registry, user_mem)
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


@pytest.mark.asyncio
async def test_workflow_agent_injects_user_name_in_prompt(mock_llm):
    from memory.session import SessionMemory
    from modules.ai.agents.workflow_agent import WorkflowAgent

    session_mem = AsyncMock(spec=SessionMemory)
    session_mem.get.return_value = {}

    context = {
        "session_id": "s4",
        "history": [],
        "session": {},
        "user": {"name": "Carlos Lima"},
    }
    agent = WorkflowAgent(mock_llm, session_mem)
    await agent.handle("Quero fazer uma troca.", context)

    call_kwargs = mock_llm.generate_response.call_args_list[0].kwargs
    assert "Carlos Lima" in call_kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_order_agent_injects_user_name_in_prompt(mock_llm, mock_registry):
    user_mem = AsyncMock(spec=UserMemory)
    context = {
        "session_id": "s3",
        "history": [],
        "session": {},
        "user": {"name": "Ana Souza", "last_order_id": "PED-100"},
    }
    agent = OrderAgent(mock_llm, mock_registry, user_mem)
    await agent.handle("Qual o status do meu pedido?", context)

    call_kwargs = mock_llm.generate_response.call_args_list[0].kwargs
    assert "Ana Souza" in call_kwargs["system_prompt"]
    assert "PED-100" in call_kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_order_agent_saves_last_order_after_tool_call(mock_llm, mock_registry):
    user_mem = AsyncMock(spec=UserMemory)

    mock_llm.generate_response.side_effect = [
        LLMResponse(
            content="",
            model="gpt-4o-mock",
            tool_calls=[{"name": "get_order_status", "arguments": {"order_id": "PED-999"}}],
        ),
        LLMResponse(content="Seu pedido está a caminho.", model="gpt-4o-mock"),
    ]
    mock_registry_with_order = AsyncMock(spec=ToolRegistry)
    mock_registry_with_order.get_tool_schemas.return_value = [{
        "function": {"name": "get_order_status"}
    }]
    mock_registry_with_order.execute.return_value = {
        "order_id": "PED-999",
        "status": "em_transito",
        "estimated_delivery": "2026-05-25",
        "carrier": "Correios",
        "tracking_code": "BR123",
    }

    context = {
        "session_id": "s-order",
        "history": [],
        "session": {},
        "user": {},
    }
    agent = OrderAgent(mock_llm, mock_registry_with_order, user_mem)
    await agent.handle("Pedido PED-999", context)

    user_mem.remember_last_order.assert_called_once_with("s-order", "PED-999")


@pytest.mark.asyncio
async def test_order_agent_does_not_save_when_order_id_absent(mock_llm, mock_registry):
    user_mem = AsyncMock(spec=UserMemory)

    mock_llm.generate_response.side_effect = [
        LLMResponse(
            content="",
            model="gpt-4o-mock",
            tool_calls=[{"name": "get_order_status", "arguments": {"order_id": "X"}}],
        ),
        LLMResponse(content="Não encontrei o pedido.", model="gpt-4o-mock"),
    ]
    mock_registry_err = AsyncMock(spec=ToolRegistry)
    mock_registry_err.get_tool_schemas.return_value = [{"function": {"name": "get_order_status"}}]
    mock_registry_err.execute.return_value = {"error": "not_found"}

    context = {"session_id": "s-err", "history": [], "session": {}, "user": {}}
    agent = OrderAgent(mock_llm, mock_registry_err, user_mem)
    await agent.handle("Pedido X", context)

    user_mem.remember_last_order.assert_not_called()


@pytest.mark.asyncio
async def test_process_agent_with_tool_call(mock_context):
    from unittest.mock import AsyncMock
    from memory.user_memory import UserMemory
    from modules.ai.agents.process_agent import ProcessAgent
    from modules.ai.llm.schemas import LLMResponse
    from modules.ai.tools.process_tool import ProcessTool
    from modules.ai.tools.registry import ToolRegistry
    from modules.ai.llm.client import LLMClient
    from shared.constants import AgentName

    llm = AsyncMock(spec=LLMClient)
    llm.generate_response.side_effect = [
        LLMResponse(
            content="",
            model="gpt-4o-mock",
            tool_calls=[{
                "name": "get_process_info",
                "arguments": {"numero_processo": "0001234-12.2023.8.26.0000"},
            }],
        ),
        LLMResponse(
            content="Seu processo está na 1ª Vara Cível, sob responsabilidade do juiz João da Silva.",
            model="gpt-4o-mock",
        ),
    ]

    projuris_mock = AsyncMock()
    projuris_mock.get_processo_by_numero.return_value = {
        "numeroProcesso": "0001234-12.2023.8.26.0000",
        "codigoProcesso": 25569655,
        "classeProcessual": "Procedimento Comum Cível",
        "orgaoJulgador": "1ª Vara Cível",
        "magistrado": "João da Silva",
        "partes": [{"nome": "Banco XPTO"}, {"nome": "José da Silva"}],
    }
    projuris_mock.get_processo_envolvidos.return_value = [
        {"codigoPessoaEnvolvido": 42015519, "nomePessoaEnvolvido": "JOSÉ", "participacaoTipo": "Autor"},
    ]

    user_mem = AsyncMock(spec=UserMemory)
    registry = ToolRegistry([ProcessTool(projuris_mock)])
    agent = ProcessAgent(llm, registry, user_mem)

    assert agent.name == AgentName.PROCESS
    ctx = {**mock_context, "user": {"name": "José", "projuris_codigo_pessoa": 42015519}}
    response = await agent.handle("Como está meu processo 0001234-12.2023.8.26.0000?", ctx)

    assert isinstance(response, AgentResponse)
    assert response.message
    user_mem.remember_last_process.assert_called_once_with(
        "test-session-001", "0001234-12.2023.8.26.0000"
    )


@pytest.mark.asyncio
async def test_process_agent_asks_for_number_when_absent(mock_context):
    from unittest.mock import AsyncMock
    from memory.user_memory import UserMemory
    from modules.ai.agents.process_agent import ProcessAgent
    from modules.ai.llm.schemas import LLMResponse
    from modules.ai.tools.registry import ToolRegistry
    from modules.ai.llm.client import LLMClient

    llm = AsyncMock(spec=LLMClient)
    llm.generate_response.return_value = LLMResponse(
        content="Para consultar o senhor(a), preciso do número do processo. Poderia informá-lo?",
        model="gpt-4o-mock",
        tool_calls=None,
    )

    user_mem = AsyncMock(spec=UserMemory)
    registry = ToolRegistry([])
    agent = ProcessAgent(llm, registry, user_mem)

    response = await agent.handle("Como está meu processo?", mock_context)

    assert isinstance(response, AgentResponse)
    assert response.message
    user_mem.remember_last_process.assert_not_called()


@pytest.mark.asyncio
async def test_process_agent_returns_friendly_message_on_error(mock_context):
    from unittest.mock import AsyncMock
    from memory.user_memory import UserMemory
    from modules.ai.agents.process_agent import ProcessAgent
    from modules.ai.llm.schemas import LLMResponse
    from modules.ai.tools.process_tool import ProcessTool
    from modules.ai.tools.registry import ToolRegistry
    from modules.ai.llm.client import LLMClient
    from shared.exceptions import IntegrationError

    llm = AsyncMock(spec=LLMClient)
    llm.generate_response.return_value = LLMResponse(
        content="",
        model="gpt-4o-mock",
        tool_calls=[{
            "name": "get_process_info",
            "arguments": {"numero_processo": "9999999-00.2020.0.00.0000"},
        }],
    )

    projuris_mock = AsyncMock()
    projuris_mock.get_processo_by_numero.side_effect = IntegrationError("HTTP 404 from /processos/9999999")

    user_mem = AsyncMock(spec=UserMemory)
    registry = ToolRegistry([ProcessTool(projuris_mock)])
    agent = ProcessAgent(llm, registry, user_mem)

    response = await agent.handle("Processo 9999999-00.2020.0.00.0000", mock_context)

    assert isinstance(response, AgentResponse)
    assert response.message
    user_mem.remember_last_process.assert_not_called()


@pytest.mark.asyncio
async def test_user_memory_remember_last_process():
    import json
    from unittest.mock import AsyncMock
    from memory.user_memory import UserMemory
    from shared.interfaces import CacheBackend

    cache = AsyncMock(spec=CacheBackend)
    cache.get.return_value = None
    mem = UserMemory(cache)

    await mem.remember_last_process("session-xyz", "0001234-12.2023.8.26.0000")

    cache.set.assert_called_once()
    stored = json.loads(cache.set.call_args[0][1])
    assert stored["last_process_numero"] == "0001234-12.2023.8.26.0000"


@pytest.mark.asyncio
async def test_process_agent_nega_quando_nao_e_parte(mock_context):
    from unittest.mock import AsyncMock
    from memory.user_memory import UserMemory
    from modules.ai.agents.process_agent import ProcessAgent
    from modules.ai.llm.schemas import LLMResponse
    from modules.ai.tools.process_tool import ProcessTool
    from modules.ai.tools.registry import ToolRegistry
    from modules.ai.llm.client import LLMClient

    llm = AsyncMock(spec=LLMClient)
    llm.generate_response.return_value = LLMResponse(
        content="",
        model="gpt-4o-mock",
        tool_calls=[{"name": "get_process_info", "arguments": {"numero_processo": "0001234-12.2023.8.26.0000"}}],
    )
    projuris_mock = AsyncMock()
    projuris_mock.get_processo_by_numero.return_value = {"numeroProcesso": "X", "codigoProcesso": 1}
    projuris_mock.get_processo_envolvidos.return_value = [
        {"codigoPessoaEnvolvido": 99999, "nomePessoaEnvolvido": "OUTRO", "participacaoTipo": "Autor"},
    ]
    user_mem = AsyncMock(spec=UserMemory)
    agent = ProcessAgent(llm, ToolRegistry([ProcessTool(projuris_mock)]), user_mem)

    ctx = {**mock_context, "user": {"projuris_codigo_pessoa": 42015519}}
    response = await agent.handle("Quero ver o processo 0001234-12.2023.8.26.0000", ctx)

    assert "você é uma das partes" in response.message
    user_mem.remember_last_process.assert_not_called()


@pytest.mark.asyncio
async def test_process_agent_encaminha_quando_sem_cadastro(mock_context):
    from unittest.mock import AsyncMock
    from memory.user_memory import UserMemory
    from modules.ai.agents.process_agent import ProcessAgent
    from modules.ai.llm.schemas import LLMResponse
    from modules.ai.tools.process_tool import ProcessTool
    from modules.ai.tools.registry import ToolRegistry
    from modules.ai.llm.client import LLMClient

    llm = AsyncMock(spec=LLMClient)
    llm.generate_response.return_value = LLMResponse(
        content="",
        model="gpt-4o-mock",
        tool_calls=[{"name": "get_process_info", "arguments": {"numero_processo": "X"}}],
    )
    projuris_mock = AsyncMock()
    agent = ProcessAgent(llm, ToolRegistry([ProcessTool(projuris_mock)]), AsyncMock(spec=UserMemory))

    ctx = {**mock_context, "user": {}}  # sem projuris_codigo_pessoa
    response = await agent.handle("meu processo 0001234-12.2023.8.26.0000", ctx)

    assert response.escalate is True
    assert "atendente" in response.message
    projuris_mock.get_processo_by_numero.assert_not_called()
