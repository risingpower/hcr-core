"""Claude LLM client wrapping the Anthropic SDK."""

from __future__ import annotations

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import MessageParam


class ClaudeClient:
    """Sync and async wrapper for the Anthropic messages API."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self._api_key = api_key
        self._sync_client: Anthropic | None = None
        self._async_client: AsyncAnthropic | None = None

    def _get_sync_client(self) -> Anthropic:
        if self._sync_client is None:
            self._sync_client = Anthropic(api_key=self._api_key)
        return self._sync_client

    def _get_async_client(self) -> AsyncAnthropic:
        if self._async_client is None:
            self._async_client = AsyncAnthropic(api_key=self._api_key)
        return self._async_client

    def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Synchronous completion."""
        client = self._get_sync_client()
        messages: list[MessageParam] = [{"role": "user", "content": prompt}]
        if system is not None:
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                system=system,
            )
        else:
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
            )
        if not response.content:
            raise ValueError("Claude API returned empty content")
        block = response.content[0]
        if not hasattr(block, "text"):
            raise ValueError(
                f"Expected text block from Claude API, got {type(block).__name__}"
            )
        return block.text

    async def acomplete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> str:
        """Asynchronous completion."""
        client = self._get_async_client()
        messages: list[MessageParam] = [{"role": "user", "content": prompt}]
        if system is not None:
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
                system=system,
            )
        else:
            response = await client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=messages,
            )
        if not response.content:
            raise ValueError("Claude API returned empty content")
        block = response.content[0]
        if not hasattr(block, "text"):
            raise ValueError(
                f"Expected text block from Claude API, got {type(block).__name__}"
            )
        return block.text
