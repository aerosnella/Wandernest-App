"""Content-safety checks: local rules + Azure AI Content Safety, combined in ``SafetyValidator``."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

AZURE_TEXT_LIMIT = 10_000


@dataclass
class SafetyVerdict:
    safe: bool
    reasons: list[str] = field(default_factory=list)
    categories: dict[str, int] = field(default_factory=dict)  # Azure category -> severity
    source: str = "local"


class ContentSafetyChecker:
    """Offline rules: prompt-injection attempts and clearly harmful requests."""

    INJECTION_PATTERNS = [
        r"ignore (all |any )?(the )?(previous|prior|above) (instructions|prompts?|rules)",
        r"disregard (all |any )?(the )?(previous|prior|above|your) (instructions|rules)",
        r"(reveal|show|print|repeat) (me )?(your |the )?(system|hidden|initial) (prompt|instructions)",
        r"you are now (in )?(dan|developer mode|jailbreak)",
        r"\bjailbreak\b",
        r"act as (an? )?(unrestricted|unfiltered)",
    ]
    HARMFUL_PATTERNS = [
        r"how (to|do i|can i) (make|build|create) (a )?(bomb|explosive|weapon)",
        r"how (to|do i|can i) (smuggle|hide) (drugs|weapons|contraband)",
        r"how (to|do i|can i) (forge|fake) (a )?(passport|visa|ticket|boarding pass)",
        r"\b(kill|murder|hurt) (myself|someone|people)\b",
        r"\b(suicide|self[- ]harm)\b",
        r"\b(hijack|bomb threat)\b",
    ]

    def __init__(self) -> None:
        self._injection = [re.compile(p, re.IGNORECASE) for p in self.INJECTION_PATTERNS]
        self._harmful = [re.compile(p, re.IGNORECASE) for p in self.HARMFUL_PATTERNS]

    def check(self, text: str) -> SafetyVerdict:
        reasons: list[str] = []
        if any(p.search(text) for p in self._injection):
            reasons.append("prompt_injection")
        if any(p.search(text) for p in self._harmful):
            reasons.append("harmful_content")
        return SafetyVerdict(safe=not reasons, reasons=reasons, source="local")


class AzureContentSafetyValidator:
    """Calls Azure AI Content Safety (Hate, SelfHarm, Sexual, Violence) and applies a severity limit."""

    def __init__(self, endpoint: str, key: str, max_severity: int = 2, client=None):
        self.max_severity = max_severity
        if client is not None:  # injected (tests)
            self.client = client
            return
        from azure.ai.contentsafety import ContentSafetyClient
        from azure.core.credentials import AzureKeyCredential

        self.client = ContentSafetyClient(endpoint, AzureKeyCredential(key))

    def check(self, text: str) -> SafetyVerdict:
        from azure.ai.contentsafety.models import AnalyzeTextOptions

        response = self.client.analyze_text(AnalyzeTextOptions(text=text[:AZURE_TEXT_LIMIT]))
        categories = {str(getattr(item.category, "value", item.category)): int(item.severity or 0)
                      for item in response.categories_analysis}
        flagged = [f"azure_{name.lower()}" for name, sev in categories.items() if sev > self.max_severity]
        return SafetyVerdict(safe=not flagged, reasons=flagged, categories=categories, source="azure")


class SafetyValidator:
    """Runs local rules first, then Azure Content Safety when configured.

    If the Azure call fails, the local verdict is used and ``degraded`` is set
    (the service must not become unavailable because the safety API is down).
    """

    def __init__(self, azure: AzureContentSafetyValidator | None = None,
                 local: ContentSafetyChecker | None = None):
        self.azure = azure
        self.local = local or ContentSafetyChecker()
        self.degraded = False

    @classmethod
    def from_config(cls, cfg) -> "SafetyValidator":
        azure = None
        if cfg.content_safety_enabled:
            azure = AzureContentSafetyValidator(cfg.content_safety_endpoint, cfg.content_safety_key,
                                                cfg.content_safety_max_severity)
        else:
            logger.warning("Azure Content Safety is not configured - using local safety rules only")
        return cls(azure=azure)

    def validate(self, text: str) -> SafetyVerdict:
        local = self.local.check(text)
        if not local.safe or self.azure is None:
            return local
        try:
            self.degraded = False
            return self.azure.check(text)
        except Exception as exc:
            self.degraded = True
            logger.error("Azure Content Safety call failed (%s); using local verdict", exc)
            return local
