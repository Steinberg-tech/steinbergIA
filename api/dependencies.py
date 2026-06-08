from functools import lru_cache
from typing import Annotated, AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings
from memory.context_builder import ContextBuilder
from memory.history import HistoryMemory
from memory.session import SessionMemory
from memory.user_memory import UserMemory
from modules.ai.agents.faq_agent import FAQAgent
from modules.ai.agents.order_agent import OrderAgent
from modules.ai.agents.process_agent import ProcessAgent
from modules.ai.agents.support_agent import SupportAgent
from modules.ai.agents.workflow_agent import WorkflowAgent
from modules.ai.guardrails.content_filter import ContentFilter
from modules.ai.guardrails.input_guard import InputGuard
from modules.ai.guardrails.output_guard import OutputGuard
from modules.ai.orchestrator import Orchestrator
from modules.ai.router import IntentRouter
from modules.ai.tools.order_tool import OrderTool
from modules.ai.tools.process_tool import ProcessTool
from modules.ai.tools.registry import ToolRegistry
from modules.ai.tools.search_tool import SearchTool
from modules.ai.tools.ticket_tool import TicketTool
from modules.conversations.repository import ConversationRepository
from modules.conversations.service import ConversationService
from modules.integrations.erp.erp_client import ERPClient
from modules.integrations.projuris.identity import ProjurisIdentityService
from modules.integrations.projuris.projuris_client import ProjurisClient
from modules.knowledge.embeddings import EmbeddingGenerator
from modules.knowledge.repository import KnowledgeRepository
from modules.knowledge.service import KnowledgeService
from modules.knowledge.vector_store import VectorStore
from modules.support.repository import SupportRepository
from modules.support.service import SupportService
from modules.workflows.engine import WorkflowEngine
from modules.workflows.repository import WorkflowRepository
from shared.interfaces import CacheBackend


# ─── DB Engine ────────────────────────────────────────────────────────────────

_engine = create_async_engine(settings.database_url, echo=settings.debug, pool_pre_ping=True)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with _session_factory() as session:
        async with session.begin():
            yield session


# ─── Redis cache adapter ───────────────────────────────────────────────────────

class _RedisCache(CacheBackend):
    def __init__(self, client: aioredis.Redis) -> None:
        self._r = client

    async def get(self, key: str) -> str | None:
        val = await self._r.get(key)
        return val.decode() if val else None

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self._r.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._r.delete(key)


@lru_cache
def _get_redis() -> aioredis.Redis:
    return aioredis.from_url(settings.redis_url, decode_responses=False)


def get_cache() -> CacheBackend:
    return _RedisCache(_get_redis())


# ─── LLM Provider ─────────────────────────────────────────────────────────────

@lru_cache
def get_llm_client():
    if settings.llm_provider == "mock":
        from modules.ai.llm.providers.mock_provider import MockProvider
        return MockProvider()
    if settings.llm_provider == "anthropic":
        if not settings.anthropic_api_key:
            from modules.ai.llm.providers.mock_provider import MockProvider
            return MockProvider()
        from modules.ai.llm.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider()
    if settings.llm_provider == "deepseek":
        if not settings.deepseek_api_key:
            from modules.ai.llm.providers.mock_provider import MockProvider
            return MockProvider()
        from modules.ai.llm.providers.deepseek_provider import DeepSeekProvider
        return DeepSeekProvider()
    if not settings.openai_api_key:
        from modules.ai.llm.providers.mock_provider import MockProvider
        return MockProvider()
    from modules.ai.llm.providers.openai_provider import OpenAIProvider
    return OpenAIProvider()


# ─── Infrastructure singletons ────────────────────────────────────────────────

@lru_cache
def get_erp_client() -> ERPClient:
    return ERPClient()


@lru_cache
def get_projuris_client() -> ProjurisClient:
    return ProjurisClient(
        cache=get_cache(),
        base_url=settings.projuris_base_url,
        service_url=settings.projuris_service_url,
        username=settings.projuris_username,
        password=settings.projuris_password,
        client_id=settings.projuris_client_id,
        client_secret=settings.projuris_client_secret,
        timeout=settings.projuris_timeout_seconds,
    )


@lru_cache
def get_vector_store() -> VectorStore:
    return VectorStore()


@lru_cache
def get_embedding_generator() -> EmbeddingGenerator:
    return EmbeddingGenerator()


# ─── Services ─────────────────────────────────────────────────────────────────

def get_conversation_service(db: Annotated[AsyncSession, Depends(get_db)]) -> ConversationService:
    return ConversationService(ConversationRepository(db))


def get_knowledge_service(db: Annotated[AsyncSession, Depends(get_db)]) -> KnowledgeService:
    return KnowledgeService(
        repo=KnowledgeRepository(db),
        vector_store=get_vector_store(),
        embeddings=get_embedding_generator(),
    )


def get_support_service(db: Annotated[AsyncSession, Depends(get_db)]) -> SupportService:
    return SupportService(SupportRepository(db))


# ─── Memory ───────────────────────────────────────────────────────────────────

def get_session_memory(cache: Annotated[CacheBackend, Depends(get_cache)]) -> SessionMemory:
    return SessionMemory(cache, ttl=settings.session_ttl_seconds)


def get_user_memory(cache: Annotated[CacheBackend, Depends(get_cache)]) -> UserMemory:
    return UserMemory(cache)


def get_projuris_identity_service(
    cache: Annotated[CacheBackend, Depends(get_cache)],
) -> ProjurisIdentityService:
    return ProjurisIdentityService(get_projuris_client(), UserMemory(cache))


def get_context_builder(
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[CacheBackend, Depends(get_cache)],
) -> ContextBuilder:
    conv_service = ConversationService(ConversationRepository(db))
    history = HistoryMemory(conv_service, settings.history_max_messages)
    session_mem = SessionMemory(cache, settings.session_ttl_seconds)
    user_mem = UserMemory(cache)
    return ContextBuilder(history, session_mem, user_mem)


# ─── Tools & Registry ─────────────────────────────────────────────────────────

def get_tool_registry(
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    support_service: Annotated[SupportService, Depends(get_support_service)],
) -> ToolRegistry:
    erp = get_erp_client()
    return ToolRegistry([
        SearchTool(knowledge_service),
        OrderTool(erp),
        TicketTool(support_service),
    ])


# ─── Orchestrator ─────────────────────────────────────────────────────────────

def get_orchestrator(
    db: Annotated[AsyncSession, Depends(get_db)],
    cache: Annotated[CacheBackend, Depends(get_cache)],
    knowledge_service: Annotated[KnowledgeService, Depends(get_knowledge_service)],
    support_service: Annotated[SupportService, Depends(get_support_service)],
) -> Orchestrator:
    llm = get_llm_client()
    session_mem = SessionMemory(cache, settings.session_ttl_seconds)
    registry = ToolRegistry([
        SearchTool(knowledge_service),
        OrderTool(get_erp_client()),
        TicketTool(support_service),
        ProcessTool(get_projuris_client()),
    ])
    agents = [
        FAQAgent(llm, registry),
        OrderAgent(llm, registry, UserMemory(cache)),
        SupportAgent(llm, registry),
        WorkflowAgent(llm, session_mem),
        ProcessAgent(llm, registry, UserMemory(cache)),
    ]
    router = IntentRouter(agents)
    context_builder = get_context_builder(db, cache)
    content_filter = ContentFilter()
    return Orchestrator(
        llm=llm,
        router=router,
        input_guard=InputGuard(content_filter),
        output_guard=OutputGuard(),
        context_builder=context_builder,
    )
