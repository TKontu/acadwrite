"""Integration tests for FileIntel client.

These tests require a running FileIntel instance with a test collection.
"""

import pytest

from acadwrite.services.fileintel import (
    CollectionNotFoundError,
    FileIntelConnectionError,
    FileIntelQueryError,
)


class TestFileIntelIntegration:
    """Integration tests for FileIntel client."""

    @pytest.mark.asyncio
    async def test_health_check(self, fileintel_client):
        """Test FileIntel health check."""
        is_healthy = await fileintel_client.health_check()
        assert is_healthy is True

    @pytest.mark.asyncio
    async def test_list_collections(self, fileintel_client):
        """Test listing available collections."""
        collections = await fileintel_client.list_collections()

        assert isinstance(collections, list)
        # Should have at least one collection (or empty list is ok)
        if collections:
            # Verify collection structure
            collection = collections[0]
            assert "id" in collection
            assert "name" in collection

    @pytest.mark.asyncio
    async def test_query_success(self, fileintel_client, test_collection):
        """Test successful query against collection."""
        try:
            response = await fileintel_client.query(
                collection=test_collection,
                question="What is machine learning?",
                max_sources=5,
            )

            # Verify response structure
            assert response.answer is not None
            assert isinstance(response.answer, str)
            assert len(response.answer) > 0

            # Verify sources
            assert isinstance(response.sources, list)
            # May have 0 sources if collection is empty

            if response.sources:
                source = response.sources[0]
                # Verify source structure
                assert source.document_id is not None
                assert source.chunk_id is not None
                assert source.text is not None
                assert source.citation is not None
                assert source.in_text_citation is not None

        except CollectionNotFoundError:
            pytest.skip(f"Test collection '{test_collection}' not found")

    @pytest.mark.asyncio
    async def test_query_with_max_sources(self, fileintel_client, test_collection):
        """Test query with max_sources parameter."""
        try:
            response = await fileintel_client.query(
                collection=test_collection,
                question="Explain neural networks",
                max_sources=3,
            )

            # Should respect max_sources (or return fewer if not enough documents)
            assert len(response.sources) <= 3

        except CollectionNotFoundError:
            pytest.skip(f"Test collection '{test_collection}' not found")

    @pytest.mark.asyncio
    async def test_query_different_rag_types(self, fileintel_client, test_collection):
        """Test query with different RAG types."""
        try:
            # Test vector RAG
            response_vector = await fileintel_client.query(
                collection=test_collection,
                question="What is deep learning?",
                rag_type="vector",
                max_sources=3,
            )
            assert response_vector.answer is not None

            # Test graph RAG
            response_graph = await fileintel_client.query(
                collection=test_collection,
                question="What is deep learning?",
                rag_type="graph",
                max_sources=3,
            )
            assert response_graph.answer is not None

            # Test auto RAG
            response_auto = await fileintel_client.query(
                collection=test_collection,
                question="What is deep learning?",
                rag_type="auto",
                max_sources=3,
            )
            assert response_auto.answer is not None

        except CollectionNotFoundError:
            pytest.skip(f"Test collection '{test_collection}' not found")

    @pytest.mark.asyncio
    async def test_query_nonexistent_collection(self, fileintel_client):
        """Test query against nonexistent collection."""
        with pytest.raises(CollectionNotFoundError):
            await fileintel_client.query(
                collection="nonexistent_collection_xyz_123",
                question="test question",
            )

    @pytest.mark.asyncio
    async def test_query_empty_question(self, fileintel_client, test_collection):
        """Test query with empty question."""
        try:
            # Should handle gracefully or raise appropriate error
            response = await fileintel_client.query(
                collection=test_collection,
                question="",
                max_sources=1,
            )
            # If it doesn't raise, verify response structure
            assert response.answer is not None

        except (FileIntelQueryError, CollectionNotFoundError) as e:
            # Both are acceptable - empty question may be invalid
            pass

    @pytest.mark.asyncio
    async def test_query_long_question(self, fileintel_client, test_collection):
        """Test query with very long question."""
        try:
            long_question = " ".join(["test"] * 100)  # 100 word question

            response = await fileintel_client.query(
                collection=test_collection,
                question=long_question,
                max_sources=2,
            )

            # Should handle long questions
            assert response.answer is not None

        except CollectionNotFoundError:
            pytest.skip(f"Test collection '{test_collection}' not found")

    @pytest.mark.asyncio
    async def test_multiple_queries_sequential(self, fileintel_client, test_collection):
        """Test multiple sequential queries."""
        try:
            questions = [
                "What is artificial intelligence?",
                "Explain machine learning algorithms",
                "What are neural networks?",
            ]

            for question in questions:
                response = await fileintel_client.query(
                    collection=test_collection,
                    question=question,
                    max_sources=2,
                )
                assert response.answer is not None
                assert isinstance(response.sources, list)

        except CollectionNotFoundError:
            pytest.skip(f"Test collection '{test_collection}' not found")

    @pytest.mark.asyncio
    async def test_source_metadata_complete(self, fileintel_client, test_collection):
        """Test that source metadata is complete and properly parsed."""
        try:
            response = await fileintel_client.query(
                collection=test_collection,
                question="test query",
                max_sources=5,
            )

            if response.sources:
                for source in response.sources:
                    # Check document metadata
                    assert source.document_metadata is not None
                    assert source.document_metadata.title is not None

                    # Check chunk metadata
                    assert source.chunk_metadata is not None

                    # Check scores
                    assert isinstance(source.similarity_score, float)
                    assert isinstance(source.relevance_score, float)
                    assert 0.0 <= source.similarity_score <= 1.0
                    assert 0.0 <= source.relevance_score <= 1.0

        except CollectionNotFoundError:
            pytest.skip(f"Test collection '{test_collection}' not found")

    @pytest.mark.asyncio
    async def test_citation_formats(self, fileintel_client, test_collection):
        """Test that citation formats are properly provided."""
        try:
            response = await fileintel_client.query(
                collection=test_collection,
                question="test citation formats",
                max_sources=3,
            )

            if response.sources:
                for source in response.sources:
                    # Both citation formats should be present
                    assert source.citation is not None
                    assert len(source.citation) > 0
                    assert source.in_text_citation is not None
                    assert len(source.in_text_citation) > 0

        except CollectionNotFoundError:
            pytest.skip(f"Test collection '{test_collection}' not found")
