"""Fills the Great Learning 'Learner Slides [Code Track]' template with the WanderNest RAG project content.

Usage: python scripts/build_deck_from_template.py [template.pptx]   ->  WanderNest_RAG_Project_Slides.pptx
Screenshot boxes (amber, dashed) mark where portal / app screenshots must be pasted.
"""
import sys
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.data_loader import TravelDataLoader  # noqa: E402

TEMPLATE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "template.pptx"
OUT = ROOT / "WanderNest_RAG_Project_Slides.pptx"

BLUE, DARK, GREY = RGBColor(0x0E, 0x39, 0xA9), RGBColor(0x26, 0x2B, 0x33), RGBColor(0x6B, 0x75, 0x85)
LIGHT, WHITE, AMBER = RGBColor(0xEA, 0xF1, 0xFC), RGBColor(255, 255, 255), RGBColor(0xE6, 0x8A, 0x00)
BODY_FONT, MONO = "Montserrat Medium", "Consolas"

prs = Presentation(TEMPLATE)
slides = list(prs.slides)          # original numbering (1-based in comments below)


# ------------------------------------------------------------------ helpers
def remove_shape(shape):
    el = shape._element
    el.getparent().remove(el)


def clear_template_boxes(slide):
    """Remove the template's instruction boxes ('(Put ...)', '(In this section ...)', 'Write ... here')."""
    for sh in list(slide.shapes):
        if sh.has_text_frame and sh.text_frame.text.strip().startswith(("(", "Write ")):
            remove_shape(sh)


def set_text(shape, new_text):
    """Replace text keeping the first run's formatting."""
    tf = shape.text_frame
    first = tf.paragraphs[0]
    runs = first.runs
    runs[0].text = new_text
    for r in runs[1:]:
        r._r.getparent().remove(r._r)
    for p in tf.paragraphs[1:]:
        p._p.getparent().remove(p._p)


def find_shape(slide, startswith):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip().startswith(startswith):
            return sh
    raise KeyError(startswith)


def _bulletize(p, level_indent=171450):
    pPr = p._p.get_or_add_pPr()
    pPr.set("marL", str(level_indent))
    pPr.set("indent", str(-level_indent))
    for child in pPr.findall(qn("a:buNone")):
        pPr.remove(child)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", "•")


