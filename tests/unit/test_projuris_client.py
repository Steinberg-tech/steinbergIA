import httpx
import pytest

from modules.integrations.projuris.projuris_client import ProjurisClient


class _FakeCache:
    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def set(self, key, value, ttl=None):
        self._store[key] = value

    async def delete(self, key):
        self._store.pop(key, None)


def _client(transport):
    cache = _FakeCache()
    client = ProjurisClient(
        cache=cache,
        base_url="https://auth.test",
        service_url="https://svc.test",
        username="u", password="p", client_id="c", client_secret="s",
    )
    # injeta um token válido para pular a autenticação
    cache._store[ProjurisClient._ACCESS_KEY] = "tok"
    return client, transport


@pytest.mark.asyncio
async def test_get_pessoa_by_telefone_retorna_primeiro_match(monkeypatch):
    calls = []

    async def handler(request):
        calls.append(dict(request.url.params))
        body = request.read().decode()
        assert '"telefone"' in body
        return httpx.Response(200, json={
            "totalRegistros": 1,
            "pessoaConsulta": [{"codigoPessoa": 42015519, "nome": "Israel"}],
        })

    transport = httpx.MockTransport(handler)
    _Real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda *a, **k: _Real(transport=transport),
    )

    client, _ = _client(transport)
    pessoa = await client.get_pessoa_by_telefone("(85)9 9708-5202")

    assert pessoa["codigoPessoa"] == 42015519
    assert calls[0]["pagina"] == "0"


@pytest.mark.asyncio
async def test_get_pessoa_by_telefone_sem_match_retorna_none(monkeypatch):
    async def handler(request):
        return httpx.Response(200, json={"totalRegistros": 0, "pessoaConsulta": []})

    transport = httpx.MockTransport(handler)
    _Real = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda *a, **k: _Real(transport=transport),
    )

    client, _ = _client(transport)
    assert await client.get_pessoa_by_telefone("85997085202") is None
