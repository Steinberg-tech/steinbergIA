# Integração projurisADV (Pessoas/Clientes) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Montar a estrutura de integração da IA com o projurisADV (recurso Pessoas/Clientes), pronta para ativação quando os dados reais e os endpoints definitivos chegarem.

**Architecture:** Segue o padrão do projeto — um `ProjurisClient(BaseClient)` para HTTP, três tools finas registradas no `ToolRegistry`, um `ProjurisAgent(BaseAgent)` roteado por um novo intent `client_data`. Sem dados mockados: se não configurado, o client lança `IntegrationError`. Identidade do cliente = `session_id` (telefone), usado para auto-busca.

**Tech Stack:** Python 3.11+, httpx, tenacity, pydantic-settings, pytest, pytest-asyncio.

---

## Estrutura de arquivos

**Criar:**
- `modules/integrations/projuris/__init__.py`
- `modules/integrations/projuris/projuris_client.py` — cliente HTTP (3 métodos de leitura)
- `modules/ai/tools/projuris_search_person_tool.py` — tool `buscar_cliente`
- `modules/ai/tools/projuris_person_data_tool.py` — tool `consultar_dados_cliente`
- `modules/ai/tools/projuris_person_cases_tool.py` — tool `consultar_processos_cliente`
- `modules/ai/agents/projuris_agent.py` — `ProjurisAgent`
- `tests/unit/test_projuris_client.py`
- `tests/unit/test_projuris_tools.py`

**Modificar:**
- `config/settings.py` — 3 variáveis de config
- `shared/constants.py` — `Intent.CLIENT_DATA`, `AgentName.PROJURIS`
- `modules/ai/router.py` — mapear intent → agente
- `modules/ai/prompts/agent_prompts.py` — `PROJURIS_AGENT_PROMPT`
- `modules/ai/llm/providers/openai_provider.py` — descrição do intent
- `modules/ai/llm/providers/anthropic_provider.py` — descrição do intent
- `modules/ai/llm/providers/deepseek_provider.py` — descrição do intent
- `api/dependencies.py` — fiação (client, tools, agente)
- `tests/unit/test_agents.py` — testes do `ProjurisAgent`

---

## Task 1: Configuração e Constantes

**Files:**
- Modify: `config/settings.py` (após o bloco CRM, ~linha 54)
- Modify: `shared/constants.py` (enums `Intent` e `AgentName`)

- [ ] **Step 1: Adicionar config do projurisADV**

Em `config/settings.py`, após o bloco `# CRM`:

```python
    # projurisADV
    projuris_base_url: str = ""
    projuris_api_key: str = ""
    projuris_timeout_seconds: int = 10
```

- [ ] **Step 2: Adicionar intent e nome do agente**

Em `shared/constants.py`, dentro de `class Intent(StrEnum)`:

```python
    CLIENT_DATA = "client_data"
```

Dentro de `class AgentName(StrEnum)`:

```python
    PROJURIS = "projuris_agent"
```

- [ ] **Step 3: Verificar import**

Run: `python -c "from config.settings import settings; from shared.constants import Intent, AgentName; print(settings.projuris_timeout_seconds, Intent.CLIENT_DATA, AgentName.PROJURIS)"`
Expected: `10 client_data projuris_agent`

- [ ] **Step 4: Commit**

```bash
git add config/settings.py shared/constants.py
git commit -m "feat: add projurisADV config e intent client_data"
```

---

## Task 2: ProjurisClient

**Files:**
- Create: `modules/integrations/projuris/__init__.py`
- Create: `modules/integrations/projuris/projuris_client.py`
- Test: `tests/unit/test_projuris_client.py`

- [ ] **Step 1: Criar o pacote**

Criar `modules/integrations/projuris/__init__.py` vazio.

- [ ] **Step 2: Escrever os testes (devem falhar)**

Criar `tests/unit/test_projuris_client.py`:

