import pytest

from memory.user_memory import UserMemory


class _FakeCache:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ttl=None):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)


@pytest.mark.asyncio
async def test_remember_projuris_identity_persiste_campos():
    mem = UserMemory(_FakeCache())
    await mem.remember_projuris_identity(
        "s1",
        codigo_pessoa=42015519,
        nome="Israel",
        email="israel@x.com",
        habilitado=True,
        telefone="85997085202",
        checked_at=1000.0,
    )
    data = await mem.get("s1")
    assert data["projuris_codigo_pessoa"] == 42015519
    assert data["projuris_nome"] == "Israel"
    assert data["projuris_checked_at"] == 1000.0
    assert data["projuris_email"] == "israel@x.com"
    assert data["projuris_habilitado"] is True
    assert data["projuris_telefone"] == "85997085202"
