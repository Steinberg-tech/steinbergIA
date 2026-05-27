from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_env: str = "development"
    app_name: str = "SAC AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # LLM
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    # Database
    database_url: str = "postgresql+asyncpg://sac:sac@localhost:5432/sac_ai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8001
    chroma_collection: str = "sac_knowledge"

    # Memory
    history_max_messages: int = 20
    session_ttl_seconds: int = 3600

    # Guardrails
    max_input_length: int = 2000
    blocked_terms: str = ""

    # Rate limiting
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60

    # ERP
    erp_base_url: str = ""
    erp_api_key: str = ""
    erp_timeout_seconds: int = 10

    # CRM
    crm_base_url: str = ""
    crm_api_key: str = ""
    crm_timeout_seconds: int = 10

    # projurisADV
    projuris_base_url: str = ""
    projuris_api_key: str = ""
    projuris_timeout_seconds: int = 10

    # Digisac
    digisac_base_url: str = "https://steinbergadvogados.digisac.io/api/v1"
    digisac_token: str = ""
    digisac_service_id: str = ""
    # Comma-separated phone numbers allowed to trigger the AI (e.g. "5585997085202,5511999999999")
    digisac_allowed_senders: str = ""

    @property
    def digisac_allowed_senders_list(self) -> list[str]:
        if not self.digisac_allowed_senders:
            return []
        return [p.strip() for p in self.digisac_allowed_senders.split(",") if p.strip()]

    @property
    def blocked_terms_list(self) -> list[str]:
        if not self.blocked_terms:
            return []
        return [t.strip() for t in self.blocked_terms.split(",") if t.strip()]


settings = Settings()
