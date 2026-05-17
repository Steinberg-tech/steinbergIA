# SAC AI — Atendimento ao Cliente com IA

Sistema de SAC inteligente orientado a ferramentas, com arquitetura Multi-Agent. Projetado para receber mensagens de plataformas externas (WhatsApp, widget, API), classificar a intenção do cliente e acionar o agente especializado mais adequado para gerar a melhor resposta.

---

## Visão Geral

```
Plataforma (WhatsApp, Widget...)
        │
        ▼
   POST /chat  ou  POST /webhooks/{platform}
        │
        ▼
 ConversationService  →  ContextBuilder (histórico + sessão + usuário)
        │
        ▼
   InputGuard  →  Orchestrator  →  classify_intent (LLM)
                       │
              IntentRouter decide o agente
                       │
        ┌──────────────┼──────────────┐──────────────┐
        ▼              ▼              ▼              ▼
   FAQAgent      OrderAgent    SupportAgent  WorkflowAgent
   search_tool   order_tool    ticket_tool   (multi-etapa)
        │              │              │
   KnowledgeDB      ERP/CRM      SupportDB
                       │
                  OutputGuard  →  resposta ao cliente
```

---

## Stack

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Framework HTTP | FastAPI |
| LLM (padrão) | OpenAI GPT-4o |
| LLM (alternativo) | Anthropic Claude Sonnet |
| Banco de dados | PostgreSQL (SQLAlchemy 2.x async) |
| Cache / Sessão | Redis |
| Vector Store | ChromaDB |
| Embeddings | OpenAI `text-embedding-3-small` |
| Observabilidade | structlog (JSON estruturado) |
| Testes | pytest + pytest-asyncio |
| Linting | ruff |
| Containerização | Docker + Docker Compose |

---

## Início Rápido

### Com Docker (recomendado)

```bash
# 1. Clone e entre no diretório
cd Steinberg

# 2. Configure o ambiente
cp .env.example .env
# Por padrão, LLM_PROVIDER=mock — funciona sem API keys

# 3. Suba todos os serviços
docker-compose up --build

# 4. Rode as migrations
docker-compose exec app python scripts/migrate_db.py

# 5. Popule a base de conhecimento
docker-compose exec app python scripts/seed_knowledge.py
```

### Sem Docker (desenvolvimento local)

```bash
# Instale as dependências
pip install -r requirements.txt

# Configure o ambiente
cp .env.example .env
# Ajuste DATABASE_URL, REDIS_URL, CHROMA_HOST para localhost

python scripts/migrate_db.py
uvicorn api.app:app --reload
```

### Teste a API

```bash
# Health check
curl http://localhost:8000/health

# Enviar mensagem (modo mock — sem API key)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual o prazo de entrega?", "session_id": "5511999999999"}'

# Consultar pedido
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Qual o status do pedido 12345?", "session_id": "5511999999999"}'
```

---

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `LLM_PROVIDER` | `mock` / `openai` / `anthropic` | `mock` |
| `OPENAI_API_KEY` | Chave da OpenAI | — |
| `ANTHROPIC_API_KEY` | Chave da Anthropic | — |
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql+asyncpg://sac:sac@postgres:5432/sac_ai` |
| `REDIS_URL` | URL de conexão Redis | `redis://redis:6379/0` |
| `CHROMA_HOST` | Host do ChromaDB | `chromadb` |
| `ERP_BASE_URL` | URL do ERP (vazio = modo mock) | — |
| `CRM_BASE_URL` | URL do CRM (vazio = modo mock) | — |

> **Modo mock**: quando `LLM_PROVIDER=mock` ou API keys estão vazias, o sistema usa respostas simuladas — ideal para desenvolvimento local e testes.

---

## Arquitetura por Módulo

### `api/` — Interface HTTP (FastAPI)

Ponto de entrada da aplicação. Define as rotas, middlewares e injeção de dependências.

