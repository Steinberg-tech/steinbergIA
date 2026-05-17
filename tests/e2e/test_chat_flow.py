"""
End-to-end tests using FastAPI TestClient with mocked LLM and DB.
These tests validate the full HTTP pipeline without hitting external services.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from api.app import app
from api.dependencies import get_orchestrator, get_conversation_service
from modules.ai.agents.base_agent import AgentResponse
from modules.conversations.service import ConversationService
from modules.conversations.models import Conversation
from modules.ai.orchestrator import Orchestrator


def _mock_orchestrator() -> Orchestrator:
    orch = AsyncMock(spec=Orchestrator)
    orch.process.return_value = (
        "Seu pedido está em separação e será entregue em 3 dias úteis.",
        AgentResponse(message="...", escalate=False),
    )
    return orch


def _mock_conv_service() -> ConversationService:
    svc = AsyncMock(spec=ConversationService)
    conv = MagicMock(spec=Conversation)
    conv.id = "conv-e2e-001"
    conv.session_id = "5511999999999"
    svc.get_or_create.return_value = conv
    svc.save_user_message.return_value = MagicMock()
    svc.save_assistant_message.return_value = MagicMock()
    return svc


@pytest.fixture
def client():
    app.dependency_overrides[get_orchestrator] = _mock_orchestrator
    app.dependency_overrides[get_conversation_service] = _mock_conv_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_endpoint_returns_response(client):
    response = client.post("/chat", json={
        "message": "Qual o status do pedido 12345?",
        "session_id": "5511999999999",
        "platform": "whatsapp",
    })
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["session_id"] == "5511999999999"
    assert data["conversation_id"] == "conv-e2e-001"


def test_chat_rejects_empty_body(client):
    response = client.post("/chat", json={})
    assert response.status_code == 422


def test_chat_rejects_missing_session_id(client):
    response = client.post("/chat", json={"message": "oi"})
    assert response.status_code == 422
