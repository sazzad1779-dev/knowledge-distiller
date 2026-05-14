import os
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from providers.base import BaseLLMProvider

class GeminiProvider(BaseLLMProvider):
    def __init__(self, model: str = "gemini-1.5-pro", temperature: float = 0.3):
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        self.model_name = model

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("user", prompt))
        
        response = self.llm.invoke(messages)
        content = response.content
        
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    text_parts.append(part["text"])
                elif isinstance(part, str):
                    text_parts.append(part)
            return "".join(text_parts)
            
        return str(content)

    def get_token_count(self, text: str) -> int:
        return self.llm.get_num_tokens(text)
