from memory.history import HistoryMemory
from memory.session import SessionMemory
from memory.user_memory import UserMemory


class ContextBuilder:
    """
    Assembles the full context dict sent to every LLM call.
    Combines: recent message history + current session state + user persistent memory.
    """

    def __init__(
        self,
        history: HistoryMemory,
        session: SessionMemory,
        user_memory: UserMemory,
    ) -> None:
        self._history = history
        self._session = session
        self._user_memory = user_memory

    async def build(self, session_id: str) -> dict:
        history_messages, session_data, user_data = await _gather(
            self._history.get(session_id),
            self._session.get(session_id),
            self._user_memory.get(session_id),
        )
        return {
            "session_id": session_id,
            "history": history_messages,
            "session": session_data,
            "user": user_data,
        }


async def _gather(*coros):
    import asyncio
    return await asyncio.gather(*coros)
