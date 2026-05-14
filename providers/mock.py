from typing import Optional
from providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Simple mock response that follows the format
        return """
---
## Mock Section

**Distilled Concept**
→ This is a mock explanation for a concept found in the text.
→ Example: This is a mock example.

**Another Concept**
→ Another mock explanation.
→ Example: Another mock example.
---
"""

    def get_token_count(self, text: str) -> int:
        return len(text.split())