| Arquivo | Responsabilidade |
|---|---|
| `app.py` | Instância FastAPI, registro de middlewares e routers |
| `dependencies.py` | Fábrica de todas as dependências via `Depends()` — orquestrador, serviços, LLM, Redis |
| `routes/chat.py` | `POST /chat` — endpoint principal, recebe mensagem e retorna resposta da IA |
| `routes/conversations.py` | `GET /conversations/{session_id}` — histórico de conversas |
| `routes/knowledge.py` | `POST /knowledge/documents` e `POST /knowledge/search` — gerencia base de conhecimento |
| `routes/webhooks.py` | `POST /webhooks/{platform}` — recebe eventos do WhatsApp e outras plataformas |
| `routes/health.py` | `GET /health` e `GET /metrics` — monitoramento |
| `middleware/logging_middleware.py` | Log estruturado de todas as requisições com tempo de resposta |
| `middleware/rate_limit.py` | Limite de requisições por `session_id` (sliding window) |

---

### `modules/ai/` — Camada de Orquestração da IA

O núcleo inteligente do sistema. Contém o pipeline completo de processamento de mensagens.

#### `orchestrator.py`
Coordena todo o fluxo: recebe a mensagem, valida, monta contexto, classifica intenção, aciona o agente certo, valida a saída e retorna a resposta final.

```
process(user_message, session_id)
  1. InputGuard.validate()
  2. ContextBuilder.build()
  3. LLM.classify_intent()
  4. IntentRouter.route()
  5. agent.handle()
  6. [executa tool_calls se houver]
  7. OutputGuard.validate()
  → retorna (texto_final, AgentResponse)
```

#### `router.py`
`IntentRouter` mapeia a intenção classificada pelo LLM para o agente responsável:

| Intenção | Agente |
|---|---|
| `faq` | `FAQAgent` |
| `order_status` | `OrderAgent` |
| `support` | `SupportAgent` |
| `workflow` | `WorkflowAgent` |

#### `agents/`
Cada agente tem responsabilidade única e implementa o contrato `BaseAgent`:

| Agente | Especialidade | Tool principal |
|---|---|---|
| `FAQAgent` | Dúvidas frequentes, políticas, informações gerais | `search_knowledge` |
| `OrderAgent` | Status de pedido, rastreio, previsão de entrega | `get_order_status` |
| `SupportAgent` | Reclamações, abertura de chamado, escalação | `create_ticket` |
| `WorkflowAgent` | Fluxos multi-etapa: troca, cancelamento, reembolso, devolução | SessionMemory |

#### `tools/`
Ações concretas que a IA pode executar. Cada tool segue o contrato `BaseTool` e é registrada no `ToolRegistry`, que expõe os schemas no formato OpenAI function calling.

| Tool | O que faz |
|---|---|
| `SearchTool` | Busca semântica na base de conhecimento (ChromaDB) |
| `OrderTool` | Consulta status de pedido no ERP |
| `TicketTool` | Abre chamado no sistema de suporte e gera protocolo |

#### `guardrails/`
Camada de segurança que protege a entrada e a saída da IA:

- **`InputGuard`** — valida tamanho da mensagem, detecta tentativas de prompt injection e termos bloqueados
- **`OutputGuard`** — remove PII (CPF, telefone, e-mail) da resposta, bloqueia vazamento de dados sensíveis
- **`ContentFilter`** — filtro de palavras e padrões regex maliciosos

#### `llm/`
Abstração sobre os provedores de LLM. Troca de provider sem alterar o resto do sistema:

| Provider | Uso |
|---|---|
| `OpenAIProvider` | GPT-4o com function calling para classificação de intenção |
| `AnthropicProvider` | Claude Sonnet como alternativa |
| `MockProvider` | Respostas simuladas para desenvolvimento sem API key |

#### `prompts/`
Templates de prompt organizados por contexto. Separa a lógica de prompt do código de negócio, facilitando ajustes de tom e comportamento sem alterar os agentes.

---

### `modules/conversations/` — Camada Conversacional

Gerencia o ciclo de vida das conversas e o histórico de mensagens.

| Arquivo | Responsabilidade |
|---|---|
| `models.py` | ORM: `Conversation` (sessão, plataforma, status) + `Message` (role, conteúdo, agente) |
| `repository.py` | Queries async no PostgreSQL — buscar, criar, salvar mensagens |
| `service.py` | `ConversationService`: get-or-create de conversa, salvar mensagens, escalação |
| `schemas.py` | Pydantic DTOs: `ChatRequest`, `ChatResponse`, `MessageSchema` |

A conversa é identificada pelo `session_id` (número de telefone, ID externo da plataforma). Não há login — a identidade vem do canal.

---

### `memory/` — Camada de Memória e Contexto

Monta o contexto rico enviado ao LLM antes de cada resposta. Combina três fontes:

