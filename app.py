"""WanderNest Travel Assistant - Streamlit UI.   Run:  streamlit run app.py"""
from __future__ import annotations

import streamlit as st

from config import ConfigError, get_config

st.set_page_config(page_title="WanderNest Travel Assistant", page_icon="✈️", layout="wide",
                   initial_sidebar_state="expanded")

CATEGORY_LABELS = {
    "baggage_policy": "🧳 Baggage", "refund_policy": "💳 Refunds", "visa_immigration": "🛂 Visa",
    "disruption_event": "⛈️ Disruption", "fare_update": "💰 Fares", "safety_advisory": "🩺 Safety",
    "route_info": "🗺️ Routes", "faq": "❓ FAQ", "general": "📄 General",
}
EXAMPLES = [
    "What is the checked baggage allowance from BLR to London in Economy?",
    "Is the BLR-LON route affected by the new baggage rules?",
    "What are my refund rights if my flight is cancelled because of a strike?",
    "Do I need a visa for London and how long does it take?",
    "Why did my Air India fare to London go up?",
    "My flight from Delhi is delayed by fog - what compensation do I get?",
]

st.markdown("""
<style>
.hero {background: linear-gradient(90deg,#0b3d91,#1e88e5); padding: 1.2rem 1.5rem; border-radius: 12px; color: white;}
.hero h1 {margin: 0; font-size: 1.9rem;} .hero p {margin: .2rem 0 0 0; opacity: .9;}
.badge {display:inline-block; padding:2px 10px; border-radius:12px; font-size:.78rem; margin-right:6px;}
.update {background:#fff3cd; color:#7a5b00;} .static {background:#e3f2fd; color:#0b3d91;}
</style>
<div class="hero"><h1>✈️ WanderNest Travel Assistant</h1>
<p>Instant, source-cited answers on baggage, refunds, visas and live travel disruptions.</p></div>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Connecting to Azure services...")
def load_engine():
    from src.search_engine import TravelSearchEngine

    cfg = get_config(validate=True)
    return TravelSearchEngine.from_config(cfg), cfg


try:
    engine, cfg = load_engine()
except ConfigError as exc:
    st.error("Configuration problem - the assistant cannot start.")
    st.code(str(exc))
    st.stop()
except Exception as exc:
    st.error(f"Could not initialise the assistant: {exc}")
    st.stop()

with st.sidebar:
    st.header("Try an example")
    for i, example in enumerate(EXAMPLES):
        if st.button(example, key=f"ex{i}", use_container_width=True):
            st.session_state["query"] = example
    st.divider()
    top_k = st.slider("Passages to retrieve", 1, 10, cfg.top_k)
    show_scores = st.checkbox("Show relevance scores", value=False)
    st.divider()
    st.caption("🔒 Personal data (emails, phones, cards, passports) is redacted before processing. "
               "Answers are generated only from WanderNest documents and live updates.")

st.session_state.setdefault("query", "")
query = st.text_input("Ask a travel question", key="query",
                      placeholder="e.g. Is the BLR-LON route impacted by the new baggage rules?")
ask = st.button("Ask", type="primary")

if ask and query.strip():
    with st.spinner("Searching policies and live updates..."):
        response = engine.ask(query, k=top_k)

    if response.blocked:
        st.warning(response.answer)
        st.caption("Reason: " + ", ".join(response.reasons))
    else:
        st.subheader("Answer")
        st.markdown(response.answer)
        if response.pii_types:
            st.info("For your privacy, personal data was removed from your question: "
                    + ", ".join(response.pii_types))

        st.subheader(f"Sources ({len(response.sources)})")
        if not response.sources:
            st.caption("No supporting documents were found.")
        for i, src in enumerate(response.sources, start=1):
            label = CATEGORY_LABELS.get(src.category, src.category)
            title = f"[{i}] {src.source}" + (f" - page {src.page}" if src.page else "")
            with st.expander(title):
                kind = "update" if src.doc_type == "update" else "static"
                kind_text = "Live update" if kind == "update" else "Policy"
                st.markdown(f'<span class="badge {kind}">{kind_text}</span><span class="badge static">{label}</span>',
                            unsafe_allow_html=True)
                st.write(src.content)
                if show_scores and src.score is not None:
                    st.caption(f"Relevance score: {src.score:.3f}")
elif ask:
    st.warning("Please type a question first.")
