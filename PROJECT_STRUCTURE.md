# 🤖 SAC AI — Tool-Driven Conversational AI Architecture

> Arquitetura Conversacional Orientada a Ferramentas para atendimento ao cliente com suporte a Multi-Agent.

---

## Visão Geral

Sistema de SAC inteligente construído em Python, seguindo princípios de **Clean Code**, **separação de responsabilidades** e **modularidade**. A arquitetura é dividida em 8 camadas independentes que se comunicam por interfaces bem definidas, permitindo evolução, testes e manutenção isolada de cada parte.

---

## Estrutura de Diretórios

```
sac-ai/
│
├── main.py                          # Entrypoint da aplicação
├── config/
│   ├── __init__.py
│   ├── settings.py                  # Variáveis de ambiente, configs gerais
│   └── logging_config.py            # Configuração de logging/observabilidade
│
├── modules/
│   │
│   ├── ai/                          # 🧠 CAMADA DE ORQUESTRAÇÃO DA IA
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # Orquestrador principal — interpreta intenção, despacha agentes
│   │   ├── router.py                # Roteador de intenções → decide qual agente acionar
│   │   │
│   │   ├── agents/                  # Multi-Agent — cada agente tem responsabilidade única
│   │   │   ├── __init__.py
│   │   │   ├── base_agent.py        # Classe abstrata base para todos os agentes
│   │   │   ├── faq_agent.py         # Agente de perguntas frequentes / base de conhecimento
│   │   │   ├── order_agent.py       # Agente de consulta de pedidos / status
│   │   │   ├── support_agent.py     # Agente de suporte / escalonamento humano
│   │   │   └── workflow_agent.py    # Agente de fluxos e processos multi-etapa
│   │   │
│   │   ├── prompts/                 # Templates de prompt organizados por contexto
│   │   │   ├── __init__.py
│   │   │   ├── system_prompts.py    # Prompts de sistema (persona, regras, tom)
│   │   │   ├── agent_prompts.py     # Prompts específicos de cada agente
│   │   │   └── templates.py         # Templates reutilizáveis com placeholders
│   │   │
│   │   ├── tools/                   # Ferramentas que a IA pode acionar
│   │   │   ├── __init__.py
│   │   │   ├── base_tool.py         # Interface/contrato base para tools
│   │   │   ├── search_tool.py       # Tool: busca na base de conhecimento
│   │   │   ├── order_tool.py        # Tool: consulta de pedidos via integração
│   │   │   ├── ticket_tool.py       # Tool: abertura de chamados
│   │   │   └── registry.py          # Registro centralizado de tools disponíveis
│   │   │
│   │   ├── guardrails/              # Regras de segurança e validação de saída
│   │   │   ├── __init__.py
│   │   │   ├── input_guard.py       # Validação/sanitização de entrada do usuário
│   │   │   ├── output_guard.py      # Validação da resposta da IA antes de enviar
│   │   │   └── content_filter.py    # Filtro de conteúdo sensível/inadequado
│   │   │
│   │   └── llm/                     # Integração com modelo de IA (LLM provider)
│   │       ├── __init__.py
│   │       ├── client.py            # Client genérico para chamadas ao LLM
│   │       ├── providers/
│   │       │   ├── __init__.py
│   │       │   ├── openai_provider.py
│   │       │   └── anthropic_provider.py
│   │       └── schemas.py           # Schemas de request/response do LLM
│   │
│   ├── conversations/               # 💬 CAMADA CONVERSACIONAL
│   │   ├── __init__.py
│   │   ├── models.py                # Modelos: Conversation, Message
│   │   ├── service.py               # Lógica de negócio de conversas
│   │   ├── repository.py            # Persistência de conversas e mensagens
│   │   └── schemas.py               # DTOs / schemas de entrada e saída
│   │
│   ├── knowledge/                   # 📚 CAMADA DE CONHECIMENTO
│   │   ├── __init__.py
│   │   ├── models.py                # Modelos: Document, FAQ, Embedding
│   │   ├── service.py               # Lógica de busca, indexação, RAG
│   │   ├── repository.py            # Persistência de documentos e embeddings
│   │   ├── embeddings.py            # Geração de embeddings (OpenAI, local, etc.)
│   │   ├── vector_store.py          # Interface com vector DB (Chroma, Pinecone, pgvector)
│   │   └── loader.py                # Ingestão de docs (PDF, TXT, Markdown, etc.)
│   │
│   ├── users/                       # 👤 CAMADA DE USUÁRIOS
│   │   ├── __init__.py
│   │   ├── models.py                # Modelos: User, Role, Permission
│   │   ├── service.py               # Lógica de autenticação, autorização, perfil
│   │   ├── repository.py            # Persistência de usuários
│   │   ├── auth.py                  # Autenticação (JWT, API Key, etc.)
│   │   └── schemas.py               # DTOs de usuário
│   │
│   ├── integrations/                # 🔌 CAMADA DE INTEGRAÇÃO
│   │   ├── __init__.py
│   │   ├── base_client.py           # Client HTTP base (retry, timeout, logging)
│   │   ├── erp/
│   │   │   ├── __init__.py
│   │   │   └── erp_client.py        # Client para ERP (SAP, TOTVS, etc.)
│   │   ├── crm/
│   │   │   ├── __init__.py
│   │   │   └── crm_client.py        # Client para CRM
│   │   ├── webhooks/
│   │   │   ├── __init__.py
│   │   │   └── webhook_handler.py   # Recepção e despacho de webhooks
│   │   └── adapters/
│   │       ├── __init__.py
│   │       └── adapter_interface.py # Interface para adaptadores de integração
│   │
│   ├── workflows/                   # ⚙️ CAMADA DE FLUXOS E AUTOMAÇÕES
│   │   ├── __init__.py
│   │   ├── models.py                # Modelos: Workflow, Step, Approval
│   │   ├── engine.py                # Motor de execução de fluxos multi-etapa
│   │   ├── service.py               # Lógica de negócio de workflows
│   │   └── repository.py            # Persistência de workflows
│   │
│   └── support/                     # 🎧 CAMADA DE SUPORTE / ESCALONAMENTO
│       ├── __init__.py
│       ├── models.py                # Modelos: Ticket, Protocol, Escalation
│       ├── service.py               # Lógica de criação de chamados, escalonamento
│       ├── repository.py            # Persistência de tickets
│       └── schemas.py               # DTOs de suporte
│
├── shared/                          # 🔧 CÓDIGO COMPARTILHADO
│   ├── __init__.py
│   ├── exceptions.py                # Exceções customizadas do projeto
│   ├── interfaces.py                # Interfaces/ABCs reutilizáveis
│   ├── utils.py                     # Funções utilitárias gerais
│   └── constants.py                 # Constantes globais
│
├── memory/                          # 🧠 CAMADA DE MEMÓRIA E CONTEXTO
│   ├── __init__.py
│   ├── session.py                   # Contexto da sessão atual
│   ├── history.py                   # Histórico de conversa (short-term)
│   ├── user_memory.py               # Preferências e dados persistentes do usuário
│   └── context_builder.py           # Montagem do contexto enviado ao LLM
│
├── observability/                   # 📊 CAMADA DE OBSERVABILIDADE
│   ├── __init__.py
│   ├── logger.py                    # Logger estruturado (JSON)
│   ├── metrics.py                   # Métricas de performance e uso
│   ├── tracer.py                    # Tracing de chamadas (tools, LLM, integrações)
│   └── audit.py                     # Auditoria de ações sensíveis
│
├── api/                             # 🌐 INTERFACE HTTP (FastAPI)
│   ├── __init__.py
│   ├── app.py                       # Criação da instância FastAPI
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py                  # POST /chat — endpoint principal do SAC
│   │   ├── conversations.py         # CRUD de conversas
│   │   ├── knowledge.py             # Upload/consulta de base de conhecimento
│   │   ├── webhooks.py              # Recepção de webhooks externos
│   │   └── health.py                # Health check
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── auth_middleware.py        # Middleware de autenticação
│   │   ├── logging_middleware.py     # Middleware de logging de requisições
│   │   └── rate_limit.py            # Rate limiting
│   └── dependencies.py              # Injeção de dependências (FastAPI Depends)
│
├── tests/                           # 🧪 TESTES
│   ├── __init__.py
│   ├── conftest.py                  # Fixtures compartilhadas
│   ├── unit/
│   │   ├── test_orchestrator.py
│   │   ├── test_agents.py
│   │   ├── test_tools.py
│   │   ├── test_guardrails.py
│   │   └── test_services.py
│   ├── integration/
│   │   ├── test_llm_client.py
│   │   ├── test_vector_store.py
│   │   └── test_integrations.py
│   └── e2e/
│       └── test_chat_flow.py
│
├── scripts/                         # 📜 SCRIPTS AUXILIARES
│   ├── seed_knowledge.py            # Popular base de conhecimento inicial
│   ├── migrate_db.py                # Migrations do banco
│   └── generate_embeddings.py       # Gerar embeddings de documentos
│
├── docker-compose.yml               # Serviços: app, postgres, redis, vector-db
├── Dockerfile
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## Mapeamento: Camadas da Arquitetura → Módulos

| # | Camada | Módulo(s) | Responsabilidade |
|---|--------|-----------|------------------|
| 1 | **Conversacional** | `modules/conversations/` + `api/routes/chat.py` | Gerenciar interação usuário ↔ IA, histórico, status |
| 2 | **Orquestração da IA** | `modules/ai/orchestrator.py` + `ai/router.py` + `ai/agents/` | Interpretar intenção, rotear para agente, montar resposta |
| 3 | **Ferramentas** | `modules/ai/tools/` | Ações controladas que a IA pode invocar |
| 4 | **Domínio** | `modules/workflows/` + `modules/users/` + services de cada módulo | Regras de negócio, validações, permissões |
| 5 | **Integração** | `modules/integrations/` | Comunicação com APIs, ERPs, CRMs, bancos externos |
| 6 | **Conhecimento** | `modules/knowledge/` | FAQ, RAG, busca vetorial, embeddings, documentos |
| 7 | **Memória e Contexto** | `memory/` | Sessão, histórico, preferências, context builder |
| 8 | **Observabilidade** | `observability/` | Logs, métricas, tracing, auditoria |

---

## Fluxo Principal (SAC)

```
Usuário envia mensagem
        │
        ▼
   ┌─────────┐
   │  API     │  POST /chat
   │ (FastAPI)│
   └────┬────┘
        │
        ▼
