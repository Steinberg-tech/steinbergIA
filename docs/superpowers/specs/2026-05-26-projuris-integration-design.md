# Integração projurisADV — Pessoas/Clientes

**Data:** 2026-05-26
**Status:** Aprovado — pronto para plano de implementação

## Objetivo

Deixar a estrutura de integração da IA (SAC AI) com o sistema **projurisADV** (SajAdv REST API) montada e configurada, pronta para ativação quando os dados reais do escritório chegarem ao sistema. O escopo inicial é o recurso **Pessoas/Clientes**, com três capacidades:

1. Buscar cliente por nome / CPF / telefone
2. Consultar dados cadastrais do cliente
3. Consultar processos vinculados ao cliente

## Contexto e Decisões

- **Canal:** WhatsApp via Digisac (já integrado no projeto).
- **Autenticação:** token único do escritório (firm-level), configurado no `.env`. A IA age sempre com as permissões do escritório.
- **Sem dados mockados.** Se a integração não estiver configurada, os métodos lançam `IntegrationError` com mensagem clara, em vez de retornar dados falsos. (Mocks podem ser adicionados depois sob demanda.)
- **Identidade = telefone / `session_id`** (modelo de mensageria, sem login). O agente usa o telefone do contexto para identificar o cliente automaticamente, sem pedir CPF.
- **Distinção do intent `order_status` existente:** `order_status` cobre "andamento de um processo específico"; o novo intent `client_data` cobre "quem é o cliente, seus dados cadastrais e a lista de processos dele". Os prompts deixam essa fronteira explícita para evitar sobreposição.
- **Paths dos endpoints centralizados** como constantes no topo do `projuris_client.py`, para ajuste rápido quando a documentação real do cliente chegar.

## Arquitetura (Opção A escolhida)

Segue o padrão existente do projeto: um cliente de integração por sistema, tools finas por ação, um agente por domínio, roteamento por intent.

```
Cliente (WhatsApp/Digisac) → Orchestrator → classify_intent=client_data
  → IntentRouter → ProjurisAgent → Tools (buscar_cliente / consultar_dados / consultar_processos)
  → ProjurisClient → projurisADV REST API
```

## Componentes

### 1. Configuração — `config/settings.py`

Adicionar (padrão idêntico a ERP/CRM):

```python
projuris_base_url: str = ""
projuris_api_key: str = ""
projuris_timeout_seconds: int = 10
```

### 2. Cliente de integração — `modules/integrations/projuris/projuris_client.py`

`ProjurisClient(BaseClient)`. Sem mock. Paths como constantes no topo do módulo.

Se `settings.projuris_base_url` estiver vazio, cada método lança
`IntegrationError("projurisADV não configurado — defina PROJURIS_BASE_URL no .env")`.

| Método | Recurso projurisADV (path a confirmar) | Retorno |
|--------|----------------------------------------|---------|
| `search_person(query: str)` | `Pessoa` — busca por nome/CPF/telefone | `list[dict]` (id, nome, cpf) |
| `get_person(person_id: str)` | `Pessoa` — dados cadastrais | `dict` |
| `get_person_cases(person_id: str)` | `Processo` filtrado por pessoa | `list[dict]` |

### 3. Tools — `modules/ai/tools/`

Cada tool é fina, envolve um método do client, usa `trace` e propaga erro como `IntegrationError` (padrão de `OrderTool`).

| Arquivo | `name` (LLM) | Parâmetros | Descrição |
|---------|--------------|------------|-----------|
| `projuris_search_person_tool.py` | `buscar_cliente` | `query: str` | Busca cliente por nome, CPF ou telefone |
| `projuris_person_data_tool.py` | `consultar_dados_cliente` | `person_id: str` | Dados cadastrais (CPF, endereço, contatos) |
| `projuris_person_cases_tool.py` | `consultar_processos_cliente` | `person_id: str` | Lista de processos vinculados |

