"""Central, validated configuration for the WanderNest RAG chatbot.

All secrets come from environment variables (loaded from ``.env``); nothing is hard-coded.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

PLACEHOLDER_MARKERS = ("<", "your-", "changeme")


class ConfigError(ValueError):
    """Raised when required configuration is missing or invalid."""


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_int(name: str, default: int) -> int:
    raw = _env(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer, got '{raw}'") from exc


def _is_placeholder(value: str) -> bool:
    return any(marker in value.lower() for marker in PLACEHOLDER_MARKERS)


@dataclass(frozen=True)
class Config:
    # Azure OpenAI
    openai_api_key: str = field(default_factory=lambda: _env("AZURE_OPENAI_API_KEY"), repr=False)
    openai_endpoint: str = field(default_factory=lambda: _env("AZURE_OPENAI_ENDPOINT"))
    openai_api_version: str = field(default_factory=lambda: _env("AZURE_OPENAI_API_VERSION", "2024-06-01"))
    chat_deployment: str = field(default_factory=lambda: _env("AZURE_OPENAI_CHAT_DEPLOYMENT"))
    embedding_deployment: str = field(default_factory=lambda: _env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"))

    # Azure AI Search
    search_endpoint: str = field(default_factory=lambda: _env("AZURE_SEARCH_ENDPOINT"))
    search_key: str = field(default_factory=lambda: _env("AZURE_SEARCH_KEY"), repr=False)
    search_index_name: str = field(default_factory=lambda: _env("AZURE_SEARCH_INDEX_NAME", "wandernest-travel-index"))

    # Azure AI Content Safety (optional)
    content_safety_endpoint: str = field(default_factory=lambda: _env("AZURE_CONTENT_SAFETY_ENDPOINT"))
    content_safety_key: str = field(default_factory=lambda: _env("AZURE_CONTENT_SAFETY_KEY"), repr=False)
    content_safety_max_severity: int = field(default_factory=lambda: _env_int("CONTENT_SAFETY_MAX_SEVERITY", 2))

    # RAG parameters
    chunk_size: int = field(default_factory=lambda: _env_int("CHUNK_SIZE", 1000))
    chunk_overlap: int = field(default_factory=lambda: _env_int("CHUNK_OVERLAP", 150))
    top_k: int = field(default_factory=lambda: _env_int("TOP_K", 4))

    data_dir: Path = BASE_DIR / "data"
    results_dir: Path = BASE_DIR / "evaluation" / "results"

    REQUIRED_OPENAI = ("openai_api_key", "openai_endpoint", "chat_deployment", "embedding_deployment")
    REQUIRED_SEARCH = ("search_endpoint", "search_key", "search_index_name")

    @property
    def content_safety_enabled(self) -> bool:
        return bool(self.content_safety_endpoint and self.content_safety_key
                    and not _is_placeholder(self.content_safety_endpoint)
                    and not _is_placeholder(self.content_safety_key))

    def validate(self, require_search: bool = True) -> "Config":
        """Raise ``ConfigError`` listing every missing / placeholder / invalid setting."""
        problems: list[str] = []
        required = list(self.REQUIRED_OPENAI) + (list(self.REQUIRED_SEARCH) if require_search else [])
        env_names = {
            "openai_api_key": "AZURE_OPENAI_API_KEY", "openai_endpoint": "AZURE_OPENAI_ENDPOINT",
            "chat_deployment": "AZURE_OPENAI_CHAT_DEPLOYMENT",
            "embedding_deployment": "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "search_endpoint": "AZURE_SEARCH_ENDPOINT", "search_key": "AZURE_SEARCH_KEY",
            "search_index_name": "AZURE_SEARCH_INDEX_NAME",
        }
        for attr in required:
            value = getattr(self, attr)
            if not value:
                problems.append(f"{env_names[attr]} is not set")
            elif _is_placeholder(value):
                problems.append(f"{env_names[attr]} still contains a placeholder value")

        for attr in ("openai_endpoint", "search_endpoint"):
            value = getattr(self, attr)
            if value and not value.startswith("https://"):
                problems.append(f"{env_names[attr]} must start with https://")

        if self.chunk_size <= 0:
            problems.append("CHUNK_SIZE must be > 0")
        if not 0 <= self.chunk_overlap < max(self.chunk_size, 1):
            problems.append("CHUNK_OVERLAP must be >= 0 and smaller than CHUNK_SIZE")
        if self.top_k <= 0:
            problems.append("TOP_K must be > 0")
        if not 0 <= self.content_safety_max_severity <= 7:
            problems.append("CONTENT_SAFETY_MAX_SEVERITY must be between 0 and 7")

        if problems:
            raise ConfigError("Invalid configuration:\n  - " + "\n  - ".join(problems)
                              + "\nCopy .env.example to .env and fill in the values.")
        return self


def get_config(validate: bool = True, require_search: bool = True) -> Config:
    cfg = Config()
    return cfg.validate(require_search=require_search) if validate else cfg
