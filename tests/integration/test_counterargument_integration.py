"""Integration tests for Counterargument Generator workflow."""

import pytest

from acadwrite.workflows.counterargument import CounterargumentGenerator


class TestCounterargumentIntegration:
    """Integration tests for counterargument generation with real FileIntel and LLM."""

    @pytest.mark.asyncio
    async def test_generate_counterargument_basic(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test basic counterargument generation."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            report = await generator.generate(
                claim="Machine learning improves software development productivity",
                collection=test_collection,
                depth="quick",
            )

            # Verify report structure
            assert report.original_claim == "Machine learning improves software development productivity"
            assert report.inverted_claim is not None
            assert len(report.inverted_claim) > 0

            # Should have supporting and opposing evidence
            assert isinstance(report.supporting_evidence, list)
            assert isinstance(report.opposing_evidence, list)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_different_depths(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test counterargument generation with different depth levels."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            claim = "Deep learning is effective for image classification"

            # Quick depth
            report_quick = await generator.generate(
                claim=claim, collection=test_collection, depth="quick"
            )

            # Standard depth
            report_standard = await generator.generate(
                claim=claim, collection=test_collection, depth="standard"
            )

            # Deep analysis
            report_deep = await generator.generate(
                claim=claim, collection=test_collection, depth="deep"
            )

            # All should return valid reports
            assert report_quick.original_claim == claim
            assert report_standard.original_claim == claim
            assert report_deep.original_claim == claim

            # Different depths should potentially return different amounts of evidence
            # (though this depends on available sources)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_synthesis(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test counterargument generation with synthesis."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            report = await generator.generate(
                claim="Agile development reduces project costs",
                collection=test_collection,
                depth="standard",
                synthesis=True,
            )

            # Verify synthesis was generated
            assert report.synthesis is not None
            assert len(report.synthesis) > 0

            # Synthesis should provide balanced view
            assert isinstance(report.synthesis, str)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_max_sources(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test that max_sources parameter is respected."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            report = await generator.generate(
                claim="Neural networks are computationally efficient",
                collection=test_collection,
                depth="standard",
                max_sources=2,
            )

            # Should respect max_sources for both supporting and opposing
            assert len(report.supporting_evidence) <= 2
            assert len(report.opposing_evidence) <= 2

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_generate_claim_inversion(self, fileintel_client, llm_client, test_collection):
        """Test that claim inversion is working correctly."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            claim = "AI increases employment opportunities"

            report = await generator.generate(
                claim=claim, collection=test_collection, depth="quick"
            )

            # Inverted claim should be different from original
            assert report.inverted_claim != claim
            assert report.inverted_claim is not None
            assert len(report.inverted_claim) > 0

            # Inverted claim should capture opposite perspective
            # (exact content depends on LLM)

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_generate_with_long_claim(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test counterargument generation with long complex claim."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            long_claim = (
                "Machine learning algorithms, particularly deep neural networks "
                "with multiple hidden layers and sophisticated architectures, "
                "have demonstrated superior performance in complex pattern recognition "
                "tasks compared to traditional statistical methods across various domains"
            )

            report = await generator.generate(
                claim=long_claim, collection=test_collection, depth="quick"
            )

            assert report.original_claim == long_claim
            assert report.inverted_claim is not None

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_generate_evidence_structure(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test that evidence has proper structure."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            report = await generator.generate(
                claim="Cloud computing reduces IT infrastructure costs",
                collection=test_collection,
                depth="standard",
            )

            # Check supporting evidence structure
            if report.supporting_evidence:
                for evidence in report.supporting_evidence:
                    assert evidence.text is not None
                    assert evidence.citation is not None
                    assert evidence.relevance_score is not None
                    assert 0.0 <= evidence.relevance_score <= 1.0

            # Check opposing evidence structure
            if report.opposing_evidence:
                for evidence in report.opposing_evidence:
                    assert evidence.text is not None
                    assert evidence.citation is not None
                    assert evidence.relevance_score is not None
                    assert 0.0 <= evidence.relevance_score <= 1.0

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise

    @pytest.mark.asyncio
    async def test_generate_multiple_claims(
        self, fileintel_client, llm_client, test_collection
    ):
        """Test generating counterarguments for multiple claims."""
        try:
            generator = CounterargumentGenerator(
                fileintel_client=fileintel_client, llm_client=llm_client
            )

            claims = [
                "DevOps practices improve software quality",
                "Test-driven development reduces bugs",
                "Code reviews increase development time",
            ]

            reports = []
            for claim in claims:
                report = await generator.generate(
                    claim=claim, collection=test_collection, depth="quick"
                )
                reports.append(report)

            # All should succeed
            assert len(reports) == 3

            for report in reports:
                assert report.original_claim in claims
                assert report.inverted_claim is not None

        except Exception as e:
            if "not found" in str(e).lower():
                pytest.skip(f"Test collection '{test_collection}' not found")
            if "connection" in str(e).lower():
                pytest.skip("LLM endpoint not available")
            raise