Fluxo esperado pelo LLM: `buscar_cliente` → `person_id` → `consultar_dados_cliente` e/ou `consultar_processos_cliente`.

### 4. Agente — `modules/ai/agents/projuris_agent.py`

`ProjurisAgent(BaseAgent)`, seguindo o padrão do `OrderAgent`:

- Recebe `llm`, `tools` (registry), `user_memory`.
- Injeta o telefone do contexto no system prompt para que o LLM chame `buscar_cliente` automaticamente, sem pedir CPF.
- Expõe ao LLM apenas as 3 tools projuris.
- Após identificar o cliente, persiste o `person_id` no `UserMemory` (análogo a `remember_last_order`), evitando re-busca em mensagens seguintes.

### 5. Constantes — `shared/constants.py`

```python
# em Intent
CLIENT_DATA = "client_data"
# em AgentName
PROJURIS = "projuris_agent"
```

### 6. Roteamento — `modules/ai/router.py`

Mapear `Intent.CLIENT_DATA → AgentName.PROJURIS` em `_INTENT_TO_AGENT`.
Definir template associado em `_INTENT_TO_TEMPLATE` (ou `None`).

### 7. Prompts

- `modules/ai/prompts/agent_prompts.py`: adicionar `PROJURIS_AGENT_PROMPT` (especialidade: identificar o cliente e responder sobre dados cadastrais e processos; usar telefone do contexto; não pedir CPF se já identificado).
- Classificadores de intent (descrição do novo intent `client_data`) em:
  - `modules/ai/llm/providers/openai_provider.py`
  - `modules/ai/llm/providers/anthropic_provider.py`
  - `modules/ai/llm/providers/deepseek_provider.py`

  O enum de intents é gerado dinamicamente de `Intent`, então o schema já inclui o novo valor; só falta a descrição textual no prompt de classificação.

### 8. Fiação (DI) — `api/dependencies.py`

- `get_projuris_client()` com `@lru_cache` (padrão de `get_erp_client`).
- Registrar as 3 tools no `ToolRegistry` em **ambos** os pontos: `get_tool_registry` e `get_orchestrator`.
- Adicionar `ProjurisAgent(llm, registry, UserMemory(cache))` à lista de agentes em `get_orchestrator`.

## Tratamento de Erro

- projurisADV não configurado → `IntegrationError` clara; o agente responde algo como *"Ainda não consigo acessar o sistema de processos — integração em configuração"* em vez de quebrar.
- `ToolExecutionError` já é capturada pelo `ToolRegistry`.
- O `Orchestrator` já tem fallback via `try/except SACBaseError` retornando `FALLBACK_MESSAGE`.

## Testes (`tests/unit/`)

- `test_projuris_client.py` — métodos lançam `IntegrationError` quando não configurado; montam path/params corretos quando configurado (mock de `httpx`/`_get`).
- `test_projuris_tools.py` — cada tool chama o método certo e propaga erro.
- `test_agents.py` (estender) — `ProjurisAgent` injeta telefone no contexto, executa tool, persiste `person_id`.
- `test_router.py` (estender) — `client_data` roteia para `projuris_agent`.

## Arquivos

**Novos (≈7):** `modules/integrations/projuris/projuris_client.py`, 3 tools, `modules/ai/agents/projuris_agent.py`, `tests/unit/test_projuris_client.py`, `tests/unit/test_projuris_tools.py`.

**Editados (≈8):** `config/settings.py`, `shared/constants.py`, `modules/ai/router.py`, `modules/ai/prompts/agent_prompts.py`, `api/dependencies.py`, os 3 providers de LLM, e os testes existentes `test_router.py` / `test_agents.py`.

## Fora de Escopo

- Tarefas, Financeiro, Andamentos, Intimações (recursos futuros do projurisADV).
- Criação/atualização de cadastro de pessoa (somente leitura nesta fase).
- Dados mockados (adicionar sob demanda).
- Token por usuário individual (mantido firm-level).