┌───────────────┐
│ Conversations │  Registra mensagem, carrega histórico
│   Service     │
└──────┬────────┘
       │
       ▼
┌──────────────┐
│   Memory /   │  Monta contexto: histórico + sessão + preferências
│   Context    │
│   Builder    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Guardrails   │  Valida/sanitiza input
│ (input_guard)│
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Orchestrator │  Envia ao LLM → interpreta intenção
│              │  Decide: qual agente? quais tools?
└──────┬───────┘
       │
       ├──► Agent (FAQ)       → Tool (search)      → Knowledge Service
       ├──► Agent (Order)     → Tool (order)        → Integration Client → ERP/API
       ├──► Agent (Support)   → Tool (ticket)       → Support Service
       └──► Agent (Workflow)  → Workflow Engine      → Multi-step process
              │
              ▼
       ┌──────────────┐
       │ Guardrails   │  Valida/filtra output
       │(output_guard)│
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │ Conversations │  Salva resposta
       │   Service     │
       └──────┬────────┘
              │
              ▼
        Resposta ao usuário
```

---

## Multi-Agent: Como Funciona

Cada agente é uma classe que herda de `BaseAgent` e implementa um contrato simples:

```python
# modules/ai/agents/base_agent.py

from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class AgentResponse:
    message: str
    tool_calls: list[dict] | None = None
    escalate: bool = False
    metadata: dict | None = None

