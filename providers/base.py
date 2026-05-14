from abc import ABC, abstractmethod
from typing import Optional

class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate content based on prompt."""
        pass

    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """Get token count for the given text."""
        pass
