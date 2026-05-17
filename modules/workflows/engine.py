from modules.workflows.repository import WorkflowRepository
from observability.logger import get_logger

_log = get_logger("workflow_engine")

_WORKFLOW_STEPS: dict[str, list[str]] = {
    "troca": ["Confirmar produto", "Verificar elegibilidade", "Agendar coleta", "Confirmar nova entrega"],
    "cancelamento": ["Confirmar pedido", "Verificar prazo", "Processar cancelamento", "Confirmar reembolso"],
    "reembolso": ["Confirmar pedido", "Verificar motivo", "Aprovar reembolso", "Processar pagamento"],
    "devolucao": ["Confirmar produto", "Verificar condição", "Agendar coleta", "Confirmar recebimento"],
}


class WorkflowEngine:
    def __init__(self, repo: WorkflowRepository) -> None:
        self._repo = repo

    def get_steps(self, workflow_type: str) -> list[str]:
        return _WORKFLOW_STEPS.get(workflow_type, [])

    async def start(self, session_id: str, workflow_type: str) -> str:
        wf = await self._repo.create(session_id, workflow_type)
        _log.info("workflow_started", session_id=session_id, type=workflow_type, id=wf.id)
        return wf.id

    async def advance(self, session_id: str, collected_data: dict) -> dict:
        wf = await self._repo.get_active(session_id)
        if not wf:
            return {"status": "no_active_workflow"}
        steps = self.get_steps(wf.workflow_type)
        if wf.current_step > len(steps):
            await self._repo.complete(wf.id)
            return {"status": "completed", "workflow_id": wf.id}
        await self._repo.advance(wf.id, collected_data)
        next_step = steps[wf.current_step] if wf.current_step < len(steps) else None
        return {
            "status": "in_progress",
            "workflow_id": wf.id,
            "current_step": wf.current_step,
            "next_step": next_step,
        }
