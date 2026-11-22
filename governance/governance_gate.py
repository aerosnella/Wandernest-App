"""GovernanceGate: single entry point that screens user queries and model answers."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from governance.pii_detector import PIIDetector
from governance.safety_validator import SafetyValidator

logger = logging.getLogger(__name__)

BLOCKED_MESSAGE = ("I'm sorry, I can't help with that request. I can answer questions about baggage, "
                   "refunds, visas, flight disruptions and travel advisories for WanderNest bookings.")
UNSAFE_OUTPUT_MESSAGE = "I'm sorry, I can't share that response. Please contact a WanderNest agent for help."


@dataclass
class GateResult:
    allowed: bool
    text: str                                   # sanitised text that downstream code should use
    reasons: list[str] = field(default_factory=list)
    pii_types: list[str] = field(default_factory=list)
    safety_source: str = "local"

    @property
    def message(self) -> str:
        return "" if self.allowed else BLOCKED_MESSAGE


class GovernanceGate:
    """Order of checks: length/empty -> PII redaction -> content safety."""

    def __init__(self, pii_detector: PIIDetector | None = None,
                 safety_validator: SafetyValidator | None = None, max_query_chars: int = 1000):
        self.pii = pii_detector or PIIDetector()
        self.safety = safety_validator or SafetyValidator()
        self.max_query_chars = max_query_chars
        self.audit_log: list[dict] = []

    def _audit(self, stage: str, result: GateResult) -> None:
        entry = {"stage": stage, "allowed": result.allowed, "reasons": result.reasons, "pii": result.pii_types}
        self.audit_log.append(entry)
        logger.info("governance %s", entry)

    def check_input(self, query: str) -> GateResult:
        query = (query or "").strip()
        if not query:
            result = GateResult(False, "", ["empty_query"])
        elif len(query) > self.max_query_chars:
            result = GateResult(False, "", ["query_too_long"])
        else:
            # PII is removed first so personal data is never sent to the search index or LLM.
            sanitized, pii_types = self.pii.redact(query)
            verdict = self.safety.validate(sanitized)
            result = GateResult(verdict.safe, sanitized if verdict.safe else "", list(verdict.reasons),
                                pii_types, verdict.source)
            if pii_types:
                result.reasons.append("pii_redacted")
        self._audit("input", result)
        return result

    def check_output(self, answer: str) -> GateResult:
        sanitized, pii_types = self.pii.redact(answer or "")
        verdict = self.safety.validate(sanitized)
        if not verdict.safe:
            result = GateResult(False, UNSAFE_OUTPUT_MESSAGE, list(verdict.reasons), pii_types, verdict.source)
        else:
            reasons = ["pii_redacted"] if pii_types else []
            result = GateResult(True, sanitized, reasons, pii_types, verdict.source)
        self._audit("output", result)
        return result

    @classmethod
    def from_config(cls, cfg) -> "GovernanceGate":
        return cls(safety_validator=SafetyValidator.from_config(cfg))