| Arquivo | O que armazena | Backend |
|---|---|---|
| `history.py` | Últimas N mensagens da conversa | PostgreSQL (via ConversationService) |
| `session.py` | Estado temporário da sessão (etapa do workflow, última intenção) | Redis (TTL: 1h) |
| `user_memory.py` | Dados persistentes do contato (nome, último pedido, preferências) | Redis (TTL: 30 dias) |
| `context_builder.py` | `ContextBuilder.build(session_id)` — agrega as três fontes em um único dict | — |

---

### `modules/knowledge/` — Base de Conhecimento

Gerencia documentos, FAQ e busca semântica via RAG (Retrieval-Augmented Generation).

| Arquivo | Responsabilidade |
|---|---|
| `embeddings.py` | Gera vetores de texto usando OpenAI `text-embedding-3-small` |
| `vector_store.py` | Interface com ChromaDB — indexar e buscar por similaridade cosine |
| `loader.py` | Ingestão de documentos: `.txt`, `.md`, `.jsonl` |
| `service.py` | `KnowledgeService`: indexar documento + gerar embedding + buscar |
| `repository.py` | Persiste metadados dos documentos no PostgreSQL |

---

### `modules/support/` — Sistema de Chamados

Criação e gerenciamento de tickets de suporte com número de protocolo único.

| Arquivo | Responsabilidade |
|---|---|
| `models.py` | ORM: `Ticket` (protocolo, sessão, assunto, prioridade, status) |
| `service.py` | `SupportService.create_ticket()` — gera protocolo `SAC-YYYYMMDDHHMMSS-XXXXXX` |
| `repository.py` | Persistência de tickets no PostgreSQL |
| `schemas.py` | Pydantic DTOs de entrada e saída |

---

### `modules/workflows/` — Motor de Fluxos Multi-Etapa

Gerencia processos conversacionais com múltiplas etapas que precisam de estado persistente.

| Arquivo | Responsabilidade |
|---|---|
| `models.py` | ORM: `Workflow` (tipo, status, etapa atual, dados coletados) + `WorkflowStep` |
| `engine.py` | Define as etapas de cada fluxo e avança/conclui o processo |
| `service.py` | `WorkflowService`: iniciar e avançar fluxos |
| `repository.py` | Persistência no PostgreSQL |

Fluxos disponíveis: `troca`, `cancelamento`, `reembolso`, `devolucao`.

---

### `modules/integrations/` — Integrações Externas

Clientes HTTP para sistemas externos. Todos herdam de `BaseClient` que fornece retry automático (3 tentativas), timeout configurável e logging estruturado.

| Módulo | Responsabilidade |
|---|---|
| `base_client.py` | HTTP base com `tenacity` retry + timeout + log de erros |
| `erp/erp_client.py` | Consulta pedidos no ERP (SAP, TOTVS, etc.) — fallback para mock se URL não configurada |
| `crm/crm_client.py` | Busca dados do cliente no CRM — fallback para mock |
| `webhooks/webhook_handler.py` | Normaliza payloads de diferentes plataformas (WhatsApp, genérico) para formato interno |
| `adapters/adapter_interface.py` | Interface para adaptadores — conversão entre formato externo e interno |

---

### `observability/` — Observabilidade

Logging, métricas e auditoria centralizados.

| Arquivo | Responsabilidade |
|---|---|
| `logger.py` | Logger structlog (JSON estruturado) — acessado via `get_logger("nome")` |
| `tracer.py` | Context manager `async with trace("operação")` — mede duração e loga resultado |
| `metrics.py` | Contadores e histogramas em memória — acessíveis em `GET /metrics` |
| `audit.py` | `log_event()` — registra ações sensíveis (ticket criado, escalação, etc.) |

---

### `shared/` — Código Compartilhado

Utilitários e contratos usados por todas as camadas.

| Arquivo | O que contém |
|---|---|
| `exceptions.py` | Hierarquia de exceções do projeto (`InputValidationError`, `ToolExecutionError`, etc.) |
| `constants.py` | Enums: `Intent`, `AgentName`, `MessageRole`, `Platform`, `ConversationStatus` |
| `utils.py` | `generate_id()`, `generate_protocol()`, `strip_pii_patterns()`, `truncate()` |
| `interfaces.py` | ABCs: `Repository`, `CacheBackend` |

---

### `config/` — Configuração

