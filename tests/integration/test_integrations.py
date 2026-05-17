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
