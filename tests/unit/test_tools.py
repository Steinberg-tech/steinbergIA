import pytest
from unittest.mock import AsyncMock

from modules.ai.tools.search_tool import SearchTool
from modules.ai.tools.order_tool import OrderTool
from modules.ai.tools.registry import ToolRegistry
from shared.exceptions import ToolExecutionError


@pytest.mark.asyncio
async def test_search_tool_calls_knowledge_service():
    knowledge_service = AsyncMock()
    knowledge_service.search.return_value = [
        {"content": "Prazo é de 5 a 10 dias.", "score": 0.92}
    ]
    tool = SearchTool(knowledge_service)

    assert tool.name == "search_knowledge"
    result = await tool.execute(query="prazo de entrega", top_k=3)

    knowledge_service.search.assert_called_once_with("prazo de entrega", top_k=3)
    assert result["count"] == 1
    assert result["results"][0]["content"]


@pytest.mark.asyncio
async def test_order_tool_calls_erp():
    erp_client = AsyncMock()
    erp_client.get_order_status.return_value = {
        "order_id": "12345",
        "status": "Enviado",
        "estimated_delivery": "2026-05-20",
    }
    tool = OrderTool(erp_client)

    assert tool.name == "get_order_status"
    result = await tool.execute(order_id="12345")

    erp_client.get_order_status.assert_called_once_with("12345")
    assert result["order_id"] == "12345"


def test_registry_raises_on_unknown_tool():
    registry = ToolRegistry([])
    with pytest.raises(ToolExecutionError):
        registry.get("nonexistent_tool")


def test_registry_returns_tool_schemas():
    knowledge_service = AsyncMock()
    tool = SearchTool(knowledge_service)
    registry = ToolRegistry([tool])
    schemas = registry.get_tool_schemas()
    assert len(schemas) == 1
    assert schemas[0]["function"]["name"] == "search_knowledge"


@pytest.mark.asyncio
async def test_process_tool_calls_projuris_client():
    from modules.ai.tools.process_tool import ProcessTool

    projuris_mock = AsyncMock()
    projuris_mock.get_processo_by_numero.return_value = {
        "codigoProcesso": 25569655,
        "numeroProcesso": "0001234-12.2023.8.26.0000",
        "classeProcessual": "Procedimento Comum Cível",
        "orgaoJulgador": "1ª Vara Cível de São Paulo",
        "magistrado": "João da Silva",
        "partes": [{"nome": "Banco XPTO"}, {"nome": "José da Silva"}],
    }
    projuris_mock.get_processo_envolvidos.return_value = [
        {"codigoPessoaEnvolvido": 40407021, "nomePessoaEnvolvido": "JOSÉ", "participacaoTipo": "Autor"},
    ]
    tool = ProcessTool(projuris_mock)

    assert tool.name == "get_process_info"
    result = await tool.execute(numero_processo="0001234-12.2023.8.26.0000")

    projuris_mock.get_processo_by_numero.assert_called_once_with("0001234-12.2023.8.26.0000")
    assert result["numeroProcesso"] == "0001234-12.2023.8.26.0000"
    assert result["envolvidos"][0]["codigo_pessoa"] == 40407021
    projuris_mock.get_processo_envolvidos.assert_called_once_with(25569655)


@pytest.mark.asyncio
async def test_process_tool_raises_tool_execution_error_on_integration_error():
    from modules.ai.tools.process_tool import ProcessTool
    from shared.exceptions import IntegrationError, ToolExecutionError

    projuris_mock = AsyncMock()
    projuris_mock.get_processo_by_numero.side_effect = IntegrationError("HTTP 404 from /processos/xxx")
    tool = ProcessTool(projuris_mock)

    with pytest.raises(ToolExecutionError):
        await tool.execute(numero_processo="0000000-00.0000.0.00.0000")


@pytest.mark.asyncio
async def test_process_tool_sem_codigo_processo_nao_busca_envolvidos():
    from modules.ai.tools.process_tool import ProcessTool

    projuris_mock = AsyncMock()
    projuris_mock.get_processo_by_numero.return_value = {"numeroProcesso": "X"}  # sem codigoProcesso
    tool = ProcessTool(projuris_mock)

    result = await tool.execute(numero_processo="X")

    assert result["envolvidos"] == []
    projuris_mock.get_processo_envolvidos.assert_not_called()
