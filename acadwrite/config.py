"""Configuration management for AcadWrite."""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FileIntelSettings(BaseSettings):
    """FileIntel RAG platform configuration."""

    base_url: str = Field(default="http://localhost:8000", description="FileIntel API URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")

    model_config = SettingsConfigDict(env_prefix="FILEINTEL_")


class LLMSettings(BaseSettings):
    """LLM provider configuration.

    Configured to use the same OpenAI-compatible API as FileIntel.
    """

    provider: str = Field(default="openai", description="LLM provider")
    model: str = Field(default="gemma3-12b-awq", description="Model name")
    base_url: str = Field(
        default="http://192.168.0.247:9003/v1", description="OpenAI-compatible API base URL"
    )
    api_key: str = Field(default="ollama", description="API key")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="Temperature")
    context_length: int = Field(default=128000, description="Model context length")
    rate_limit: int = Field(default=999, description="Rate limit requests/min")

    model_config = SettingsConfigDict(env_prefix="LLM_")


class WritingSettings(BaseSettings):
    """Writing output configuration."""

    citation_style: Literal["inline", "footnote", "endnote"] = Field(
        default="footnote", description="Citation style"
    )
    markdown_dialect: Literal["gfm", "pandoc", "commonmark"] = Field(
        default="gfm", description="Markdown dialect"
    )
    include_relevance_scores: bool = Field(
        default=False, description="Include relevance scores in output"
    )

    model_config = SettingsConfigDict(env_prefix="WRITING_")


class GenerationSettings(BaseSettings):
    """Content generation configuration."""

    context_window: int = Field(
        default=500, description="Characters from previous section for context"
    )
    min_sources_per_section: int = Field(default=3, description="Minimum sources required")
    max_sources_per_section: int = Field(default=10, description="Maximum sources to use")

    model_config = SettingsConfigDict(env_prefix="GENERATION_")


class Settings(BaseSettings):
    """Main application settings."""

    fileintel: FileIntelSettings = Field(default_factory=FileIntelSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    writing: WritingSettings = Field(default_factory=WritingSettings)
    generation: GenerationSettings = Field(default_factory=GenerationSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    @classmethod
    def from_yaml(cls, path: Path) -> "Settings":
        """Load settings from YAML file.

        Args:
            path: Path to YAML config file

        Returns:
            Settings instance with values from YAML
        """
        with open(path) as f:
            config_data = yaml.safe_load(f)

        return cls(
            fileintel=FileIntelSettings(**config_data.get("fileintel", {})),
            llm=LLMSettings(**config_data.get("llm", {})),
            writing=WritingSettings(**config_data.get("writing", {})),
            generation=GenerationSettings(**config_data.get("generation", {})),
        )

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Settings":
        """Load settings from config file or environment.

        Priority (highest first):
        1. Environment variables
        2. Config file (if provided)
        3. Defaults

        Args:
            config_path: Optional path to config file

        Returns:
            Settings instance
        """
        if config_path and config_path.exists():
            return cls.from_yaml(config_path)
        return cls()
