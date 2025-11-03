"""LLM client for claim inversion and content generation."""

from typing import Optional

from openai import AsyncOpenAI


class LLMError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMClient:
    """Async LLM client using OpenAI-compatible API.

    This client uses the same OpenAI-compatible endpoint as FileIntel,
    typically a local model server like Ollama or vLLM.

    Example:
        client = LLMClient(
            base_url="http://192.168.0.247:9003/v1",
            model="gemma3-12b-awq",
            api_key="ollama"
        )
        inverted = await client.invert_claim("Agile reduces development time")
    """

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str = "ollama",
        temperature: float = 0.1,
    ) -> None:
        """Initialize LLM client.

        Args:
            base_url: OpenAI-compatible API base URL
            model: Model name (e.g., "gemma3-12b-awq")
            api_key: API key (default "ollama" for local setups)
            temperature: Temperature for generation (0.0-2.0)
        """
        self.model = model
        self.temperature = temperature
        self.client = AsyncOpenAI(
            base_url=base_url,
            api_key=api_key,
        )

    async def invert_claim(self, claim: str) -> str:
        """Invert a claim to generate opposing search query.

        This generates a search query that would find evidence contradicting
        the original claim.

        Args:
            claim: Original claim to invert

        Returns:
            Inverted claim/search query for finding counterarguments

        Raises:
            LLMError: If LLM call fails
        """
        prompt = f"""You are helping with academic research. Given a claim, generate a search query that would find OPPOSING or CONTRADICTING evidence.

Original Claim: {claim}

Generate a concise search query (3-6 keywords) that captures the OPPOSITE perspective or potential counterarguments. Focus on:
- Opposite outcomes (e.g., reduces → increases)
- Challenges or limitations
- Contradictory findings

Search Query:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=self.temperature,
                max_tokens=100,  # Short query, don't need many tokens
            )

            inverted_claim = response.choices[0].message.content
            if inverted_claim:
                return inverted_claim.strip()
            else:
                raise LLMError("LLM returned empty response")

        except Exception as e:
            raise LLMError(f"Failed to invert claim: {e}")

    async def close(self) -> None:
        """Close the LLM client connection."""
        await self.client.close()
