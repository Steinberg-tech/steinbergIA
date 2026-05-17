import pytest
from unittest.mock import AsyncMock, MagicMock

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