| Arquivo | Responsabilidade |
|---|---|
| `settings.py` | `Settings` via `pydantic-settings` — lê todas as env vars com validação de tipos |
| `logging_config.py` | `configure_logging()` — configura structlog com JSON renderer e stdlib factory |

---

### `scripts/` — Scripts Auxiliares

| Script | O que faz |
|---|---|
| `migrate_db.py` | Cria todas as tabelas no PostgreSQL via SQLAlchemy metadata |
| `seed_knowledge.py` | Popula a base de conhecimento com FAQ inicial (6 documentos de exemplo) |
| `generate_embeddings.py` | Regenera embeddings de todos os documentos (útil ao trocar de modelo) |

---

## Testes

```bash
# Todos os testes unitários (sem API keys, sem DB)
pytest tests/unit/

# Testes de integração (requer serviços rodando)
pytest tests/integration/

# Teste e2e (API completa com mocks)
pytest tests/e2e/

# Todos de uma vez
pytest
```

| Suite | O que testa |
|---|---|
| `test_orchestrator.py` | Pipeline completo com LLM mockado — guardrails, roteamento, resposta |
| `test_agents.py` | Cada agente isolado com tool calls simulados |
| `test_tools.py` | Cada tool isolada — contratos, execução, erros |
| `test_guardrails.py` | Input/output guard — bloqueios, sanitização, edge cases |
| `test_services.py` | ConversationService — get-or-create, histórico, escalação |
| `test_chat_flow.py` | E2E: `POST /chat` com dependency override — resposta HTTP, campos obrigatórios |
| `test_integrations.py` | ERP e CRM em modo mock — sem endpoints reais |
| `test_llm_client.py` | Providers reais (skippado sem API key) |

---

## Como Estender

### Novo agente

```python
# modules/ai/agents/meu_agent.py
from modules.ai.agents.base_agent import BaseAgent, AgentResponse

class MeuAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "meu_agent"

    @property
    def description(self) -> str:
        return "O que este agente faz."

    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        ...
        return AgentResponse(message="resposta")
```

Depois: adicionar em `shared/constants.py` (`AgentName`), registrar no `router.py` e instanciar em `api/dependencies.py`.

### Nova tool

```python
# modules/ai/tools/minha_tool.py
from modules.ai.tools.base_tool import BaseTool

class MinhaTool(BaseTool):
    @property
    def name(self) -> str:
        return "minha_tool"

    @property
    def description(self) -> str:
        return "Descrição para o LLM decidir quando usar."

    @property
    def parameters_schema(self) -> dict:
        return {"type": "object", "properties": {"param": {"type": "string"}}, "required": ["param"]}

    async def execute(self, param: str) -> dict:
        return {"resultado": ...}
```

Depois: registrar no `ToolRegistry` em `api/dependencies.py`.

### Nova integração

```python
# modules/integrations/meu_sistema/client.py
from modules.integrations.base_client import BaseClient

class MeuSistemaClient(BaseClient):
    async def get_dados(self, id: str) -> dict:
        return await self._get(f"/endpoint/{id}")
```

---

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Status da aplicação |
| `GET` | `/metrics` | Contadores e histogramas internos |
| `POST` | `/chat` | Endpoint principal — processa mensagem e retorna resposta da IA |
| `GET` | `/conversations/{session_id}` | Lista conversas de uma sessão |
| `GET` | `/conversations/{session_id}/history` | Histórico de mensagens |
| `DELETE` | `/conversations/{id}` | Marca conversa como resolvida |
| `POST` | `/knowledge/documents` | Indexa novo documento na base de conhecimento |
| `GET` | `/knowledge/documents` | Lista documentos indexados |
| `POST` | `/knowledge/search` | Busca semântica na base de conhecimento |
| `POST` | `/webhooks/{platform}` | Recebe eventos de plataformas externas |

> Documentação interativa disponível em `http://localhost:8000/docs` quando `DEBUG=true`.

---

## Comandos

```bash
uvicorn api.app:app --reload      # servidor de desenvolvimento
pytest                            # rodar todos os testes
pytest tests/unit/                # apenas unitários
ruff check .                      # lint
ruff format .                     # formatação
python scripts/migrate_db.py      # criar tabelas
python scripts/seed_knowledge.py  # popular FAQ inicial
python scripts/generate_embeddings.py  # regenerar embeddings
docker-compose up                 # subir toda a stack
```
