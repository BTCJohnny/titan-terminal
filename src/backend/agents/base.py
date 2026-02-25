"""Base agent class for all specialist agents."""
import json
from abc import ABC, abstractmethod
from typing import Any
import anthropic
from ..config import config


class BaseAgent(ABC):
    """Base class for all specialist agents."""

    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.MODEL_NAME

    @abstractmethod
    def analyze(self, symbol: str, context: dict) -> dict:
        """Analyze a symbol and return structured JSON output."""
        pass

    def _call_claude(self, user_message: str, max_tokens: int = 2000) -> str:
        """Call Claude API with the agent's system prompt."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=self.system_prompt,
            messages=[{"role": "user", "content": user_message}]
        )
        return response.content[0].text

    def _parse_json_response(self, response: str) -> dict:
        """Extract JSON from Claude's response."""
        # Try to find JSON block in response
        try:
            # Look for ```json blocks
            if "```json" in response:
                start = response.index("```json") + 7
                end = response.index("```", start)
                return json.loads(response[start:end].strip())
            # Try parsing whole response as JSON
            return json.loads(response)
        except (json.JSONDecodeError, ValueError):
            # Return raw response wrapped in dict
            return {"raw_response": response, "parse_error": True}