```python
import pytest
from unittest.mock import AsyncMock

from modules.integrations.projuris.projuris_client import ProjurisClient
from shared.exceptions import IntegrationError


@pytest.mark.asyncio
async def test_search_person_raises_when_not_configured(monkeypatch):
    from config import settings as settings_mod
    monkeypatch.setattr(settings_mod.settings, "projuris_base_url", "")
    client = ProjurisClient()
    with pytest.raises(IntegrationError):
        await client.search_person("Maria")


@pytest.mark.asyncio
async def test_get_person_raises_when_not_configured(monkeypatch):
    from config import settings as settings_mod
    monkeypatch.setattr(settings_mod.settings, "projuris_base_url", "")
    client = ProjurisClient()
    with pytest.raises(IntegrationError):
        await client.get_person("123")


@pytest.mark.asyncio
async def test_get_person_cases_raises_when_not_configured(monkeypatch):
    from config import settings as settings_mod
    monkeypatch.setattr(settings_mod.settings, "projuris_base_url", "")
    client = ProjurisClient()
    with pytest.raises(IntegrationError):
        await client.get_person_cases("123")


@pytest.mark.asyncio
async def test_search_person_calls_get_when_configured(monkeypatch):
    from config import settings as settings_mod
    monkeypatch.setattr(settings_mod.settings, "projuris_base_url", "https://api.projuris.test")
    client = ProjurisClient()
    client._get = AsyncMock(return_value=[{"id": "1", "nome": "Maria"}])

    result = await client.search_person("Maria")

    client._get.assert_called_once()
    assert result == [{"id": "1", "nome": "Maria"}]


@pytest.mark.asyncio
async def test_get_person_calls_get_with_id(monkeypatch):
    from config import settings as settings_mod
    monkeypatch.setattr(settings_mod.settings, "projuris_base_url", "https://api.projuris.test")
    client = ProjurisClient()
    client._get = AsyncMock(return_value={"id": "42", "cpf": "000"})

    result = await client.get_person("42")

    args, _ = client._get.call_args
    assert "42" in args[0]
    assert result["id"] == "42"
```

- [ ] **Step 3: Rodar testes e confirmar falha**

Run: `pytest tests/unit/test_projuris_client.py -v`
Expected: FAIL — `ModuleNotFoundError: modules.integrations.projuris.projuris_client`

- [ ] **Step 4: Implementar o ProjurisClient**

Criar `modules/integrations/projuris/projuris_client.py`:

```python
from config.settings import settings
from modules.integrations.base_client import BaseClient
from observability.logger import get_logger
from shared.exceptions import IntegrationError

_log = get_logger("projuris_client")

# Paths da API projurisADV (SajAdv REST). Ajustar quando a documentação
# definitiva do escritório chegar — toda dependência de endpoint vive aqui.
PERSON_SEARCH_PATH = "/pessoa/consulta"
PERSON_DATA_PATH = "/pessoa/{person_id}"
PERSON_CASES_PATH = "/pessoa/{person_id}/processos"


class ProjurisClient(BaseClient):
    """
    Cliente de integração com o projurisADV (Pessoas/Clientes).
    Somente leitura. Sem mock: lança IntegrationError quando não configurado.
    """

    def __init__(self) -> None:
        super().__init__(
            base_url=settings.projuris_base_url,
            api_key=settings.projuris_api_key,
            timeout=settings.projuris_timeout_seconds,
        )
        self._configured = bool(settings.projuris_base_url)

    def _ensure_configured(self) -> None:
        if not self._configured:
            raise IntegrationError(
                "projurisADV não configurado — defina PROJURIS_BASE_URL no .env"
            )

    async def search_person(self, query: str) -> list[dict]:
        self._ensure_configured()
        data = await self._get(PERSON_SEARCH_PATH, params={"q": query})
        _log.info("projuris_person_search", query=query)
        return data

    async def get_person(self, person_id: str) -> dict:
        self._ensure_configured()
        data = await self._get(PERSON_DATA_PATH.format(person_id=person_id))
        _log.info("projuris_person_fetched", person_id=person_id)
        return data

    async def get_person_cases(self, person_id: str) -> list[dict]:
        self._ensure_configured()
        data = await self._get(PERSON_CASES_PATH.format(person_id=person_id))
        _log.info("projuris_person_cases_fetched", person_id=person_id)
        return data
```

- [ ] **Step 5: Rodar testes e confirmar sucesso**

Run: `pytest tests/unit/test_projuris_client.py -v`
Expected: PASS (5 passed)