class BaseAgent(ABC):
    """Contrato base para todos os agentes do SAC."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Identificador único do agente."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição do que o agente faz (usado pelo router)."""
        ...

    @abstractmethod
    async def handle(self, user_message: str, context: dict) -> AgentResponse:
        """Processa a mensagem e retorna a resposta."""
        ...
```

O **Router** decide qual agente acionar com base na intenção detectada:

```python
# modules/ai/router.py

class IntentRouter:
    """Roteia a intenção do usuário para o agente correto."""

    def __init__(self, agents: list[BaseAgent]):
        self._agents = {agent.name: agent for agent in agents}

    async def route(self, intent: str) -> BaseAgent:
        """Retorna o agente responsável pela intenção identificada."""
        mapping = {
            "faq": "faq_agent",
            "order_status": "order_agent",
            "support": "support_agent",
            "workflow": "workflow_agent",
        }
        agent_name = mapping.get(intent, "faq_agent")
        return self._agents[agent_name]
```

O **Orchestrator** coordena tudo:

```python
# modules/ai/orchestrator.py

class Orchestrator:
    """Orquestra o fluxo: LLM → intenção → agente → tools → resposta."""

    def __init__(self, llm_client, router, guardrails, context_builder):
        self._llm = llm_client
        self._router = router
        self._guardrails = guardrails
        self._context = context_builder

    async def process(self, user_message: str, session_id: str) -> str:
        # 1. Guardrail de entrada
        safe_input = self._guardrails.validate_input(user_message)

        # 2. Montar contexto
        context = await self._context.build(session_id)

        # 3. Detectar intenção via LLM
        intent = await self._llm.classify_intent(safe_input, context)

        # 4. Rotear para agente
        agent = await self._router.route(intent)

        # 5. Agente processa
        response = await agent.handle(safe_input, context)

        # 6. Guardrail de saída
        safe_output = self._guardrails.validate_output(response.message)

        return safe_output
