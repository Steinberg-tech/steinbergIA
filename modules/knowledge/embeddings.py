from fastembed import TextEmbedding

from observability.tracer import trace

_FASTEMBED_MODEL = "BAAI/bge-small-en-v1.5"


class EmbeddingGenerator:
    def __init__(self) -> None:
        self._model = TextEmbedding(model_name=_FASTEMBED_MODEL)

    async def embed(self, text: str) -> list[float]:
        async with trace("embedding.generate", model=_FASTEMBED_MODEL):
            result = list(self._model.embed([text]))
        return result[0].tolist()

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        async with trace("embedding.generate_batch", count=len(texts)):
            results = list(self._model.embed(texts))
        return [r.tolist() for r in results]
