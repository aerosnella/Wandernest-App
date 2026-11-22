"""TravelSearchEngine: governed retrieval (Azure AI Search) + grounded answer synthesis (Azure OpenAI)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from governance.governance_gate import GovernanceGate

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are WanderNest Travels' virtual assistant for travellers flying from BLR, DEL and BOM \
to LON, JFK, DXB and BKK.

Rules:
1. Answer ONLY from the numbered context passages below. Do not use outside knowledge.
2. If the context does not contain the answer, say you do not have that information and suggest contacting a \
WanderNest agent. Never guess about fees, refunds, baggage allowances or visa rules.
3. Passages from "update" documents are the latest real-time information; if they conflict with a static \
policy, prefer the update and say so.
4. Cite the passages you used as [1], [2], ... after the relevant sentence.
5. Be concise, friendly and practical. Never ask for or repeat personal data (passport, card, phone numbers).

Context:
{context}
"""


@dataclass
class SearchResult:
    content: str
    source: str
    category: str = "general"
    doc_type: str = "static"
    page: int | None = None
    score: float | None = None

    @classmethod
    def from_document(cls, doc, score: float | None = None) -> "SearchResult":
        md = doc.metadata or {}
        return cls(content=doc.page_content, source=md.get("source", "unknown"),
                   category=md.get("category", "general"), doc_type=md.get("doc_type", "static"),
                   page=md.get("page"), score=score)


@dataclass
class ChatResponse:
    query: str
    answer: str
    sources: list[SearchResult] = field(default_factory=list)
    blocked: bool = False
    reasons: list[str] = field(default_factory=list)
    pii_types: list[str] = field(default_factory=list)

    @property
    def contexts(self) -> list[str]:
        return [s.content for s in self.sources]


class TravelSearchEngine:
    """Public API: ``search_by_text``, ``synthesize_response`` and the end-to-end ``ask``."""

    NO_ANSWER = ("I couldn't find anything about that in WanderNest's policies or latest travel updates. "
                 "Please contact a WanderNest agent for help.")

    def __init__(self, vector_store, llm, gate: GovernanceGate | None = None, top_k: int = 4):
        self.vector_store = vector_store
        self.llm = llm
        self.gate = gate or GovernanceGate()
        self.top_k = top_k

    @classmethod
    def from_config(cls, cfg) -> "TravelSearchEngine":
        from src.vector_store import get_embeddings, get_llm, get_vector_store

        embeddings = get_embeddings(cfg)
        return cls(get_vector_store(cfg, embeddings), get_llm(cfg), GovernanceGate.from_config(cfg), cfg.top_k)

    def search_by_text(self, query: str, k: int | None = None) -> list[SearchResult]:
        """Vector similarity search for already-sanitised text."""
        k = k or self.top_k
        if hasattr(self.vector_store, "similarity_search_with_score"):
            hits = self.vector_store.similarity_search_with_score(query, k=k)
        else:
            hits = [(d, None) for d in self.vector_store.similarity_search(query, k=k)]
        return [SearchResult.from_document(doc, score) for doc, score in hits]

    @staticmethod
    def _format_context(results: list[SearchResult]) -> str:
        blocks = []
        for i, r in enumerate(results, start=1):
            tag = "UPDATE" if r.doc_type == "update" else "POLICY"
            blocks.append(f"[{i}] ({tag} | {r.category} | {r.source}) {r.content}")
        return "\n\n".join(blocks)

    def synthesize_response(self, query: str, results: list[SearchResult]) -> str:
        """Generate an answer grounded in the retrieved passages only."""
        if not results:
            return self.NO_ANSWER
        messages = [("system", SYSTEM_PROMPT.format(context=self._format_context(results))),
                    ("human", query)]
        reply = self.llm.invoke(messages)
        return getattr(reply, "content", str(reply)).strip()

    def ask(self, query: str, k: int | None = None) -> ChatResponse:
        """Governance-checked question answering: input gate -> retrieve -> synthesise -> output gate."""
        gate_in = self.gate.check_input(query)
        if not gate_in.allowed:
            return ChatResponse(query=query, answer=gate_in.message, blocked=True, reasons=gate_in.reasons)

        try:
            results = self.search_by_text(gate_in.text, k)
            answer = self.synthesize_response(gate_in.text, results)
        except Exception as exc:
            logger.exception("Search/synthesis failed")
            return ChatResponse(query=gate_in.text, answer="Sorry, something went wrong while looking that up. "
                                "Please try again or contact a WanderNest agent.", blocked=False,
                                reasons=[f"error:{type(exc).__name__}"])

        gate_out = self.gate.check_output(answer)
        return ChatResponse(query=gate_in.text, answer=gate_out.text, sources=results if gate_out.allowed else [],
                            blocked=not gate_out.allowed, reasons=gate_in.reasons + gate_out.reasons,
                            pii_types=sorted(set(gate_in.pii_types + gate_out.pii_types)))