```

---

## Tools: Contrato Base

```python
# modules/ai/tools/base_tool.py

from abc import ABC, abstractmethod

class BaseTool(ABC):
    """Contrato base para ferramentas que a IA pode acionar."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição usada pelo LLM para decidir quando usar a tool."""
        ...

    @property
    @abstractmethod
    def parameters_schema(self) -> dict:
        """JSON Schema dos parâmetros aceitos."""
        ...

    @abstractmethod
    async def execute(self, **params) -> dict:
        """Executa a tool e retorna o resultado."""
        ...
```

---

## Princípios de Clean Code Aplicados

1. **Single Responsibility**: cada arquivo/classe tem uma única razão para mudar.
2. **Dependency Inversion**: módulos dependem de abstrações (`BaseAgent`, `BaseTool`, `BaseClient`), não de implementações concretas.
3. **Interface Segregation**: contratos pequenos e específicos por responsabilidade.
4. **Open/Closed**: novos agentes e tools são adicionados sem alterar o código existente — basta registrar no router/registry.
5. **Naming claro**: nomes descritivos, sem abreviações obscuras, sem comentários desnecessários.
6. **Testabilidade**: cada camada pode ser testada isoladamente com mocks das dependências.
7. **Separação config/código**: variáveis de ambiente em `config/settings.py`, nunca hardcoded.

---

## Stack Sugerida

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.11+ |
| Framework HTTP | FastAPI |
| LLM Client | OpenAI SDK / Anthropic SDK |
| Vector Store | ChromaDB / pgvector / Pinecone |
| Banco de dados | PostgreSQL |
| Cache/Sessão | Redis |
| Embeddings | OpenAI `text-embedding-3-small` ou modelo local |
| Testes | pytest + pytest-asyncio |
| Linting | ruff |
| Containerização | Docker + Docker Compose |
| Observabilidade | structlog + OpenTelemetry (opcional) |

---

## Como Adicionar um Novo Agente

1. Crie o arquivo em `modules/ai/agents/meu_agent.py`
2. Herde de `BaseAgent` e implemente `name`, `description` e `handle`
3. Se o agente precisar de tools, crie-as em `modules/ai/tools/` herdando de `BaseTool`
4. Registre as tools no `registry.py`
5. Adicione o mapeamento de intenção no `router.py`
6. Escreva testes em `tests/unit/test_agents.py`

## Como Adicionar uma Nova Integração

1. Crie o client em `modules/integrations/<sistema>/`
2. Herde de `base_client.py` para herdar retry, timeout e logging
3. Crie a tool correspondente em `modules/ai/tools/` que chama o client
4. Registre no `registry.py`

---

## Permissões por Perfil

| Perfil | Acesso |
|--------|--------|
| **Usuário comum** | Consultas básicas, FAQ, status de pedido |
| **Gestor** | Relatórios, métricas, aprovações de workflow |
| **Admin** | Configurar integrações, gerenciar base de conhecimento, acessar auditoria |

---

## Próximos Passos

- [ ] Inicializar projeto com `main.py` + FastAPI
- [ ] Implementar `BaseAgent` e primeiro agente (FAQ)
- [ ] Configurar LLM client (escolher provider)
- [ ] Montar `Orchestrator` com router básico
- [ ] Configurar vector store para base de conhecimento
- [ ] Adicionar guardrails de input/output
- [ ] Setup Docker Compose (app + postgres + redis + chroma)
- [ ] Implementar camada de observabilidade
- [ ] Testes unitários dos agentes e tools
