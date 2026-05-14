from typing import Optional
from providers.base import BaseLLMProvider

class MockLLMProvider(BaseLLMProvider):
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        # Simple mock response that follows the new format
        return """
---
## Mock Section

> **Summary:** This is a mock summary of the section content, providing a high-level overview.

**Mock Concept**
→ This is a refined mock explanation that explains complex parts in detail.
→ Example: A practical mock example that makes the concept relatable.

**Another Mock Concept**
→ Another detailed explanation.
→ Example: Another practical example.
---
"""

    def get_token_count(self, text: str) -> int:
        return len(text.split())