- [ ] **Step 6: Commit**

```bash
git add modules/integrations/projuris/ tests/unit/test_projuris_client.py
git commit -m "feat: add ProjurisClient para Pessoas/Clientes do projurisADV"
```

---

## Task 3: Tools projurisADV

**Files:**
- Create: `modules/ai/tools/projuris_search_person_tool.py`
- Create: `modules/ai/tools/projuris_person_data_tool.py`
- Create: `modules/ai/tools/projuris_person_cases_tool.py`
- Test: `tests/unit/test_projuris_tools.py`

- [ ] **Step 1: Escrever os testes (devem falhar)**

Criar `tests/unit/test_projuris_tools.py`:

```python
import pytest
from unittest.mock import AsyncMock

from modules.ai.tools.projuris_search_person_tool import ProjurisSearchPersonTool
from modules.ai.tools.projuris_person_data_tool import ProjurisPersonDataTool
from modules.ai.tools.projuris_person_cases_tool import ProjurisPersonCasesTool
from shared.exceptions import IntegrationError


@pytest.mark.asyncio
async def test_search_person_tool_calls_client():
    client = AsyncMock()
    client.search_person.return_value = [{"id": "1", "nome": "Maria"}]
    tool = ProjurisSearchPersonTool(client)

    assert tool.name == "buscar_cliente"
    result = await tool.execute(query="Maria")

    client.search_person.assert_called_once_with("Maria")
    assert result["results"] == [{"id": "1", "nome": "Maria"}]


@pytest.mark.asyncio
async def test_person_data_tool_calls_client():
    client = AsyncMock()
    client.get_person.return_value = {"id": "42", "cpf": "000"}
    tool = ProjurisPersonDataTool(client)

    assert tool.name == "consultar_dados_cliente"
    result = await tool.execute(person_id="42")

    client.get_person.assert_called_once_with("42")
    assert result["id"] == "42"


@pytest.mark.asyncio
async def test_person_cases_tool_calls_client():
    client = AsyncMock()
    client.get_person_cases.return_value = [{"numero": "0001"}]
    tool = ProjurisPersonCasesTool(client)

    assert tool.name == "consultar_processos_cliente"
    result = await tool.execute(person_id="42")

    client.get_person_cases.assert_called_once_with("42")
    assert result["count"] == 1


@pytest.mark.asyncio
async def test_search_person_tool_wraps_error():
    client = AsyncMock()
    client.search_person.side_effect = RuntimeError("boom")
    tool = ProjurisSearchPersonTool(client)

    with pytest.raises(IntegrationError):
        await tool.execute(query="Maria")
```

- [ ] **Step 2: Rodar testes e confirmar falha**

Run: `pytest tests/unit/test_projuris_tools.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implementar a tool de busca**

Criar `modules/ai/tools/projuris_search_person_tool.py`:

```python
from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError


class ProjurisSearchPersonTool(BaseTool):
    """Busca um cliente no projurisADV por nome, CPF ou telefone."""

    def __init__(self, projuris_client) -> None:
        self._projuris = projuris_client

    @property
    def name(self) -> str:
        return "buscar_cliente"

    @property
    def description(self) -> str:
        return (
            "Busca um cliente no sistema jurídico (projurisADV) por nome, CPF ou "
            "telefone. Retorna a lista de pessoas encontradas com seus identificadores."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nome, CPF ou telefone do cliente a buscar.",
                },
            },
            "required": ["query"],
        }

    async def execute(self, query: str) -> dict:
        async with trace("tool.buscar_cliente", query=query):
            try:
                results = await self._projuris.search_person(query)
                return {"results": results, "count": len(results)}
            except Exception as exc:
                raise IntegrationError(f"Falha ao buscar cliente '{query}': {exc}") from exc
```

- [ ] **Step 4: Implementar a tool de dados cadastrais**

Criar `modules/ai/tools/projuris_person_data_tool.py`:

```python
from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError


