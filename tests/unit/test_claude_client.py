"""Tests for Claude LLM client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hcr_core.llm.claude import ClaudeClient


class TestClaudeClient:
    def test_init_with_api_key(self) -> None:
        client = ClaudeClient(model="claude-sonnet-4-20250514", api_key="test-key")
        assert client.model == "claude-sonnet-4-20250514"

    @patch("hcr_core.llm.claude.Anthropic")
    def test_complete_calls_api(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_block = MagicMock()
        mock_block.text = "test response"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(model="claude-sonnet-4-20250514", api_key="test-key")
        result = client.complete("Hello", system="You are helpful.")

        assert result == "test response"
        mock_client.messages.create.assert_called_once()

    @patch("hcr_core.llm.claude.Anthropic")
    def test_complete_without_system(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_block = MagicMock()
        mock_block.text = "response"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(model="claude-sonnet-4-20250514", api_key="test-key")
        result = client.complete("Hello")

        assert result == "response"

    @patch("hcr_core.llm.claude.AsyncAnthropic")
    async def test_acomplete_calls_api(self, mock_async_cls: MagicMock) -> None:
        mock_client = AsyncMock()
        mock_async_cls.return_value = mock_client
        mock_block = MagicMock()
        mock_block.text = "async response"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(model="claude-sonnet-4-20250514", api_key="test-key")
        result = await client.acomplete("Hello", system="System prompt")

        assert result == "async response"

    @patch("hcr_core.llm.claude.Anthropic")
    def test_complete_with_max_tokens(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_block = MagicMock()
        mock_block.text = "short"
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        mock_client.messages.create.return_value = mock_response

        client = ClaudeClient(model="claude-sonnet-4-20250514", api_key="test-key")
        client.complete("Hello", max_tokens=100)

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["max_tokens"] == 100
