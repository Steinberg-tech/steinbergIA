import pytest
from unittest.mock import AsyncMock, MagicMock

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
