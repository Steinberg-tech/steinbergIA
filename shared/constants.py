from enum import StrEnum


class Intent(StrEnum):
    FAQ = "faq"
    ORDER_STATUS = "order_status"
    SUPPORT = "support"
    WORKFLOW = "workflow"


class AgentName(StrEnum):
    FAQ = "faq_agent"
    ORDER = "order_agent"
    SUPPORT = "support_agent"
    WORKFLOW = "workflow_agent"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    WAITING = "waiting"


class Platform(StrEnum):
    WHATSAPP = "whatsapp"
    WIDGET = "widget"
    API = "api"
    TELEGRAM = "telegram"


class TicketStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class WorkflowStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_APPROVAL = "waiting_approval"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TemplateMessage(StrEnum):
    RETOMADA_DE_CONVERSA = "retomada_de_conversa"
    AUXMATERNIDADE = "auxmaternidade"
    CONTATO_URGENTE_OK = "contato_urgente_ok"
    COMERCIAL_REENVIOCASOS = "comercial_reenviocasos"
    SOLICITACAO_DOCUMENTOS = "solicitacao_documentos"
    BOAS_VINDAS_ADVLEADS_AUXACIDENTE = "boas_vindas_advleads_auxacidente"
    LEAD_INSTASTEINBERG = "lead_instasteinberg"
    CONVERSA_RETOMADA = "conversa_retomada"
    BOAS_VINDAS_2 = "boas_vindas_2"
    CONTATO_INFORMACAO_PROCESSO = "contato_informacao_processo"
    NOVO_NUMERO = "novo_numero"
    CONTATO_URGENTE_NOVO = "contato_urgente_novo"
