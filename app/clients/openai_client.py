"""Placeholder OpenAI client.

Use this module to wrap interactions with OpenAI's APIs. Keep keys in environment
variables and never hardcode secrets.
"""

from __future__ import annotations

from app.core.config import settings


class OpenAIClient:
    def __init__(self) -> None:
        # Placeholder for client initialization; do not implement real logic
        self.api_key = settings.openai_api_key

    def chat(self, messages: list[dict]) -> dict:
        """Placeholder chat call to OpenAI.

        Do not implement real logic. This method will be implemented later.
        """
        raise NotImplementedError("OpenAI client is a placeholder in the scaffold.")
