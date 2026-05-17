"""
Integration tests for LLM providers.
These tests require real API keys and are skipped in CI unless ENV vars are set.
"""

import os
import pytest

from modules.ai.llm.providers.openai_provider import OpenAIProvider
from shared.constants import Intent


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
@pytest.mark.asyncio
async def test_openai_classify_intent_faq():
    provider = OpenAIProvider()
    classification = await provider.classify_intent(
        "Qual é o prazo de entrega?",
        context={"history": []},
    )
    assert classification.intent in [Intent.FAQ, Intent.ORDER_STATUS]
    assert 0.0 <= classification.confidence <= 1.0


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
@pytest.mark.asyncio
async def test_openai_generate_response():
    from modules.ai.prompts.agent_prompts import FAQ_AGENT_PROMPT
    provider = OpenAIProvider()
    response = await provider.generate_response(
        system_prompt=FAQ_AGENT_PROMPT,
        user_message="Como funciona a troca de produto?",
        history=[],
    )
    assert response.content
    assert response.output_tokens > 0
