"""Rule-based PII detection and redaction (emails, phones, cards, Aadhaar, PAN, passports, SSN)."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PIIMatch:
    pii_type: str
    start: int
    end: int
    text: str


def _luhn_valid(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


class PIIDetector:
    """Finds personal data in free text. Patterns are listed from highest to lowest priority."""

    PATTERNS: list[tuple[str, re.Pattern]] = [
        ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
        ("CREDIT_CARD", re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")),
        ("AADHAAR", re.compile(r"(?<!\d)[2-9]\d{3}[ -]?\d{4}[ -]?\d{4}(?!\d)")),
        ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
        ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
        ("PHONE", re.compile(r"(?<!\d)(?:\+\d{1,3}[ -]?)?[6-9]\d{4}[ -]?\d{5}(?!\d)|(?<!\w)\+\d{1,3}[ -]?\d[\d -]{7,12}\d(?!\d)")),
        ("PASSPORT", re.compile(r"\b(?:passport\s*(?:no\.?|number|#)?\s*:?\s*)([A-Z][0-9]{7})\b", re.IGNORECASE)),
    ]

    def detect(self, text: str) -> list[PIIMatch]:
        matches: list[PIIMatch] = []
        taken: list[tuple[int, int]] = []
        for pii_type, pattern in self.PATTERNS:
            for m in pattern.finditer(text):
                start, end = m.span()
                if pii_type == "CREDIT_CARD" and not _luhn_valid(m.group()):
                    continue
                if pii_type == "PHONE" and len(re.sub(r"\D", "", m.group())) < 10:
                    continue
                if any(start < t_end and end > t_start for t_start, t_end in taken):
                    continue
                taken.append((start, end))
                matches.append(PIIMatch(pii_type, start, end, m.group()))
        return sorted(matches, key=lambda x: x.start)

    def contains_pii(self, text: str) -> bool:
        return bool(self.detect(text))

    def redact(self, text: str) -> tuple[str, list[str]]:
        """Return the text with each PII span replaced by ``[TYPE]`` plus the types found."""
        matches = self.detect(text)
        redacted = text
        for m in reversed(matches):
            redacted = redacted[:m.start] + f"[{m.pii_type}]" + redacted[m.end:]
        return redacted, sorted({m.pii_type for m in matches})
