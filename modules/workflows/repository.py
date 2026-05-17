import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from modules.workflows.models import Workflow, WorkflowStep
from shared.constants import WorkflowStatus
from shared.utils import generate_id, now_utc


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, session_id: str, workflow_type: str) -> Workflow:
        wf = Workflow(id=generate_id(), session_id=session_id, workflow_type=workflow_type)
        self._session.add(wf)
        await self._session.flush()
        return wf

    async def get_active(self, session_id: str) -> Workflow | None:
        result = await self._session.execute(
            select(Workflow)
            .where(Workflow.session_id == session_id)
            .where(Workflow.status == WorkflowStatus.IN_PROGRESS)
            .options(selectinload(Workflow.steps))
            .order_by(Workflow.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def advance(self, workflow_id: str, data: dict) -> None:
        result = await self._session.execute(select(Workflow).where(Workflow.id == workflow_id))
        wf = result.scalar_one_or_none()
        if wf:
            wf.current_step += 1
            existing = json.loads(wf.data or "{}")
            existing.update(data)
            wf.data = json.dumps(existing)
            wf.updated_at = now_utc()

    async def complete(self, workflow_id: str) -> None:
        result = await self._session.execute(select(Workflow).where(Workflow.id == workflow_id))
        wf = result.scalar_one_or_none()
        if wf:
            wf.status = WorkflowStatus.COMPLETED
            wf.updated_at = now_utc()
