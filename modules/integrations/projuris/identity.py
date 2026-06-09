import time

from memory.user_memory import UserMemory
from modules.integrations.projuris.projuris_client import ProjurisClient
from observability.logger import get_logger
from shared.exceptions import IntegrationError

_log = get_logger("projuris_identity")


class ProjurisIdentityService:
    """Resolve e cacheia a identidade do contato no Projuris a partir do telefone.

    - Cache positivo: persiste enquanto a UserMemory viver (30 dias).
    - Não encontrado: re-tenta apenas após a janela de re-tentativa (1h).
    - Erro transitório (Projuris fora): não cacheia como não-encontrado.
    """

    _NOT_FOUND_RETRY_SECONDS = 60 * 60

    def __init__(self, client: ProjurisClient, user_memory: UserMemory) -> None:
        self._client = client
        self._user_memory = user_memory

    async def ensure_identity(self, session_id: str, phone: str) -> dict:
        user = await self._user_memory.get(session_id)

        if user.get("projuris_codigo_pessoa"):
            return user  # cache positivo

        checked_at = user.get("projuris_checked_at")
        if checked_at and (time.time() - checked_at) < self._NOT_FOUND_RETRY_SECONDS:
            return user  # não-encontrado recente: não reconsulta

        if not phone:
            return user

        try:
            pessoa = await self._client.get_pessoa_by_telefone(phone)
        except IntegrationError as exc:
            _log.error("projuris_identity_lookup_failed", session_id=session_id, error=str(exc))
            return user  # transitório: não cacheia

        if pessoa:
            await self._user_memory.remember_projuris_identity(
                session_id,
                codigo_pessoa=pessoa.get("codigoPessoa"),
                nome=pessoa.get("nome"),
                email=pessoa.get("emailPrincipal"),
                habilitado=pessoa.get("habilitado"),
                telefone=pessoa.get("telefonePrincipal"),
                checked_at=time.time(),
            )
            _log.info("projuris_identity_resolved", session_id=session_id, codigo_pessoa=pessoa.get("codigoPessoa"))
        else:
            await self._user_memory.remember_projuris_identity(
                session_id,
                codigo_pessoa=None,
                nome=None,
                email=None,
                habilitado=None,
                telefone=None,
                checked_at=time.time(),
            )
            _log.info("projuris_identity_not_found", session_id=session_id)

        return await self._user_memory.get(session_id)
