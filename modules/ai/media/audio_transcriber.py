import io

from config.settings import settings
from observability.logger import get_logger

_log = get_logger("audio_transcriber")


class AudioTranscriber:
    """Transcribes audio bytes to text using OpenAI Whisper."""

    async def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/ogg") -> str:
        if not settings.openai_api_key:
            _log.warning("audio_transcriber_no_key")
            return "[Áudio recebido — transcrição indisponível: configure OPENAI_API_KEY]"

        from openai import AsyncOpenAI

        ext = _mime_to_ext(mime_type)
        filename = f"audio.{ext}"

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename

        try:
            result = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="pt",
            )
            text = result.text.strip()
            _log.info("audio_transcribed", chars=len(text))
            return text
        except Exception as exc:
            _log.error("audio_transcription_error", error=str(exc))
            return "[Áudio recebido — não foi possível transcrever no momento]"


def _mime_to_ext(mime_type: str) -> str:
    mapping = {
        "audio/ogg": "ogg",
        "audio/ogg; codecs=opus": "ogg",
        "audio/mpeg": "mp3",
        "audio/mp4": "mp4",
        "audio/wav": "wav",
        "audio/webm": "webm",
        "audio/aac": "aac",
    }
    return mapping.get(mime_type, "ogg")
