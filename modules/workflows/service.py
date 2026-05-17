from modules.workflows.engine import WorkflowEngine
from modules.workflows.repository import WorkflowRepository


class WorkflowService:
    def __init__(self, engine: WorkflowEngine) -> None:
        self._engine = engine

    async def start_workflow(self, session_id: str, workflow_type: str) -> str:
        return await self._engine.start(session_id, workflow_type)

    async def advance_workflow(self, session_id: str, data: dict) -> dict:
        return await self._engine.advance(session_id, data)

    def get_available_workflows(self) -> list[str]:
        from modules.workflows.engine import _WORKFLOW_STEPS
        return list(_WORKFLOW_STEPS.keys())
