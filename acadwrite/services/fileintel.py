"""FileIntel API client for RAG queries."""

from typing import Any, Dict, List, Optional

import httpx

from acadwrite.models.query import QueryResponse


class FileIntelError(Exception):
    """Base exception for FileIntel client errors."""

    pass


class FileIntelConnectionError(FileIntelError):
    """Failed to connect to FileIntel API."""

    pass


class FileIntelQueryError(FileIntelError):
    """Error executing query against FileIntel."""

    pass


class CollectionNotFoundError(FileIntelError):
    """Requested collection does not exist."""

    pass


class FileIntelClient:
    """Async HTTP client for FileIntel RAG platform.

    This client handles all communication with the FileIntel API,
    including queries, collection management, and health checks.

    Example:
        async with FileIntelClient("http://localhost:8000") as client:
            response = await client.query("my_collection", "What is RAG?")
            print(response.answer)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize FileIntel client.

        Args:
            base_url: Base URL of FileIntel API
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "FileIntelClient":
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client.

        Returns:
            Active AsyncClient instance

        Raises:
            FileIntelError: If client not initialized (use context manager)
        """
        if self._client is None:
            raise FileIntelError("Client not initialized. Use 'async with' context manager.")
        return self._client

    async def health_check(self) -> bool:
        """Check if FileIntel API is available.

        Returns:
            True if API is healthy

        Raises:
            FileIntelConnectionError: If cannot connect to API
        """
        client = self._get_client()
        url = f"{self.base_url}/health"

        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "ok"
        except httpx.ConnectError as e:
            raise FileIntelConnectionError(f"Cannot connect to FileIntel at {self.base_url}: {e}")
        except httpx.HTTPStatusError as e:
            raise FileIntelConnectionError(f"FileIntel health check failed: {e}")

    async def list_collections(self) -> List[Dict[str, Any]]:
        """List available collections.

        Returns:
            List of collection dictionaries with id, name, description, status

        Raises:
            FileIntelConnectionError: If cannot connect to API
            FileIntelQueryError: If API returns error
        """
        client = self._get_client()
        url = f"{self.base_url}/api/v2/collections"

        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                error_msg = data.get("error", "Unknown error")
                raise FileIntelQueryError(f"Failed to list collections: {error_msg}")

            return data.get("data", [])

        except httpx.ConnectError as e:
            raise FileIntelConnectionError(f"Cannot connect to FileIntel: {e}")
        except httpx.HTTPStatusError as e:
            raise FileIntelQueryError(f"HTTP error listing collections: {e}")

    async def query(
        self,
        collection: str,
        question: str,
        rag_type: str = "vector",
        max_sources: Optional[int] = None,
    ) -> QueryResponse:
        """Execute a query against a collection.

        Args:
            collection: Collection name to query
            question: Question to ask
            rag_type: RAG type - "vector", "graph", or "auto"
            max_sources: Maximum number of sources to return

        Returns:
            QueryResponse with answer and sources

        Raises:
            FileIntelConnectionError: If cannot connect to API
            CollectionNotFoundError: If collection doesn't exist
            FileIntelQueryError: If query fails
        """
        client = self._get_client()
        url = f"{self.base_url}/api/v2/collections/{collection}/query"

        payload: Dict[str, Any] = {
            "question": question,
            "rag_type": rag_type,
        }

        if max_sources is not None:
            payload["max_sources"] = max_sources

        try:
            response = await client.post(url, json=payload)

            # Handle 404 specially for collection not found
            if response.status_code == 404:
                raise CollectionNotFoundError(
                    f"Collection '{collection}' not found. "
                    f"Use list_collections() to see available collections."
                )

            response.raise_for_status()
            data = response.json()

            if not data.get("success"):
                error_msg = data.get("error", "Unknown error")
                raise FileIntelQueryError(f"Query failed: {error_msg}")

            # Parse response data into QueryResponse model
            return QueryResponse.from_fileintel_response(data["data"])

        except httpx.ConnectError as e:
            raise FileIntelConnectionError(f"Cannot connect to FileIntel at {self.base_url}: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise CollectionNotFoundError(f"Collection '{collection}' not found")
            raise FileIntelQueryError(f"HTTP error during query: {e}")
        except CollectionNotFoundError:
            # Re-raise our custom exceptions
            raise
        except FileIntelConnectionError:
            raise
        except FileIntelQueryError:
            raise
        except Exception as e:
            # Catch-all for unexpected errors
            raise FileIntelQueryError(f"Unexpected error during query: {e}")
