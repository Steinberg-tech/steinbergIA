import structlog

logger = structlog.get_logger()


def get_logger(name: str) -> structlog.BoundLogger:
    return structlog.get_logger(name)
