"""Unit tests for LLM client."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from acadwrite.services import LLMClient, LLMError


class TestLLMClient:
    """Tests for LLMClient."""

    @pytest.mark.asyncio
    async def test_invert_claim_success(self) -> None:
        """Test successful claim inversion."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "agile increases development time challenges"

        # Mock the OpenAI client
        with patch("acadwrite.services.llm.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(
                base_url="http://test:9003/v1",
                model="test-model",
                api_key="test",
            )

            result = await client.invert_claim("Agile reduces development time")

            assert result == "agile increases development time challenges"
            mock_client.chat.completions.create.assert_called_once()

            # Check prompt includes original claim
            call_args = mock_client.chat.completions.create.call_args
            assert "Agile reduces development time" in call_args[1]["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_invert_claim_empty_response(self) -> None:
        """Test handling of empty LLM response."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None

        with patch("acadwrite.services.llm.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(
                base_url="http://test:9003/v1",
                model="test-model",
            )

            with pytest.raises(LLMError) as exc_info:
                await client.invert_claim("Test claim")

            assert "empty response" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_invert_claim_api_error(self) -> None:
        """Test handling of API errors."""
        with patch("acadwrite.services.llm.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API connection failed")
            )
            mock_openai_class.return_value = mock_client

            client = LLMClient(
                base_url="http://test:9003/v1",
                model="test-model",
            )

            with pytest.raises(LLMError) as exc_info:
                await client.invert_claim("Test claim")

            assert "Failed to invert claim" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_initialization(self) -> None:
        """Test client initialization with custom parameters."""
        with patch("acadwrite.services.llm.AsyncOpenAI") as mock_openai_class:
            client = LLMClient(
                base_url="http://custom:8000/v1",
                model="custom-model",
                api_key="custom-key",
                temperature=0.5,
            )

            assert client.model == "custom-model"
            assert client.temperature == 0.5

            # Check AsyncOpenAI was called with correct params
            mock_openai_class.assert_called_once_with(
                base_url="http://custom:8000/v1",
                api_key="custom-key",
            )

    @pytest.mark.asyncio
    async def test_invert_claim_whitespace_trimming(self) -> None:
        """Test that response whitespace is trimmed."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "  \n  inverted query  \n  "

        with patch("acadwrite.services.llm.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_openai_class.return_value = mock_client

            client = LLMClient(
                base_url="http://test:9003/v1",
                model="test-model",
            )

            result = await client.invert_claim("Test")

            assert result == "inverted query"

    @pytest.mark.asyncio
    async def test_close(self) -> None:
        """Test closing the client."""
        with patch("acadwrite.services.llm.AsyncOpenAI") as mock_openai_class:
            mock_client = AsyncMock()
            mock_openai_class.return_value = mock_client

            client = LLMClient(
                base_url="http://test:9003/v1",
                model="test-model",
            )

            await client.close()

            mock_client.close.assert_called_once()
