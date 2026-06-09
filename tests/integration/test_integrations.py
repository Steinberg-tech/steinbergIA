"""
Integration tests for ERP and CRM clients (mock mode — no real endpoints needed).
"""

import pytest

from modules.integrations.erp.erp_client import ERPClient
from modules.integrations.crm.crm_client import CRMClient


@pytest.mark.asyncio
async def test_erp_client_mock_order():
    client = ERPClient()
    result = await client.get_order_status("PED-00123")
    assert result["order_id"] == "PED-00123"
    assert "status" in result
    assert "estimated_delivery" in result


@pytest.mark.asyncio
async def test_crm_client_mock_customer():
    client = CRMClient()
    result = await client.get_customer("5511999999999")
    assert result["phone"] == "5511999999999"
    assert "name" in result


@pytest.mark.asyncio
async def test_erp_client_mock_customer_orders():
    client = ERPClient()
    orders = await client.get_customer_orders("customer-001")
    assert isinstance(orders, list)
    assert len(orders) > 0


import os
from unittest.mock import AsyncMock
from shared.interfaces import CacheBackend

_PROJURIS_CONFIGURED = bool(os.getenv("PROJURIS_BASE_URL"))


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not _PROJURIS_CONFIGURED, reason="PROJURIS_BASE_URL não configurado")
async def test_projuris_client_authenticates():
    from config.settings import settings
    from modules.integrations.projuris.projuris_client import ProjurisClient

    cache = AsyncMock(spec=CacheBackend)
    cache.get.return_value = None

    client = ProjurisClient(
        cache=cache,
        base_url=settings.projuris_base_url,
        username=settings.projuris_username,
        password=settings.projuris_password,
    )

    token = await client._get_valid_token()
    assert isinstance(token, str) and len(token) > 10
    cache.set.assert_called()


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not _PROJURIS_CONFIGURED, reason="PROJURIS_BASE_URL não configurado")
async def test_projuris_client_uses_cached_token():
    from modules.integrations.projuris.projuris_client import ProjurisClient

    cache = AsyncMock(spec=CacheBackend)
    cache.get.return_value = "token-do-cache-123"

    client = ProjurisClient(
        cache=cache,
        base_url="https://api.projuris.com.br",
        username="u",
        password="p",
    )

    token = await client._get_valid_token()
    assert token == "token-do-cache-123"
    cache.set.assert_not_called()
