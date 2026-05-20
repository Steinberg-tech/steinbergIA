import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from api.app import app

from modules.conversations.service import ConversationService
from modules.conversations.repository import ConversationRepository
from modules.conversations.schemas import MessageSchema
from shared.constants import ConversationStatus, MessageRole, Platform


@pytest.fixture
def mock_repo():
    return AsyncMock(spec=ConversationRepository)


@pytest.fixture
def service(mock_repo) -> ConversationService:
    return ConversationService(mock_repo)


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(service, mock_repo):
    existing = MagicMock()
    existing.id = "conv-123"
    mock_repo.get_by_session.return_value = existing

    conv = await service.get_or_create("session-001", Platform.API)
    assert conv.id == "conv-123"
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_creates_new_when_none(service, mock_repo):
    mock_repo.get_by_session.return_value = None
    new_conv = MagicMock()
    new_conv.id = "conv-new"
    mock_repo.create.return_value = new_conv

    conv = await service.get_or_create("session-002", Platform.WHATSAPP)
    assert conv.id == "conv-new"
    mock_repo.create.assert_called_once_with("session-002", Platform.WHATSAPP)


@pytest.mark.asyncio
async def test_get_history_returns_empty_when_no_conversation(service, mock_repo):
    mock_repo.get_by_session.return_value = None
    history = await service.get_history("session-unknown")
    assert history == []


@pytest.mark.asyncio
async def test_escalate_calls_repo(service, mock_repo):
    await service.escalate("conv-001")
    mock_repo.update_status.assert_called_once_with("conv-001", ConversationStatus.ESCALATED)


@pytest.fixture
def mock_cache_backend():
    return AsyncMock()


@pytest.mark.asyncio
async def test_user_memory_clear_deletes_key(mock_cache_backend):
    from memory.user_memory import UserMemory
    mem = UserMemory(mock_cache_backend)
    await mem.clear("session-abc")
    mock_cache_backend.delete.assert_called_once_with("user_memory:session-abc")


@pytest.mark.asyncio
async def test_reset_command_clears_memory_and_resolves_conversation():
    session_mem = AsyncMock()
    user_mem = AsyncMock()
    conv_service = AsyncMock()

    fake_conv = MagicMock()
    fake_conv.id = "conv-999"
    conv_service.get_or_create.return_value = fake_conv

    with (
        patch("api.routes.chat.get_session_memory", return_value=session_mem),
        patch("api.routes.chat.get_user_memory", return_value=user_mem),
        patch("api.routes.chat.get_conversation_service", return_value=conv_service),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/chat", json={
                "message": "/reset",
                "session_id": "session-abc",
                "platform": "api",
            })

    assert resp.status_code == 200
    data = resp.json()
    assert "resetada" in data["message"].lower()
    session_mem.clear.assert_called_once_with("session-abc")
    user_mem.clear.assert_called_once_with("session-abc")
    conv_service.resolve.assert_called_once_with("conv-999")
    conv_service.save_user_message.assert_not_called()


@pytest.mark.asyncio
async def test_reset_command_case_insensitive():
    """Verifica que /RESET e /Reset também funcionam."""
    session_mem = AsyncMock()
    user_mem = AsyncMock()
    conv_service = AsyncMock()

    fake_conv = MagicMock()
    fake_conv.id = "conv-888"
    conv_service.get_or_create.return_value = fake_conv

    with (
        patch("api.routes.chat.get_session_memory", return_value=session_mem),
        patch("api.routes.chat.get_user_memory", return_value=user_mem),
        patch("api.routes.chat.get_conversation_service", return_value=conv_service),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/chat", json={
                "message": "/RESET",
                "session_id": "session-abc",
                "platform": "api",
            })

    assert resp.status_code == 200
    session_mem.clear.assert_called_once()
