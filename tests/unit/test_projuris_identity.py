from unittest.mock import AsyncMock

import pytest

from memory.user_memory import UserMemory
from modules.integrations.projuris.identity import ProjurisIdentityService
from shared.exceptions import IntegrationError


class _FakeCache:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ttl=None):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)


def _service():
    client = AsyncMock()
    mem = UserMemory(_FakeCache())
    return ProjurisIdentityService(client, mem), client, mem


@pytest.mark.asyncio
async def test_busca_e_cacheia_quando_encontrado():
    svc, client, mem = _service()
    client.get_pessoa_by_telefone.return_value = {
        "codigoPessoa": 42015519, "nome": "Israel",
        "emailPrincipal": "i@x.com", "habilitado": True,
        "telefonePrincipal": "85997085202",
    }
    result = await svc.ensure_identity("s1", "558597085202")
    assert result["projuris_codigo_pessoa"] == 42015519
    client.get_pessoa_by_telefone.assert_awaited_once()


@pytest.mark.asyncio
async def test_usa_cache_positivo_sem_reconsultar():
    svc, client, mem = _service()
    await mem.update("s1", projuris_codigo_pessoa=1, projuris_checked_at=1.0)
    await svc.ensure_identity("s1", "558597085202")
    client.get_pessoa_by_telefone.assert_not_awaited()


@pytest.mark.asyncio
async def test_nao_encontrado_recente_nao_reconsulta(monkeypatch):
    svc, client, mem = _service()
    import modules.integrations.projuris.identity as mod
    monkeypatch.setattr(mod.time, "time", lambda: 1000.0)
    await mem.update("s1", projuris_codigo_pessoa=None, projuris_checked_at=999.0)
    await svc.ensure_identity("s1", "558597085202")
    client.get_pessoa_by_telefone.assert_not_awaited()


@pytest.mark.asyncio
async def test_erro_transitorio_nao_cacheia():
    svc, client, mem = _service()
    client.get_pessoa_by_telefone.side_effect = IntegrationError("down")
    result = await svc.ensure_identity("s1", "558597085202")
    assert "projuris_checked_at" not in result
