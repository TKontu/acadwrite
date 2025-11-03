"""Unit tests for FileIntel client."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from acadwrite.services import (
    CollectionNotFoundError,
    FileIntelClient,
    FileIntelConnectionError,
    FileIntelError,
    FileIntelQueryError,
)


class TestFileIntelClient:
    """Tests for FileIntelClient."""

    @pytest.fixture
    def mock_client(self) -> MagicMock:
        """Create a mock httpx.AsyncClient."""
        return MagicMock(spec=httpx.AsyncClient)

    @pytest.mark.asyncio
    async def test_context_manager(self) -> None:
        """Test async context manager."""
        async with FileIntelClient("http://localhost:8000") as client:
            assert client._client is not None

    @pytest.mark.asyncio
    async def test_health_check_success(self, mock_client: MagicMock) -> None:
        """Test successful health check."""
        # Mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        result = await client.health_check()

        assert result is True
        mock_client.get.assert_called_once_with("http://localhost:8000/health")

    @pytest.mark.asyncio
    async def test_health_check_connection_error(self, mock_client: MagicMock) -> None:
        """Test health check with connection error."""
        mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        with pytest.raises(FileIntelConnectionError) as exc_info:
            await client.health_check()

        assert "Cannot connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_collections_success(self, mock_client: MagicMock) -> None:
        """Test successful collection listing."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": [
                {
                    "id": "coll-1",
                    "name": "test_collection",
                    "description": "Test",
                    "status": "ready",
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        collections = await client.list_collections()

        assert len(collections) == 1
        assert collections[0]["name"] == "test_collection"
        mock_client.get.assert_called_once_with("http://localhost:8000/api/v2/collections")

    @pytest.mark.asyncio
    async def test_list_collections_error(self, mock_client: MagicMock) -> None:
        """Test collection listing with API error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Internal error",
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        with pytest.raises(FileIntelQueryError) as exc_info:
            await client.list_collections()

        assert "Failed to list collections" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_success(self, mock_client: MagicMock) -> None:
        """Test successful query."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "answer": "This is the answer [Author, 2020, p. 5].",
                "sources": [
                    {
                        "document_id": "doc-1",
                        "chunk_id": "chunk-1",
                        "filename": "test.pdf",
                        "citation": "Author (2020). Title.",
                        "in_text_citation": "(Author, 2020, p. 5)",
                        "text": "Content excerpt",
                        "similarity_score": 0.95,
                        "relevance_score": 0.95,
                        "chunk_metadata": {"page_number": 5},
                        "document_metadata": {
                            "title": "Title",
                            "authors": ["Author"],
                        },
                    }
                ],
                "query_type": "vector",
                "collection_id": "coll-1",
                "question": "What is the test?",
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        result = await client.query("test_collection", "What is the test?")

        assert result.answer == "This is the answer [Author, 2020, p. 5]."
        assert len(result.sources) == 1
        assert result.sources[0].filename == "test.pdf"
        assert result.query_type == "vector"

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:8000/api/v2/collections/test_collection/query"
        assert call_args[1]["json"]["question"] == "What is the test?"
        assert call_args[1]["json"]["rag_type"] == "vector"

    @pytest.mark.asyncio
    async def test_query_with_max_sources(self, mock_client: MagicMock) -> None:
        """Test query with max_sources parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {
                "answer": "Answer",
                "sources": [],
                "query_type": "vector",
                "collection_id": "coll-1",
                "question": "Test?",
            },
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        await client.query("test_collection", "Test?", max_sources=5)

        call_args = mock_client.post.call_args
        assert call_args[1]["json"]["max_sources"] == 5

    @pytest.mark.asyncio
    async def test_query_collection_not_found(self, mock_client: MagicMock) -> None:
        """Test query with non-existent collection."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not found", request=MagicMock(), response=mock_response
        )
        mock_client.post = AsyncMock(return_value=mock_response)

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        with pytest.raises(CollectionNotFoundError) as exc_info:
            await client.query("nonexistent", "Test?")

        assert "nonexistent" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_connection_error(self, mock_client: MagicMock) -> None:
        """Test query with connection error."""
        mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        with pytest.raises(FileIntelConnectionError) as exc_info:
            await client.query("test_collection", "Test?")

        assert "Cannot connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_query_api_error(self, mock_client: MagicMock) -> None:
        """Test query with API error response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "error": "Query processing failed",
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        with pytest.raises(FileIntelQueryError) as exc_info:
            await client.query("test_collection", "Test?")

        assert "Query failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_client_not_initialized(self) -> None:
        """Test using client without context manager."""
        client = FileIntelClient("http://localhost:8000")

        with pytest.raises(FileIntelError) as exc_info:
            await client.health_check()

        assert "not initialized" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_close(self, mock_client: MagicMock) -> None:
        """Test close method."""
        mock_client.aclose = AsyncMock()

        client = FileIntelClient("http://localhost:8000")
        client._client = mock_client

        await client.close()

        mock_client.aclose.assert_called_once()
        assert client._client is None
