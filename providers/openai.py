import os
from typing import Optional
from langchain_openai import ChatOpenAI
from providers.base import BaseLLMProvider
import tiktoken

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.3):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.model_name = model
        try:
            self.encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append(("system", system_prompt))
        messages.append(("user", prompt))
        
        response = self.llm.invoke(messages)
        return response.content

    def get_token_count(self, text: str) -> int:
        return len(self.encoding.encode(text))
