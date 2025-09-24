"""OpenAI client for chatbot functionality.

Use this module to wrap interactions with OpenAI's APIs. Keep keys in environment
variables and never hardcode secrets.
"""

from __future__ import annotations

import openai
from app.core.config import settings
from app.core.logger import log_info


class OpenAIClient:
    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        
        self.client = openai.OpenAI(api_key=settings.openai_api_key)

    def chat(self, messages: list[dict], model: str = "gpt-3.5-turbo") -> dict:
        """Make a chat completion request to OpenAI.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: The model to use for completion
            
        Returns:
            Dictionary containing the response from OpenAI
        """
        try:
            log_info("Making OpenAI chat request", model=model, message_count=len(messages))
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return {
                "content": response.choices[0].message.content,
                "role": "assistant",
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
        except Exception as e:
            log_info("OpenAI API error", error=str(e))
            raise Exception(f"OpenAI API error: {str(e)}")
