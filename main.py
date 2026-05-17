import uvicorn

from config.logging_config import configure_logging
from config.settings import settings

configure_logging()

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_config=None,
    )