class ProjurisPersonDataTool(BaseTool):
    """Consulta os dados cadastrais de um cliente no projurisADV."""

    def __init__(self, projuris_client) -> None:
        self._projuris = projuris_client

    @property
    def name(self) -> str:
        return "consultar_dados_cliente"

    @property
    def description(self) -> str:
        return (
            "Consulta os dados cadastrais de um cliente (CPF, endereço, contatos) "
            "pelo identificador da pessoa no projurisADV."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "person_id": {
                    "type": "string",
                    "description": "Identificador da pessoa no projurisADV.",
                },
            },
            "required": ["person_id"],
        }

    async def execute(self, person_id: str) -> dict:
        async with trace("tool.consultar_dados_cliente", person_id=person_id):
            try:
                return await self._projuris.get_person(person_id)
            except Exception as exc:
                raise IntegrationError(
                    f"Falha ao consultar dados do cliente {person_id}: {exc}"
                ) from exc
```

- [ ] **Step 5: Implementar a tool de processos**

Criar `modules/ai/tools/projuris_person_cases_tool.py`:

```python
from modules.ai.tools.base_tool import BaseTool
from observability.tracer import trace
from shared.exceptions import IntegrationError


class ProjurisPersonCasesTool(BaseTool):
    """Lista os processos vinculados a um cliente no projurisADV."""

    def __init__(self, projuris_client) -> None:
        self._projuris = projuris_client

    @property
    def name(self) -> str:
        return "consultar_processos_cliente"

    @property
    def description(self) -> str:
        return (
            "Lista os processos vinculados a um cliente pelo identificador da pessoa "
            "no projurisADV. Use após identificar o cliente com buscar_cliente."
        )

    @property
    def parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "person_id": {
                    "type": "string",
                    "description": "Identificador da pessoa no projurisADV.",
                },
            },
            "required": ["person_id"],
        }

    async def execute(self, person_id: str) -> dict:
        async with trace("tool.consultar_processos_cliente", person_id=person_id):
            try:
                cases = await self._projuris.get_person_cases(person_id)
                return {"cases": cases, "count": len(cases)}
            except Exception as exc:
                raise IntegrationError(
                    f"Falha ao consultar processos do cliente {person_id}: {exc}"
                ) from exc
```

- [ ] **Step 6: Rodar testes e confirmar sucesso**

Run: `pytest tests/unit/test_projuris_tools.py -v`
Expected: PASS (4 passed)

- [ ] **Step 7: Commit**

```bash
git add modules/ai/tools/projuris_*.py tests/unit/test_projuris_tools.py
git commit -m "feat: add tools projurisADV (buscar/dados/processos do cliente)"
```

---

## Task 4: ProjurisAgent e Prompt

**Files:**
- Modify: `modules/ai/prompts/agent_prompts.py` (adicionar prompt no final, antes de `build_user_context_block`)
- Create: `modules/ai/agents/projuris_agent.py`
- Test: `tests/unit/test_agents.py` (adicionar ao final)

- [ ] **Step 1: Adicionar o PROJURIS_AGENT_PROMPT**

Em `modules/ai/prompts/agent_prompts.py`, após `WORKFLOW_AGENT_PROMPT` (antes da função `build_user_context_block`):

```python
PROJURIS_AGENT_PROMPT = BASE_SYSTEM_PROMPT + """
Sua especialidade: identificar o cliente no sistema jurídico (projurisADV) e
responder sobre seus dados cadastrais e processos vinculados.
- O telefone do cliente está no contexto. Use a ferramenta buscar_cliente com esse
  telefone para identificá-lo automaticamente — NÃO peça CPF se já o identificou.
- Após identificar, use consultar_dados_cliente para dados cadastrais e
  consultar_processos_cliente para listar os processos.
- Diferencie-se do status de processo individual: aqui o foco é o cliente e a
  visão geral dos seus processos, não o andamento detalhado de um processo específico.
- Se o sistema jurídico não estiver disponível, informe que a consulta está
  temporariamente indisponível e ofereça atendimento humano.
"""
```

- [ ] **Step 2: Escrever os testes (devem falhar)**

Em `tests/unit/test_agents.py`, adicionar os imports no topo (junto aos demais agentes):

```python
from modules.ai.agents.projuris_agent import ProjurisAgent
```

E adicionar ao final do arquivo:

```python
@pytest.mark.asyncio
async def test_projuris_agent_returns_response(mock_llm, mock_registry, mock_context):
    user_mem = AsyncMock(spec=UserMemory)
    agent = ProjurisAgent(mock_llm, mock_registry, user_mem)
    assert agent.name == AgentName.PROJURIS
    response = await agent.handle("Quais são meus processos?", mock_context)
    assert isinstance(response, AgentResponse)
    assert response.message


