import json

import httpx
import pytest

from modules.integrations.projuris.projuris_client import ProjurisClient
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


def _client():
    cache = _FakeCache()
    client = ProjurisClient(
        cache=cache,
        base_url="https://auth.test",
        service_url="https://svc.test",
        username="u", password="p", client_id="c", client_secret="s",
    )
    cache._store[ProjurisClient._ACCESS_KEY] = "tok"
    return client


def _patch_transport(monkeypatch, handler):
    _Real = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _Real(transport=transport))


@pytest.mark.asyncio
async def test_get_pessoa_by_telefone_retorna_primeiro_match(monkeypatch):
    bodies = []

    async def handler(request):
        bodies.append(json.loads(request.read().decode()))
        assert dict(request.url.params)["pagina"] == "0"
        return httpx.Response(200, json={
            "totalRegistros": 1,
            "pessoaConsulta": [{"codigoPessoa": 42015519, "nome": "Israel"}],
        })

    _patch_transport(monkeypatch, handler)
    pessoa = await _client().get_pessoa_by_telefone("(85)9 9708-5202")

    assert pessoa["codigoPessoa"] == 42015519
    assert bodies[0]["telefone"] == "85997085202"


@pytest.mark.asyncio
async def test_get_pessoa_by_telefone_sem_match_retorna_none(monkeypatch):
    async def handler(request):
        return httpx.Response(200, json={"totalRegistros": 0, "pessoaConsulta": []})

    _patch_transport(monkeypatch, handler)
    assert await _client().get_pessoa_by_telefone("85997085202") is None


@pytest.mark.asyncio
async def test_get_pessoa_by_telefone_erro_http_levanta_integration_error(monkeypatch):
    async def handler(request):
        return httpx.Response(500)

    _patch_transport(monkeypatch, handler)
    with pytest.raises(IntegrationError):
        await _client().get_pessoa_by_telefone("85997085202")


@pytest.mark.asyncio
async def test_get_processo_envolvidos(monkeypatch):
    async def handler(request):
        assert request.url.path.endswith("/adv-service/processo/25569655")
        return httpx.Response(200, json={
            "codigoProcesso": 25569655,
            "processoEnvolvidoSimplificadoWs": [
                {"codigoPessoaEnvolvido": 40407021, "nomePessoaEnvolvido": "CLAUDINA", "participacaoTipo": "Autor"},
                {"codigoPessoaEnvolvido": 40407022, "nomePessoaEnvolvido": "BANCO PAN", "participacaoTipo": "Réu"},
            ],
        })

    _patch_transport(monkeypatch, handler)
    envolvidos = await _client().get_processo_envolvidos(25569655)
    assert {e["codigoPessoaEnvolvido"] for e in envolvidos} == {40407021, 40407022}


@pytest.mark.asyncio
async def test_get_processo_envolvidos_vazio(monkeypatch):
    async def handler(request):
        return httpx.Response(200, json={"codigoProcesso": 1})

    _patch_transport(monkeypatch, handler)
    assert await _client().get_processo_envolvidos(1) == []
