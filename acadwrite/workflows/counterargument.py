"""Counterargument generator workflow for balanced analysis."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from acadwrite.models.query import QueryResponse, Source
from acadwrite.services import FileIntelClient, LLMClient


class AnalysisDepth(Enum):
    """Analysis depth for counterargument generation."""

    QUICK = "quick"  # Single query for each side
    STANDARD = "standard"  # Standard analysis
    DEEP = "deep"  # Multiple queries and detailed analysis


@dataclass
class Evidence:
    """Evidence for or against a claim."""

    source: Source
    key_point: str
    relevance: str

    @property
    def citation(self) -> str:
        """Get formatted citation from source."""
        return self.source.citation

    @property
    def snippet(self) -> str:
        """Get text snippet from source."""
        return self.source.text

    @property
    def title(self) -> str:
        """Get document title."""
        return self.source.document_metadata.title

    @property
    def year(self) -> Optional[str]:
        """Get publication year."""
        return self.source.document_metadata.publication_date

    @property
    def page(self) -> Optional[int]:
        """Get page number."""
        return self.source.chunk_metadata.page_number


@dataclass
class CounterargumentReport:
    """Report containing supporting and contradicting evidence."""

    original_claim: str
    inverted_claim: str
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    synthesis: Optional[str] = None
    depth: AnalysisDepth = AnalysisDepth.STANDARD


class CounterargumentGenerator:
    """Generate counterargument analysis for claims.

    This workflow:
    1. Queries FileIntel for evidence supporting the original claim
    2. Uses LLM to invert the claim
    3. Queries FileIntel for evidence supporting the inverted claim (contradicting original)
    4. Optionally synthesizes findings with LLM

    Example:
        async with FileIntelClient("http://localhost:8000") as fileintel:
            llm = LLMClient(base_url="http://localhost:9003/v1", model="gemma3-12b-awq")
            generator = CounterargumentGenerator(fileintel, llm)

            report = await generator.generate(
                claim="Agile reduces development time",
                collection="thesis_sources",
                depth=AnalysisDepth.STANDARD,
                include_synthesis=True,
            )

            print(f"Supporting: {len(report.supporting_evidence)} sources")
            print(f"Contradicting: {len(report.contradicting_evidence)} sources")
    """

    def __init__(
        self,
        fileintel: FileIntelClient,
        llm: LLMClient,
    ) -> None:
        """Initialize counterargument generator.

        Args:
            fileintel: FileIntel client for querying documents
            llm: LLM client for claim inversion and synthesis
        """
        self.fileintel = fileintel
        self.llm = llm

    async def generate(
        self,
        claim: str,
        collection: str,
        depth: AnalysisDepth = AnalysisDepth.STANDARD,
        include_synthesis: bool = False,
        max_sources_per_side: int = 5,
    ) -> CounterargumentReport:
        """Generate counterargument analysis for a claim.

        Args:
            claim: Original claim to analyze
            collection: FileIntel collection name
            depth: Analysis depth
            include_synthesis: Whether to generate LLM synthesis
            max_sources_per_side: Maximum sources per side

        Returns:
            CounterargumentReport with evidence from both sides

        Raises:
            FileIntelError: If queries fail
            LLMError: If LLM operations fail
        """
        # Query for supporting evidence (original claim)
        supporting_response = await self.fileintel.query(
            collection=collection,
            question=claim,
            search_type="vector",
            max_results=max_sources_per_side,
        )

        # Use LLM to invert the claim
        inverted_claim = await self.llm.invert_claim(claim)

        # Query for contradicting evidence (inverted claim)
        contradicting_response = await self.fileintel.query(
            collection=collection,
            question=inverted_claim,
            search_type="vector",
            max_results=max_sources_per_side,
        )

        # Build evidence lists
        supporting_evidence = self._build_evidence_list(
            supporting_response, "Supports original claim"
        )
        contradicting_evidence = self._build_evidence_list(
            contradicting_response, "Supports opposing view"
        )

        # Optional synthesis
        synthesis = None
        if include_synthesis:
            synthesis = await self._synthesize(
                claim,
                inverted_claim,
                supporting_evidence,
                contradicting_evidence,
            )

        return CounterargumentReport(
            original_claim=claim,
            inverted_claim=inverted_claim,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            synthesis=synthesis,
            depth=depth,
        )

    def _build_evidence_list(
        self,
        response: QueryResponse,
        relevance_note: str,
    ) -> List[Evidence]:
        """Build evidence list from query response.

        Args:
            response: Query response from FileIntel
            relevance_note: Note about relevance to claim

        Returns:
            List of Evidence objects
        """
        evidence_list = []

        for source in response.sources:
            # Extract key point from the source text
            # Take first sentence or up to 200 chars
            key_point = self._extract_key_point(source.text)

            evidence = Evidence(
                source=source,
                key_point=key_point,
                relevance=relevance_note,
            )
            evidence_list.append(evidence)

        return evidence_list

    def _extract_key_point(self, text: str, max_length: int = 200) -> str:
        """Extract key point from source text.

        Args:
            text: Source text
            max_length: Maximum length of key point

        Returns:
            Extracted key point
        """
        # Try to get first sentence
        for delimiter in [".", "!", "?"]:
            idx = text.find(delimiter)
            if 0 < idx < max_length:
                return text[: idx + 1].strip()

        # Otherwise truncate at max_length
        if len(text) > max_length:
            return text[:max_length].strip() + "..."

        return text.strip()

    async def _synthesize(
        self,
        original_claim: str,
        inverted_claim: str,
        supporting: List[Evidence],
        contradicting: List[Evidence],
    ) -> str:
        """Generate synthesis of findings using LLM.

        Args:
            original_claim: Original claim
            inverted_claim: Inverted claim
            supporting: Supporting evidence
            contradicting: Contradicting evidence

        Returns:
            Synthesis text
        """
        # Build synthesis prompt
        prompt = f"""You are analyzing academic evidence about a claim.

Original Claim: {original_claim}
Opposing View: {inverted_claim}

Supporting Evidence ({len(supporting)} sources):
"""

        for i, ev in enumerate(supporting[:3], 1):  # Show top 3
            prompt += f"{i}. {ev.key_point}\n"

        prompt += f"\nContradicting Evidence ({len(contradicting)} sources):\n"

        for i, ev in enumerate(contradicting[:3], 1):  # Show top 3
            prompt += f"{i}. {ev.key_point}\n"

        prompt += """
Based on this evidence, provide a brief (2-3 sentence) synthesis that:
1. Acknowledges the complexity of the issue
2. Notes the strength of evidence on each side
3. Suggests conditions or contexts where each view might apply

Synthesis:"""

        # Use a simple completion call
        # Note: We're reusing invert_claim infrastructure but with custom prompt
        # In a real implementation, you might add a generic completion method to LLMClient
        response = await self.llm.client.chat.completions.create(
            model=self.llm.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.llm.temperature,
            max_tokens=200,
        )

        synthesis = response.choices[0].message.content
        if synthesis:
            return synthesis.strip()

        return "Unable to generate synthesis."
