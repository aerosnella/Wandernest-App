# WanderNest Travels - Dynamic RAG Chatbot (LLMOps)

A governed RAG assistant that answers baggage, refund, visa and disruption questions from WanderNest's static
policy PDFs **and** real-time update bulletins, with source citations.

```
User -> GovernanceGate (PII redaction, content safety) -> TravelSearchEngine
      -> Azure AI Search (vector store, Azure OpenAI embeddings) -> Azure OpenAI chat (grounded answer)
      -> GovernanceGate (output check) -> Streamlit UI (answer + sources)
```

## Project layout

| Path | Purpose |
|---|---|
| `.env.example`, `config.py` | Credentials template; validated config (reports every missing/placeholder value) |
| `src/data_loader.py` | `TravelDataLoader`: loads PDFs from `data/`, categorises by filename, chunks text |
| `src/vector_store.py` | Azure OpenAI embeddings + chat model, LangChain `AzureSearch` vector store |
| `src/search_engine.py` | `TravelSearchEngine`: `search_by_text`, `synthesize_response`, governed `ask` |
| `governance/` | `GovernanceGate`, `PIIDetector`, `ContentSafetyChecker`, `AzureContentSafetyValidator`, `SafetyValidator` |
| `ingest.py` | Load -> chunk -> batch index (retry, idempotent keys) -> verify index count |
| `app.py` | Streamlit UI (examples, sources with Policy / Live-update badges, privacy notice) |
| `evaluation/` | Golden dataset + RAGAS runner (4 metrics, thresholds, PASS/FAIL, CSV + JSON output) |
| `scripts/generate_sample_data.py` | Creates **sample** PDFs in `data/` - replace with your real documents |
| `scripts/build_deck_from_template.py` | Fills the Great Learning slide template -> `WanderNest_RAG_Project_Slides.pptx` |
| `Dockerfile`, `.dockerignore` | Container image for Azure Container Registry / App Service (port 8501) |
| `tests/test_offline.py` | 29 offline tests (no Azure needed) |

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env      # then fill in your Azure keys
```

Required: an Azure OpenAI chat deployment and embedding deployment, and an Azure AI Search service.
Azure AI Content Safety is optional - without it the local rules (prompt-injection / harmful-request patterns)
are used, and the same fallback is used if the Azure call fails.

## Run

```powershell
python scripts/generate_sample_data.py   # optional: sample PDFs (skip if you add your own to data/)
python ingest.py --dry-run               # load + chunk only, no Azure calls
python ingest.py --reset                 # build the index (omit --reset to upsert)
streamlit run app.py                     # chatbot UI
python -m evaluation.run_ragas           # RAGAS evaluation (add --strict for CI)
python -m pytest tests -q                # offline unit tests
```

## Data conventions

* PDFs go directly in `data/`.
* The category is derived from the filename (`baggage`, `refund`, `visa`, `strike|weather|delay`, `fare`,
  `advisory|safety`, `route`, `faq`; see `CATEGORY_RULES`).
* Files named `update_*.pdf` are real-time updates (`doc_type=update`); the prompt tells the model to prefer
  them over older static policy. To publish a new policy or bulletin: drop the PDF in `data/` and run
  `python ingest.py`. Chunk keys are deterministic, so re-running updates rather than duplicates; use `--reset`
  if you removed files.

## Governance

* **Input:** empty/over-long queries blocked; PII (email, phone, card with Luhn check, Aadhaar, PAN, SSN,
  passport) redacted *before* retrieval or LLM calls; prompt-injection and harmful requests blocked; Azure
  Content Safety severity threshold (`CONTENT_SAFETY_MAX_SEVERITY`, default 2).
* **Output:** PII redacted again, content safety re-checked; unsafe answers replaced with a safe message.
* An audit trail of every decision is kept in `GovernanceGate.audit_log` and logged.

## Evaluation (RAGAS)

`evaluation/golden_dataset.py` holds 12 question / reference-answer pairs that match the sample PDFs
(update them if you change the knowledge base). Thresholds in `evaluation/run_ragas.py`:
faithfulness >= 0.80, answer_relevancy >= 0.70, context_precision >= 0.70, context_recall >= 0.70.
Results are written to `evaluation/results/` (`ragas_scores_*.csv`, `ragas_summary_*.json`).

> The sample PDFs contain illustrative, non-official figures. Do not present them as real airline policy.