@pytest.mark.asyncio
async def test_projuris_agent_injects_phone_in_prompt(mock_llm, mock_registry):
    user_mem = AsyncMock(spec=UserMemory)
    context = {
        "session_id": "5585999990000",
        "history": [],
        "session": {},
        "user": {},
    }
    agent = ProjurisAgent(mock_llm, mock_registry, user_mem)
    await agent.handle("Meus processos", context)

    call_kwargs = mock_llm.generate_response.call_args_list[0].kwargs
    assert "5585999990000" in call_kwargs["system_prompt"]


@pytest.mark.asyncio
async def test_projuris_agent_saves_person_id_after_tool_call(mock_llm):
    user_mem = AsyncMock(spec=UserMemory)

    mock_llm.generate_response.side_effect = [
        LLMResponse(
            content="",
            model="gpt-4o-mock",
            tool_calls=[{"name": "buscar_cliente", "arguments": {"query": "5585999990000"}}],
        ),
        LLMResponse(content="Encontrei seu cadastro.", model="gpt-4o-mock"),
    ]
    registry = AsyncMock(spec=ToolRegistry)
    registry.get_tool_schemas.return_value = [
        {"function": {"name": "buscar_cliente"}},
        {"function": {"name": "consultar_dados_cliente"}},
        {"function": {"name": "consultar_processos_cliente"}},
    ]
    registry.execute.return_value = {"results": [{"id": "P-77", "nome": "Maria"}], "count": 1}

    context = {"session_id": "5585999990000", "history": [], "session": {}, "user": {}}
    agent = ProjurisAgent(mock_llm, registry, user_mem)
    await agent.handle("Meus processos", context)

    user_mem.update.assert_called_once_with("5585999990000", projuris_person_id="P-77")
```

- [ ] **Step 3: Rodar testes e confirmar falha**

Run: `pytest tests/unit/test_agents.py -k projuris -v`
Expected: FAIL — `ModuleNotFoundError: modules.ai.agents.projuris_agent`

- [ ] **Step 4: Implementar o ProjurisAgent**

Criar `modules/ai/agents/projuris_agent.py`:

```python
from memory.user_memory import UserMemory
from modules.ai.agents.base_agent import AgentResponse, BaseAgent
from modules.ai.llm.client import LLMClient
from modules.ai.prompts.agent_prompts import PROJURIS_AGENT_PROMPT, build_user_context_block
from modules.ai.tools.registry import ToolRegistry
from observability.logger import get_logger
from observability.tracer import trace
from shared.constants import AgentName

_log = get_logger("projuris_agent")

_PROJURIS_TOOL_NAMES = {
    "buscar_cliente",
    "consultar_dados_cliente",
    "consultar_processos_cliente",
}


class ProjurisAgent(BaseAgent):
    def __init__(self, llm: LLMClient, tools: ToolRegistry, user_memory: UserMemory) -> None:
        self._llm = llm
        self._tools = tools
        self._user_memory = user_memory

    @property
    def name(self) -> str:
        return AgentName.PROJURIS

    @property
    def description(self) -> str:
        return "Identifica o cliente no projurisADV e consulta dados cadastrais e processos."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        session_id = context.get("session_id", "unknown")
        system_prompt = (
            PROJURIS_AGENT_PROMPT
            + build_user_context_block(context)
            + f"\n\n## TELEFONE DO CLIENTE\n- {session_id} (use em buscar_cliente)"
        )

        async with trace("projuris_agent.handle"):
            projuris_tools = [
                t for t in self._tools.get_tool_schemas()
                if t["function"]["name"] in _PROJURIS_TOOL_NAMES
            ]

            llm_response = await self._llm.generate_response(
                system_prompt=system_prompt,
                user_message=user_message,
                history=context.get("history", []),
                tools=projuris_tools,
            )

            if llm_response.tool_calls:
                tool_results = []
                for tc in llm_response.tool_calls:
                    result = await self._tools.execute(tc["name"], **tc["arguments"])
                    tool_results.append(result)
                    person_id = _extract_person_id(result)
                    if person_id:
                        await self._user_memory.update(
                            session_id, projuris_person_id=person_id
                        )

                enriched = (
                    user_message
                    + "\n\n[Dados do projurisADV:]\n"
                    + str(tool_results)
                )
                final = await self._llm.generate_response(
                    system_prompt=system_prompt,
                    user_message=enriched,
                    history=context.get("history", []),
                )
                return AgentResponse(
                    message=final.content,
                    tool_calls=llm_response.tool_calls,
                    metadata={"projuris_results": tool_results},
                )

        return AgentResponse(message=llm_response.content)


