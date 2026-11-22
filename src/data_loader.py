"""Loads WanderNest PDFs from ``data/``, tags them by filename and splits them into chunks."""
from __future__ import annotations

import logging
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# Ordered rules: the first keyword found in the lower-cased filename decides the category.
CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("disruption_event", ("strike", "weather", "delay", "disruption")),
    ("baggage_policy", ("baggage", "luggage")),
    ("refund_policy", ("refund", "cancel")),
    ("visa_immigration", ("visa", "immigration")),
    ("fare_update", ("fare", "surcharge")),
    ("safety_advisory", ("advisory", "safety", "health")),
    ("route_info", ("route",)),
    ("faq", ("faq",)),
]
UPDATE_PREFIX = "update_"  # files starting with this are real-time updates, not static policy


class TravelDataLoader:
    """Reads every PDF in ``data_dir`` and returns chunked LangChain ``Document`` objects."""

    def __init__(self, data_dir: str | Path, chunk_size: int = 1000, chunk_overlap: int = 150):
        self.data_dir = Path(data_dir)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @staticmethod
    def categorize(filename: str) -> str:
        """Derive the document category from the filename."""
        name = filename.lower()
        for category, keywords in CATEGORY_RULES:
            if any(k in name for k in keywords):
                return category
        return "general"

    @staticmethod
    def is_update(filename: str) -> bool:
        return filename.lower().startswith(UPDATE_PREFIX)

    def list_pdfs(self) -> list[Path]:
        if not self.data_dir.is_dir():
            raise FileNotFoundError(f"Data folder not found: {self.data_dir}")
        return sorted(self.data_dir.glob("*.pdf"))

    def load_documents(self) -> list[Document]:
        """Load each PDF page as a Document with source/category/doc_type metadata."""
        from langchain_community.document_loaders import PyPDFLoader

        pdfs = self.list_pdfs()
        if not pdfs:
            raise FileNotFoundError(f"No PDF files found in {self.data_dir}")

        documents: list[Document] = []
        for pdf in pdfs:
            try:
                pages = PyPDFLoader(str(pdf)).load()
            except Exception as exc:  # a corrupt file must not stop the whole ingestion
                logger.error("Skipping %s: %s", pdf.name, exc)
                continue
            category = self.categorize(pdf.name)
            doc_type = "update" if self.is_update(pdf.name) else "static"
            for page in pages:
                page.page_content = re.sub(r"[ \t]+", " ", page.page_content).strip()
                if not page.page_content:
                    continue
                page.metadata = {
                    "source": pdf.name,
                    "category": category,
                    "doc_type": doc_type,
                    "page": int(page.metadata.get("page", 0)) + 1,
                }
                documents.append(page)
            logger.info("Loaded %s (%s, %s)", pdf.name, category, doc_type)
        return documents

    def chunk_documents(self, documents: list[Document]) -> list[Document]:
        """Split documents into overlapping chunks and number them per source."""
        chunks = self.splitter.split_documents(documents)
        counters: dict[str, int] = {}
        for chunk in chunks:
            src = chunk.metadata["source"]
            counters[src] = counters.get(src, 0) + 1
            chunk.metadata["chunk_id"] = f"{src}#{counters[src]}"
        return chunks

    def load_and_chunk(self) -> list[Document]:
        return self.chunk_documents(self.load_documents())
