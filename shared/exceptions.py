class SACBaseError(Exception):
    """Base exception for all SAC AI errors."""


class InputValidationError(SACBaseError):
    """Raised when user input fails validation."""


class OutputValidationError(SACBaseError):
    """Raised when AI output fails safety checks."""


class AgentNotFoundError(SACBaseError):
    """Raised when the router cannot find an agent for the given intent."""


class ToolExecutionError(SACBaseError):
    """Raised when a tool fails to execute."""


class LLMProviderError(SACBaseError):
    """Raised when the LLM provider returns an error."""


class IntegrationError(SACBaseError):
    """Raised when an external integration (ERP, CRM) fails."""


class ConversationNotFoundError(SACBaseError):
    """Raised when a conversation or session cannot be found."""


class KnowledgeBaseError(SACBaseError):
    """Raised when the knowledge base / vector store fails."""