def _extract_person_id(result: dict) -> str | None:
    """Extrai o id da pessoa do resultado de buscar_cliente, se houver um único match."""
    results = result.get("results")
    if isinstance(results, list) and len(results) == 1:
        return results[0].get("id")
    return None
```

- [ ] **Step 5: Rodar testes e confirmar sucesso**

Run: `pytest tests/unit/test_agents.py -k projuris -v`
Expected: PASS (3 passed)

- [ ] **Step 6: Commit**

```bash
git add modules/ai/agents/projuris_agent.py modules/ai/prompts/agent_prompts.py tests/unit/test_agents.py
git commit -m "feat: add ProjurisAgent com auto-identificação por telefone"
```

---

## Task 5: Roteamento por intent

**Files:**
- Modify: `modules/ai/router.py` (dicts `_INTENT_TO_AGENT` e `_INTENT_TO_TEMPLATE`)
- Test: `tests/unit/test_agents.py` (adicionar teste de roteamento)

- [ ] **Step 1: Escrever o teste (deve falhar)**

Em `tests/unit/test_agents.py`, adicionar ao final:

```python
@pytest.mark.asyncio
async def test_router_maps_client_data_to_projuris(mock_llm, mock_registry):
    from modules.ai.router import IntentRouter
    from shared.constants import Intent

    user_mem = AsyncMock(spec=UserMemory)
    agent = ProjurisAgent(mock_llm, mock_registry, user_mem)
    router = IntentRouter([agent])

    routed = router.route(Intent.CLIENT_DATA)
    assert routed.name == AgentName.PROJURIS
```

- [ ] **Step 2: Rodar teste e confirmar falha**

Run: `pytest tests/unit/test_agents.py::test_router_maps_client_data_to_projuris -v`
Expected: FAIL — `AgentNotFoundError` (intent cai no fallback `faq_agent`, mas o faq_agent não está registrado neste router) ou retorna nome errado.

- [ ] **Step 3: Mapear o intent**

Em `modules/ai/router.py`, em `_INTENT_TO_AGENT`:

```python
    Intent.WORKFLOW: AgentName.WORKFLOW,
    Intent.CLIENT_DATA: AgentName.PROJURIS,
```

Em `_INTENT_TO_TEMPLATE` (sem template específico):

```python
    Intent.WORKFLOW: TemplateMessage.SOLICITACAO_DOCUMENTOS,
    Intent.CLIENT_DATA: None,
