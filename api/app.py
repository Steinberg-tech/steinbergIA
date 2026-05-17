from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.middleware.logging_middleware import LoggingMiddleware
from api.middleware.rate_limit import RateLimitMiddleware
from api.routes import chat, conversations, health, knowledge, webhooks
from config.logging_config import configure_logging
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Tool-Driven Conversational AI for customer support (SAC)",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(knowledge.router)
app.include_router(webhooks.router)