def add_text(slide, x, y, w, h, paras, size=12, color=DARK, font=BODY_FONT, anchor=MSO_ANCHOR.TOP,
             align=PP_ALIGN.LEFT):
    """paras: list of str or dict(text, bullet, bold, size, color, mono, space)."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.03)
    for i, item in enumerate(paras if isinstance(paras, list) else [paras]):
        o = {"text": item} if isinstance(item, str) else dict(item)
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(o.get("space", 5))
        r = p.add_run()
        r.text = o["text"]
        r.font.size = Pt(o.get("size", size))
        r.font.bold = o.get("bold", False)
        r.font.color.rgb = o.get("color", color)
        r.font.name = MONO if o.get("mono") else font
        if o.get("bullet"):
            _bulletize(p)
    return tb


def B(text, **kw):
    return {"text": text, "bullet": True, **kw}


def H(text, size=13):
    return {"text": text, "bold": True, "color": BLUE, "size": size, "space": 4}


def screenshot_box(slide, x, y, w, h, label):
    s = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = RGBColor(0xFF, 0xF6, 0xE0)
    s.line.color.rgb = AMBER
    s.line.width = Pt(1.5)
    s.line.dash_style = 4  # dash
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "INSERT SCREENSHOT\n" + label
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = AMBER
    r.font.name = BODY_FONT
    return s


def table(slide, x, y, w, col_widths, rows, size=10, row_h=0.28):
    t = slide.shapes.add_table(len(rows), len(col_widths), Inches(x), Inches(y), Inches(w),
                               Inches(row_h * len(rows))).table
    for i, cw in enumerate(col_widths):
        t.columns[i].width = Inches(cw)
    for r, row in enumerate(rows):
        t.rows[r].height = Inches(row_h)
        for c, val in enumerate(row):
            cell = t.cell(r, c)
            cell.text = val
            cell.margin_left = cell.margin_right = Inches(0.06)
            cell.margin_top = cell.margin_bottom = Inches(0.02)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            run = cell.text_frame.paragraphs[0].runs[0]
            run.font.size = Pt(size)
            run.font.name = MONO if (c == 0 and r > 0 and rows[0][0] in ("Variable", "File")) else BODY_FONT
            run.font.bold = r == 0
            run.font.color.rgb = WHITE if r == 0 else DARK
            cell.fill.solid()
            cell.fill.fore_color.rgb = BLUE if r == 0 else (LIGHT if r % 2 else WHITE)
    return t


def box(slide, x, y, w, h, label, fill=BLUE, size=10, color=WHITE):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    tf = s.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = Inches(0.04)
    for i, line in enumerate(label.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = line
        r.font.size = Pt(size if i == 0 else size - 1.5)
        r.font.bold = i == 0
        r.font.color.rgb = color
        r.font.name = BODY_FONT
    return s


def arrow(slide, x, y, w=0.28):
    s = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(0.22))
    s.fill.solid()
    s.fill.fore_color.rgb = AMBER
    s.line.fill.background()
    s.shadow.inherit = False


def prep(idx):
    s = slides[idx - 1]
    clear_template_boxes(s)
    return s


# ------------------------------------------------------------------ real data from the project
loader = TravelDataLoader(ROOT / "data", 1000, 150)
doc_rows = [("File", "Category (from filename)", "Type")]
for pdf in loader.list_pdfs():
    doc_rows.append((pdf.name, loader.categorize(pdf.name), "Live update" if loader.is_update(pdf.name) else "Static policy"))
chunks = loader.load_and_chunk()
pages = len(loader.load_documents())
from collections import Counter  # noqa: E402
by_cat = dict(Counter(c.metadata["category"] for c in chunks))

# ------------------------------------------------------------------ Step 1: business context
s = slides[0]  # title slide: keep template text, add the client line
add_text(s, 1.5, 3.55, 7.0, 0.4, "WanderNest Travels  |  Dynamic RAG Chatbot", size=13, color=GREY, align=PP_ALIGN.CENTER)

s = prep(5)  # 1.1 Problem statement
add_text(s, 0.4, 0.95, 9.2, 4.3, [
    B("WanderNest Travels serves 500K+ users a year and processes 62,000+ bookings from BLR, DEL and BOM to LON, JFK, DXB and BKK."),
    B("Travel conditions change by the hour: weather delays, strikes, airline mergers, fare increases, visa and baggage-rule changes. Static FAQs and generic chatbots cannot answer these in real time."),
    B("Human agents spend 10-15 minutes per query across live APIs, news feeds, internal policies and itineraries."),
    B("Result: unresolved queries, booking abandonment, lost revenue, low satisfaction and reputational damage against competitors such as Booking.com."),
    {"text": "How do we give every traveller an instant, accurate, source-cited answer that reflects the latest policies and events?",
     "bold": True, "color": BLUE, "space": 4},
], size=12)

s = prep(6)  # 1.2 Business context
add_text(s, 0.4, 0.95, 4.5, 4.3, [
    H("Objective"),
    B("Apply LLMOps best practices to build a RAG chatbot grounded in a static knowledge base (policies, routes, FAQs) plus real-time update documents."),
    B("Answer questions such as \"Is the BLR-LON route impacted by the new baggage rules?\" by retrieving the relevant policy and citing it."),
    B("Lower cost per ticket by moving first-line support to the bot, and keep travellers inside the WanderNest ecosystem."),
], size=11)
add_text(s, 5.1, 0.95, 4.5, 4.3, [
    H("Expected business impact"),
    B("Higher deflection rate of routine queries"),
    B("Real-time accuracy: answers grounded in current documents"),
    B("Reduced regulatory risk: policy and DOT refund rules cited"),
    B("Operational agility: new policy = update the knowledge base"),
    B("Lower re-accommodation cost via alternatives and vouchers"),
    B("Source-verified safety and health advice"),
    B("Fewer disputes through clear fee explanations"),
], size=11)

s = prep(7)  # 1.3 Data description
add_text(s, 0.4, 0.9, 9.2, 0.6, "The knowledge base is a set of PDFs: static policies (baggage, refunds, visas, routes, FAQs, safety) and "
         "real-time updates (fare increase, weather, strike, visa notice). The category is derived from the filename.", size=11)
table(s, 0.4, 1.6, 9.2, [4.2, 2.8, 2.2], doc_rows, size=9, row_h=0.285)

s = prep(8)  # 1.4 Data source
add_text(s, 0.4, 0.95, 9.2, 4.3, [
    B("Location: PDFs are read directly from the project's data/ folder, with no intermediate conversion."),
    B("Static documents: airline and WanderNest policies, route guide, FAQs and advisories."),
    B("Updates: files named update_*.pdf are flagged doc_type=update. The prompt prefers them when they conflict with older policy."),
    B("Metadata stored with every chunk: source, category, doc_type, page, chunk_id."),
    B(f"Current corpus: {len(doc_rows) - 1} PDFs, {pages} pages, {len(chunks)} chunks (1000 characters, 150 overlap)."),
    B("The demo PDFs are illustrative samples created by scripts/generate_sample_data.py. Replace them with official documents for production."),
], size=12)

s = prep(9)  # 1.5 Solution methodology
cards = [("1. Ingest", "Load PDFs, categorise by filename, chunk, embed and batch-index into Azure AI Search; verify the count."),
         ("2. Govern input", "Redact PII, block prompt injection and harmful content (Azure Content Safety + local rules)."),
         ("3. Retrieve", "Similarity search for the top-k chunks (static policies and live updates)."),
         ("4. Generate", "Azure OpenAI answers only from the numbered context and cites sources [1], [2]."),
         ("5. Govern output", "Re-check the answer for PII and unsafe content before display."),
         ("6. Evaluate", "RAGAS on a golden dataset: faithfulness, answer relevancy, context precision, context recall.")]
for i, (h, d) in enumerate(cards):
    x, y = 0.4 + (i % 3) * 3.1, 1.05 + (i // 3) * 2.05
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(2.95), Inches(1.9))
    bg.fill.solid(); bg.fill.fore_color.rgb = LIGHT; bg.line.fill.background(); bg.shadow.inherit = False
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(0.07), Inches(1.9))
    bar.fill.solid(); bar.fill.fore_color.rgb = BLUE; bar.line.fill.background(); bar.shadow.inherit = False
    add_text(s, x + 0.15, y + 0.1, 2.7, 1.75, [H(h, 13), {"text": d, "size": 11.5}], size=11.5)

# ------------------------------------------------------------------ Step 2: Azure resources
s = prep(11)  # Azure services
table(s, 0.4, 1.0, 9.2, [2.6, 6.6], [
    ("Azure service", "Purpose in this project"),
    ("Azure AI Foundry / Azure OpenAI", "Hosts the chat model (answer generation, RAGAS judge) and the embedding model (chunks and queries)"),
    ("Azure AI Search", "Vector index of document chunks; similarity search used for retrieval"),
    ("Azure AI Content Safety", "Screens questions and answers for Hate, Self-harm, Sexual and Violence content"),
    ("Azure Container Registry", "Stores the Docker image of the Streamlit application"),
    ("Azure App Service", "Runs the container so travellers and agents can use the chatbot online"),
], size=10, row_h=0.62)
add_text(s, 0.4, 4.85, 9.2, 0.4, "All resources use the default resource group, region East US where required.", size=10, color=GREY)

s = prep(13)  # 2.1 Foundry resource creation
add_text(s, 0.4, 0.95, 3.7, 4.2, [
    H("Settings used"),
    B("Resource group: default_resource_group"),
    B("Region: East US"),
    B("Pricing tier: Standard S0"),
    B("Wait 10-15 minutes until the resource is fully operational"),
    B("Skip creation if a Foundry resource already exists; go straight to model deployment"),
], size=11)
screenshot_box(s, 4.3, 1.3, 5.3, 3.65, "Azure AI Foundry resource creation\n(portal review page, account visible)")

s = prep(14)  # 2.2 Foundry interface
screenshot_box(s, 0.6, 1.3, 8.8, 3.65, "Azure AI Foundry user interface\n(account details visible, key areas boxed in red)")

s = prep(16)  # Model selection
table(s, 0.4, 1.0, 9.2, [1.9, 2.4, 4.9], [
    ("Role", "Model (example)", "Why it was selected"),
    ("Chat / answer generation", "gpt-4o-mini", "Low cost and latency for high-volume support; strong instruction following keeps answers grounded and cited"),
    ("Embeddings", "text-embedding-3-small", "Accurate semantic search at low cost; same model for chunks and queries"),
    ("Evaluation judge", "Same chat deployment", "RAGAS uses it to score faithfulness and relevancy at temperature 0"),
], size=10, row_h=0.75)
add_text(s, 0.4, 4.2, 9.2, 0.7, "Deployment names are read from AZURE_OPENAI_CHAT_DEPLOYMENT and AZURE_OPENAI_EMBEDDING_DEPLOYMENT, "
         "so the models can be swapped without code changes. Update this table if your deployments differ.", size=10, color=GREY)

s = prep(17)  # Model deployment
screenshot_box(s, 0.6, 1.0, 8.8, 3.5, "Models + deployments page in Azure AI Foundry\n(chat and embedding deployments listed)")
add_text(s, 0.6, 4.6, 8.8, 0.6, "Copy the deployment names, endpoint and key into .env (AZURE_OPENAI_*).", size=11)

s = prep(19)  # Search creation
add_text(s, 0.4, 0.95, 3.7, 4.2, [
    H("Settings used"),
    B("Same resource group and region as Foundry"),
    B("Tier: a paid tier with vector search (Basic or Standard)"),
    B("The index is created automatically by LangChain AzureSearch on first ingestion"),
    B("Endpoint and admin key go into .env (AZURE_SEARCH_*)"),
], size=11)
screenshot_box(s, 4.3, 1.3, 5.3, 3.65, "Azure AI Search resource creation\n(review page, account visible)")

s = prep(21)  # ACR creation
add_text(s, 0.4, 0.95, 4.3, 4.2, [
    H("Settings used"),
    B("Same resource group; SKU Basic"),
    B("Build and push the image from the project root:"),
    {"text": "az acr build -r <name> -t wandernest-rag .", "mono": True, "size": 9},
    B("The Dockerfile installs requirements.txt and runs Streamlit on port 8501"),
    B(".env is excluded from the image (.dockerignore)"),
], size=11)
screenshot_box(s, 4.9, 1.3, 4.7, 3.65, "Azure Container Registry creation\nand pushed repository")

s = prep(23)  # App service creation
add_text(s, 0.4, 0.95, 4.3, 4.2, [
    H("Settings used"),
    B("Web App for Containers (Linux), same resource group"),
    B("Image source: the Azure Container Registry image above"),
    B("Container port: 8501 (WEBSITES_PORT=8501)"),
    B("Add every .env variable as an Application setting so secrets stay out of the image"),
], size=11)
screenshot_box(s, 4.9, 1.3, 4.7, 3.65, "Azure App Service creation\nand running app URL")

# ------------------------------------------------------------------ Step 3: architecture
s = prep(25)  # Folder structure
tree = [
    "wandernest_rag/",
    "|- .env.example      credential template (copy to .env)",
    "|- config.py         validated settings",
    "|- ingest.py         load > chunk > index > verify",
    "|- app.py            Streamlit UI",
    "|- Dockerfile        container image",
    "|- data/             source PDFs (static + update_*)",
    "|- src/",
    "|   |- data_loader.py    TravelDataLoader",
    "|   |- vector_store.py   embeddings, LLM, AzureSearch",
    "|   `- search_engine.py  TravelSearchEngine",
    "|- governance/",
    "|   |- pii_detector.py       PII detection/redaction",
    "|   |- safety_validator.py   Azure + local safety",
    "|   `- governance_gate.py    GovernanceGate",
    "|- evaluation/       golden dataset + RAGAS runner",
    "|- scripts/          sample data + deck builders",
    "`- tests/            29 offline tests",
]
add_text(s, 0.4, 0.95, 9.2, 4.4, [{"text": line, "mono": True, "size": 9.5, "space": 1} for line in tree])

s = prep(26)  # Component interaction
add_text(s, 0.4, 0.88, 9.2, 0.3, "Online question answering", size=11, color=BLUE)
online = [("app.py\nStreamlit UI", BLUE), ("GovernanceGate\nPII + safety", RGBColor(0xC6, 0x28, 0x28)),
          ("Search engine\nTravelSearchEngine", BLUE), ("Azure AI Search\nvector retrieval", RGBColor(0x1F, 0x6F, 0xD6)),
          ("Azure OpenAI\ngrounded answer", RGBColor(0x1F, 0x6F, 0xD6))]
x = 0.4
for i, (lab, col) in enumerate(online):
    box(s, x, 1.2, 1.62, 0.8, lab, col, size=10)
    if i < len(online) - 1:
        arrow(s, x + 1.64, 1.49, 0.26)
    x += 1.9
add_text(s, 0.4, 2.1, 9.2, 0.3, "The answer returns through GovernanceGate (output check) to the UI with its sources.", size=9, color=GREY)
add_text(s, 0.4, 2.5, 9.2, 0.3, "Offline ingestion", size=11, color=BLUE)
offline = [("ingest.py\nCLI", BLUE), ("TravelDataLoader\nload + chunk", BLUE),
           ("vector_store.py\nembeddings", RGBColor(0x1F, 0x6F, 0xD6)), ("Azure AI Search\nindex + verify", RGBColor(0x1F, 0x6F, 0xD6))]
x = 0.4
for i, (lab, col) in enumerate(offline):
    box(s, x, 2.82, 1.9, 0.8, lab, col, size=10)
    if i < len(offline) - 1:
        arrow(s, x + 1.95, 3.11, 0.3)
    x += 2.4
box(s, 0.4, 3.95, 4.4, 0.8, "config.py + .env\nshared, validated settings for every component", RGBColor(0x4A, 0x55, 0x68), size=10)
box(s, 5.2, 3.95, 4.4, 0.8, "evaluation/run_ragas.py\ncalls the engine, scores with RAGAS", RGBColor(0x2E, 0x7D, 0x32), size=10)

s = prep(27)  # .env
table(s, 0.4, 0.95, 9.2, [3.6, 5.6], [
    ("Variable", "Description"),
    ("AZURE_OPENAI_API_KEY", "Key of the Azure OpenAI / Foundry resource"),
    ("AZURE_OPENAI_ENDPOINT", "Resource endpoint (https://<name>.openai.azure.com/)"),
    ("AZURE_OPENAI_API_VERSION", "API version used by the SDK"),
    ("AZURE_OPENAI_CHAT_DEPLOYMENT", "Deployment name of the chat model"),
    ("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "Deployment name of the embedding model"),
    ("AZURE_SEARCH_ENDPOINT / AZURE_SEARCH_KEY", "Azure AI Search endpoint and admin key"),
    ("AZURE_SEARCH_INDEX_NAME", "Name of the vector index (created on first ingestion)"),
    ("AZURE_CONTENT_SAFETY_ENDPOINT / _KEY", "Optional: Azure AI Content Safety; local rules used if unset"),
    ("CHUNK_SIZE / CHUNK_OVERLAP / TOP_K", "Chunking (1000/150) and number of passages retrieved (4)"),
], size=9, row_h=0.36)
add_text(s, 0.4, 4.7, 9.2, 0.5, "Copy .env.example to .env and fill in your values. config.py lists every missing or placeholder value on start-up. .env is never committed.",
         size=10, color=GREY)

# ------------------------------------------------------------------ Step 4: running
s = prep(29)  # 4.1 Ingestion
add_text(s, 0.4, 0.95, 4.6, 4.3, [
    H("How to run"),
    {"text": "python ingest.py --dry-run", "mono": True, "size": 9.5},
    {"text": "load + chunk only (no Azure calls)", "size": 9, "color": GREY},
    {"text": "python ingest.py --reset", "mono": True, "size": 9.5},
    {"text": "rebuild the index, batch-index chunks, verify count", "size": 9, "color": GREY},
    H("Output of the dry run (this corpus)", 11),
    {"text": f"Loaded {pages} pages -> {len(chunks)} chunks", "mono": True, "size": 9, "space": 2},
    {"text": "by category:", "mono": True, "size": 9, "space": 2},
    *[{"text": f"  {k}: {v}", "mono": True, "size": 9, "space": 1} for k, v in by_cat.items()],
], size=10)
screenshot_box(s, 5.2, 1.0, 4.4, 3.9, "Terminal output of python ingest.py --reset\n(\"Index verification OK\" line)")

s = prep(30)  # 4.2 Streamlit
add_text(s, 0.4, 0.95, 4.3, 4.3, [
    H("How to run"),
    {"text": "streamlit run app.py", "mono": True, "size": 10},
    {"text": "Opens at http://localhost:8501", "size": 10, "color": GREY},
    H("What the UI shows", 11),
    B("Example questions in the sidebar"),
    B("Answer with citations [1], [2]"),
    B("Source cards with Policy / Live update badges"),
    B("Privacy notice when PII was removed"),
    B("Clear message when a request is blocked"),
], size=10)
screenshot_box(s, 4.9, 1.0, 4.7, 3.9, "Streamlit app answering a question\n(answer + sources visible)")

s = prep(31)  # RAGAS
set_text(find_shape(s, "4.2 Running RAGAS"), "4.3 Running RAGAS Evaluation")
table(s, 0.4, 0.95, 9.2, [2.2, 5.6, 1.4], [
    ("Metric", "What it measures", "Pass if"),
    ("Faithfulness", "Answer is supported by the retrieved context (no hallucination)", ">= 0.80"),
    ("Answer relevancy", "Answer addresses the question asked", ">= 0.70"),
    ("Context precision", "Relevant chunks are ranked first", ">= 0.70"),
    ("Context recall", "Retrieved context covers the reference answer", ">= 0.70"),
], size=9.5, row_h=0.36)
add_text(s, 0.4, 2.85, 4.4, 2.4, [
    H("How to run", 11),
    {"text": "python -m evaluation.run_ragas", "mono": True, "size": 9.5},
    B("12 golden questions run through the real pipeline"),
    B("Per-question scores (CSV) and PASS/FAIL summary (JSON) saved to evaluation/results/"),
    B("--strict returns a failing exit code for CI"),
], size=10)
screenshot_box(s, 5.0, 2.85, 4.6, 2.3, "RAGAS results printed in the terminal\n(scores + PASS/FAIL per metric)")

# ------------------------------------------------------------------ Conclusion
s = prep(33)  # Key takeaways
add_text(s, 0.4, 0.95, 9.2, 4.3, [
    B("Grounding in documents plus live updates produces current, source-cited answers instead of guesses from model memory."),
    B("Governance is part of the pipeline: PII is redacted before retrieval or generation, and both questions and answers are safety-checked."),
    B("Deterministic chunk keys make re-ingestion safe, so publishing a new policy is a PDF upload and one command."),
    B("The bot says it does not know when the context lacks the answer, and routes the traveller to a human agent."),
    B("RAGAS with explicit thresholds turns answer quality into a measurable release gate."),
    B("29 offline tests protect configuration, loading, PII, governance, retrieval and ingestion logic."),
], size=12)

s = prep(34)  # Business impact
table(s, 0.4, 0.95, 9.2, [2.8, 6.4], [
    ("Business impact", "How the solution delivers it"),
    ("Higher deflection rate", "Instant first-line answers on baggage, refunds, visas and disruptions"),
    ("Real-time data accuracy", "update_*.pdf bulletins are retrieved and preferred over older policy"),
    ("Reduced regulatory risk", "Answers cite policy and DOT refund rules from the documents"),
    ("Operational agility", "New baggage or visa policy goes live by re-ingesting the knowledge base"),
    ("Lower re-accommodation cost", "Suggests rebooking and the 110% voucher option from the FAQ"),
    ("Enhanced safety adherence", "Source-verified health and security advisories"),
    ("Lower dispute volume", "Clear, documented explanations for surcharges and fees"),
], size=9.5, row_h=0.46)

# ------------------------------------------------------------------ remove the learner-instruction slides (2, 3)
sld_id_lst = prs.slides._sldIdLst
for idx in (2, 1):  # delete 0-based 2 then 1
    sld_id = sld_id_lst[idx]
    prs.part.drop_rel(sld_id.rId)
    sld_id_lst.remove(sld_id)

prs.save(OUT)
print("saved", OUT, len(prs.slides), "slides")