```

- [ ] **Step 4: Rodar teste e confirmar sucesso**

Run: `pytest tests/unit/test_agents.py::test_router_maps_client_data_to_projuris -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add modules/ai/router.py tests/unit/test_agents.py
git commit -m "feat: rotear intent client_data para projuris_agent"
```

---

## Task 6: Descrição do intent nos classificadores

**Files:**
- Modify: `modules/ai/llm/providers/openai_provider.py` (`_CLASSIFICATION_SYSTEM`)
- Modify: `modules/ai/llm/providers/anthropic_provider.py` (prompt de classificação)
- Modify: `modules/ai/llm/providers/deepseek_provider.py` (prompt de classificação)

> O enum de intents já é gerado dinamicamente de `Intent`, então o schema da função já inclui `client_data`. Falta só a descrição textual em cada prompt para o LLM saber quando usá-lo.

- [ ] **Step 1: openai_provider.py**

Em `_CLASSIFICATION_SYSTEM`, na lista de intenções, após a linha `workflow`:

```python
- workflow: processo multi-etapa como troca, cancelamento, reembolso
- client_data: dados cadastrais do cliente e lista de processos vinculados a ele
```

- [ ] **Step 2: anthropic_provider.py**

Localizar a linha `Intenções: faq | order_status | support | workflow` e trocar por:

```python
Intenções: faq | order_status | support | workflow | client_data
client_data = dados cadastrais do cliente e lista de processos vinculados a ele."""
```

(mantendo o fechamento da string que já existia — confirme a estrutura exata no arquivo ao editar.)

- [ ] **Step 3: deepseek_provider.py**

Na lista de intenções do prompt, após a linha `workflow`, adicionar:

```python
- client_data: dados cadastrais do cliente e lista de processos vinculados a ele
```

- [ ] **Step 4: Verificar imports dos providers**

Run: `python -c "import modules.ai.llm.providers.openai_provider, modules.ai.llm.providers.anthropic_provider, modules.ai.llm.providers.deepseek_provider; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add modules/ai/llm/providers/openai_provider.py modules/ai/llm/providers/anthropic_provider.py modules/ai/llm/providers/deepseek_provider.py
git commit -m "feat: descrever intent client_data nos classificadores de LLM"
```

---

## Task 7: Fiação (Dependency Injection)

**Files:**
- Modify: `api/dependencies.py`

- [ ] **Step 1: Adicionar imports**

No bloco de imports de `api/dependencies.py`, junto aos demais:

```python
from modules.ai.agents.projuris_agent import ProjurisAgent
from modules.ai.tools.projuris_search_person_tool import ProjurisSearchPersonTool
from modules.ai.tools.projuris_person_data_tool import ProjurisPersonDataTool
from modules.ai.tools.projuris_person_cases_tool import ProjurisPersonCasesTool
from modules.integrations.projuris.projuris_client import ProjurisClient
```

- [ ] **Step 2: Adicionar o singleton do client**

Após `get_erp_client()`:

```python
@lru_cache
def get_projuris_client() -> ProjurisClient:
    return ProjurisClient()
```

- [ ] **Step 3: Registrar tools em get_tool_registry**

Em `get_tool_registry`, dentro do `ToolRegistry([...])`, adicionar (após `TicketTool(support_service)`):

```python
    projuris = get_projuris_client()
    return ToolRegistry([
        SearchTool(knowledge_service),
        OrderTool(erp),
        TicketTool(support_service),
        ProjurisSearchPersonTool(projuris),
        ProjurisPersonDataTool(projuris),
        ProjurisPersonCasesTool(projuris),
    ])
```

- [ ] **Step 4: Registrar tools e agente em get_orchestrator**

Em `get_orchestrator`, no `ToolRegistry([...])`, adicionar as 3 tools (mesmo padrão acima, instanciando `projuris = get_projuris_client()` antes do registry). E na lista `agents`, adicionar:

```python
        ProjurisAgent(llm, registry, UserMemory(cache)),
```

- [ ] **Step 5: Verificar a fiação e rodar a suíte completa**

Run: `python -c "import api.dependencies; print('ok')"`
Expected: `ok`

Run: `pytest`
Expected: todos os testes passam (incluindo os novos de projuris).

- [ ] **Step 6: Lint**

Run: `ruff check . && ruff format --check .`
Expected: sem erros (rodar `ruff format .` se necessário).

- [ ] **Step 7: Commit**

```bash
git add api/dependencies.py
git commit -m "feat: registrar ProjurisClient, tools e ProjurisAgent na DI"
```

---

## Notas para ativação futura

Quando os dados reais e a documentação definitiva do projurisADV chegarem:

1. Preencher `.env`: `PROJURIS_BASE_URL`, `PROJURIS_API_KEY`.
2. Ajustar os paths em `modules/integrations/projuris/projuris_client.py` (constantes no topo) conforme os endpoints reais de `Pessoa` e `Processo`.
3. Validar o formato de resposta — se a API retornar wrappers (ex.: `{"items": [...]}`), normalizar dentro dos métodos do client e ajustar `_extract_person_id`.
4. Opcional: adicionar mocks de desenvolvimento se quiser testar o fluxo end-to-end sem o sistema real.
