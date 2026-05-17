"""
Creates all database tables from SQLAlchemy models.
Run: python scripts/migrate_db.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import create_async_engine

from config.settings import settings
from modules.conversations.models import Base as ConvBase
from modules.knowledge.models import Document
from modules.support.models import Ticket
from modules.workflows.models import Workflow, WorkflowStep


async def migrate():
    print(f"Connecting to: {settings.database_url}")
    engine = create_async_engine(settings.database_url)
    async with engine.begin() as conn:
        await conn.run_sync(ConvBase.metadata.create_all)
    await engine.dispose()
    print("Migration complete. Tables created.")


if __name__ == "__main__":
    asyncio.run(migrate())
