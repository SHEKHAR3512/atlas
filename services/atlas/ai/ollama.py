import json
import logging
from typing import Any, Dict
import httpx
from services.atlas.ai.base import AIProvider
from services.atlas.ai.disabled import DisabledAIProvider
from services.atlas.core.config import config

logger = logging.getLogger("atlas.ai.ollama")


class OllamaProvider(AIProvider):
    """
    Local Ollama integration provider.
    Fails gracefully to DisabledAIProvider if Ollama daemon is offline.
    """

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = config.settings.OLLAMA_BASE_URL or base_url
        self.model = config.settings.OLLAMA_MODEL or model
        self.fallback = DisabledAIProvider()

    async def generate(self, prompt: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False}
                )
                if res.status_code == 200:
                    return res.json().get("response", "")
        except Exception as e:
            logger.debug(f"Ollama offline or error ({e}), using fallback.")
        return await self.fallback.generate(prompt)

    async def structured_generate(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        prompt_with_format = f"{prompt}\nReturn JSON strictly matching this schema:\n{json.dumps(schema)}"
        raw_text = await self.generate(prompt_with_format)
        try:
            return json.loads(raw_text)
        except Exception:
            return await self.fallback.structured_generate(prompt, schema)

    async def summarize(self, text: str) -> str:
        prompt = f"Summarize the following quantitative trading experiment concisely:\n\n{text}"
        res = await self.generate(prompt)
        if not res or "[Deterministic AI Disabled]" in res:
            return await self.fallback.summarize(text)
        return res
