from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProvider(ABC):

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """Generate unstructured text completion."""
        pass

    @abstractmethod
    async def structured_generate(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON adhering to given schema."""
        pass

    @abstractmethod
    async def summarize(self, text: str) -> str:
        """Summarize research results or trade history."""
        pass
