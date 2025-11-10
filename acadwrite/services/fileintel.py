"""FileIntel API client for RAG queries."""

import asyncio
import time
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
        api_key: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        """Initialize FileIntel client.

        Args:
            base_url: Base URL of FileIntel API
            api_key: API key for authentication (X-API-Key header, required for secured instances)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "FileIntelClient":
        """Async context manager entry."""
        # Add authentication header if API key provided
        headers = {}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        self._client = httpx.AsyncClient(timeout=self.timeout, headers=headers)
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

    async def _poll_task(
        self,
        task_id: str,
        poll_interval: float = 2.0,
        max_wait: float = 300.0,
    ) -> Dict[str, Any]:
        """Poll task status until completion.

        FileIntel v2 API is fully async - all queries return task IDs that must be polled.

        Args:
            task_id: Task ID from async query submission
            poll_interval: Seconds between status checks (default: 2.0)
            max_wait: Maximum seconds to wait before timeout (default: 300)

        Returns:
            Task result data when complete

        Raises:
            FileIntelQueryError: If task fails or times out
            FileIntelConnectionError: If cannot connect to API
        """
        client = self._get_client()
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            # Check task status
            status_url = f"{self.base_url}/api/v2/tasks/{task_id}/status"

            try:
                response = await client.get(status_url)
                response.raise_for_status()
                status_data = response.json()

                if not status_data.get("success"):
                    raise FileIntelQueryError(
                        f"Failed to get task status: {status_data.get('error')}"
                    )

                task_info = status_data["data"]
                status = task_info["status"]

                if status == "SUCCESS":
                    # Get the result
                    result_url = f"{self.base_url}/api/v2/tasks/{task_id}/result"
                    result_response = await client.get(result_url)
                    result_response.raise_for_status()
                    result_data = result_response.json()

                    if not result_data.get("success"):
                        raise FileIntelQueryError(
                            f"Failed to get task result: {result_data.get('error')}"
                        )

                    return result_data["data"]

                elif status == "FAILURE":
                    error_msg = task_info.get("error", "Unknown error")
                    raise FileIntelQueryError(f"Query task failed: {error_msg}")

                elif status in ["PENDING", "STARTED", "RETRY"]:
                    # Still processing, wait and retry
                    await asyncio.sleep(poll_interval)
                    continue

                else:
                    raise FileIntelQueryError(f"Unknown task status: {status}")

            except httpx.HTTPStatusError as e:
                raise FileIntelConnectionError(f"HTTP error checking task status: {e}")
            except httpx.ConnectError as e:
                raise FileIntelConnectionError(f"Cannot connect to FileIntel: {e}")

        # Timeout
        raise FileIntelQueryError(
            f"Query timed out after {max_wait}s. Task ID: {task_id}. "
            f"Use this ID to check status manually."
        )

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
        search_type: str = "adaptive",
        max_results: Optional[int] = None,
        include_sources: bool = True,
        answer_format: str = "default",
        timeout: float = 300.0,
    ) -> QueryResponse:
        """Execute a query against a collection.

        Note: FileIntel v2 API is fully async. This method submits the query
        as a Celery task and polls until completion. The API ignores query_mode
        parameter and always returns a task_id.

        Args:
            collection: Collection name to query
            question: Question to ask
            search_type: Search type - "vector", "graph", "adaptive", "global", "local"
            max_results: Maximum number of sources to return
            include_sources: Include source citations in response
            answer_format: Answer format - "default", "single_paragraph", "table",
                          "list", "json", "essay", or "markdown"
            timeout: Maximum seconds to wait for result (default: 5 minutes)

        Returns:
            QueryResponse with answer and sources

        Raises:
            FileIntelConnectionError: If cannot connect to API
            CollectionNotFoundError: If collection doesn't exist
            FileIntelQueryError: If query fails or times out
        """
        client = self._get_client()
        url = f"{self.base_url}/api/v2/collections/{collection}/query"

        # Build request payload
        # Note: API will force async mode regardless of query_mode parameter
        payload: Dict[str, Any] = {
            "question": question,
            "search_type": search_type,
            "include_sources": include_sources,
            "answer_format": answer_format,
        }

        if max_results is not None:
            payload["max_results"] = max_results

        try:
            # Step 1: Submit query (returns task_id immediately)
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
                raise FileIntelQueryError(f"Query submission failed: {error_msg}")

            # Extract task_id from response
            task_data = data["data"]
            task_id = task_data.get("task_id")

            if not task_id:
                # Unexpected response format
                raise FileIntelQueryError(f"API response missing task_id. Got: {task_data}")

            # Step 2: Poll task until completion
            result_data = await self._poll_task(task_id, max_wait=timeout)

            # Step 3: Parse result into QueryResponse
            return QueryResponse.from_fileintel_response(result_data)

        except CollectionNotFoundError:
            raise
        except FileIntelConnectionError:
            raise
        except FileIntelQueryError:
            raise
        except httpx.ConnectError as e:
            raise FileIntelConnectionError(f"Cannot connect to FileIntel at {self.base_url}: {e}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise CollectionNotFoundError(f"Collection '{collection}' not found")
            raise FileIntelQueryError(f"HTTP error during query: {e}")
        except Exception as e:
            raise FileIntelQueryError(f"Unexpected error during query: {e}")
