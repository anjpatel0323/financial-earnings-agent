"""
Streamlit UI — Dark Professional Theme
---------------------------------------
Bloomberg terminal-inspired dark UI for the Financial Earnings Intelligence Agent.
"""

import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="FEIA — Financial Earnings Intelligence Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark professional CSS ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* Base dark background */
[data-testid="stAppViewContainer"] {
    background-color: #0a0e1a;
    color: #e2e8f0;
}
[data-testid="stSidebar"] {
    background-color: #0d1117;
    border-right: 1px solid #1e2d40;
}
[data-testid="stSidebarContent"] {
    padding-top: 1.5rem;
}

/* Header */
.feia-header {
    background: linear-gradient(135deg, #0d1117 0%, #0a1628 100%);
    border-bottom: 1px solid #1e3a5f;
    padding: 1.2rem 2rem;
    margin: -1rem -1rem 1.5rem -1rem;
    display: flex;
    align-items: center;
    gap: 16px;
}
.feia-logo {
    font-size: 28px;
    font-weight: 700;
    color: #00d4aa;
    letter-spacing: -0.5px;
    font-family: monospace;
}
.feia-tagline {
    font-size: 12px;
    color: #4a7fa5;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-top: 2px;
}

/* Metric cards */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 8px;
    padding: 14px 16px;
}
.metric-label {
    font-size: 11px;
    color: #4a7fa5;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 22px;
    font-weight: 600;
    color: #00d4aa;
    font-family: monospace;
}
.metric-sub {
    font-size: 11px;
    color: #2d4a6b;
    margin-top: 2px;
}

/* Chat messages */
[data-testid="stChatMessage"] {
    background: #0d1117 !important;
    border: 1px solid #1e2d40 !important;
    border-radius: 8px !important;
    margin-bottom: 12px !important;
}

/* Citation tags */
.citation-tag {
    display: inline-block;
    background: #0a1628;
    border: 1px solid #1e3a5f;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    font-family: monospace;
    color: #00d4aa;
    margin: 3px 4px 3px 0;
}
.citation-row {
    padding: 8px 0;
    border-bottom: 1px solid #1e2d40;
    font-size: 12px;
    color: #4a7fa5;
}

/* Sidebar elements */
.sidebar-section {
    font-size: 10px;
    font-weight: 600;
    color: #2d4a6b;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin: 1.2rem 0 0.6rem 0;
}
.ticker-badge {
    display: inline-block;
    background: #0a1628;
    border: 1px solid #1e3a5f;
    color: #00d4aa;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-family: monospace;
    margin: 2px;
}
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
}
.dot-green { background: #00d4aa; box-shadow: 0 0 6px #00d4aa; }
.dot-red { background: #e74c3c; }

/* Example question buttons */
[data-testid="stButton"] button {
    background: #0d1117 !important;
    border: 1px solid #1e2d40 !important;
    color: #4a7fa5 !important;
    border-radius: 6px !important;
    font-size: 12px !important;
    text-align: left !important;
    padding: 8px 12px !important;
    transition: all 0.15s !important;
}
[data-testid="stButton"] button:hover {
    border-color: #00d4aa !important;
    color: #00d4aa !important;
    background: #0a1628 !important;
}

/* Chat input */
[data-testid="stChatInputTextArea"] {
    background: #0d1117 !important;
    border: 1px solid #1e3a5f !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
}

/* Spinner */
[data-testid="stSpinner"] { color: #00d4aa !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0a0e1a; }
::-webkit-scrollbar-thumb { background: #1e2d40; border-radius: 2px; }

/* Expander */
[data-testid="stExpander"] {
    background: #0a1628 !important;
    border: 1px solid #1e2d40 !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
# ── Live market ticker ────────────────────────────────────────────────────────
import yfinance as yf

@st.cache_data(ttl=300)  # refresh every 5 minutes
def get_ticker_data(symbols):
    data = []
    for symbol in symbols:
        try:
            tick = yf.Ticker(symbol)
            hist = tick.history(period="2d")
            if len(hist) >= 2:
                price     = hist["Close"].iloc[-1]
                prev      = hist["Close"].iloc[-2]
                change    = price - prev
                change_pct = (change / prev) * 100
                data.append({
                    "symbol":     symbol,
                    "price":      round(price, 2),
                    "change":     round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "up":         change >= 0,
                })
        except:
            pass
    return data

ticker_data = get_ticker_data(["AAPL", "MSFT", "GOOGL", "AMZN"])

ticker_html = '<div style="background:#050810; border-bottom:1px solid #1e2d40; padding:8px 16px; display:flex; gap:32px; font-family:monospace; font-size:13px; overflow-x:auto;">'
for t in ticker_data:
    color  = "#00d4aa" if t["up"] else "#e74c3c"
    arrow  = "▲" if t["up"] else "▼"
    ticker_html += f"""
    <div style="display:flex; align-items:center; gap:8px; white-space:nowrap;">
        <span style="color:#4a7fa5; font-weight:600;">{t['symbol']}</span>
        <span style="color:#e2e8f0;">${t['price']}</span>
        <span style="color:{color};">{arrow} {abs(t['change'])} ({abs(t['change_pct'])}%)</span>
    </div>"""
ticker_html += '<div style="margin-left:auto; font-size:11px; color:#2d4a6b; display:flex; align-items:center;">15-min delayed · yfinance</div>'
ticker_html += '</div>'

st.markdown(ticker_html, unsafe_allow_html=True)
st.markdown("""
<div class="feia-header">
    <div>
        <div class="feia-logo">▸ FEIA</div>
        <div class="feia-tagline">Financial Earnings Intelligence Agent</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Check API status ──────────────────────────────────────────────────────────
api_ready = False
try:
    resp = requests.get(f"{API_URL}/health", timeout=3)
    api_ready = resp.json().get("agent_loaded", False)
except:
    pass

# ── Metric cards ──────────────────────────────────────────────────────────────
tickers_covered = ["AAPL", "MSFT", "GOOGL", "AMZN"]
st.markdown(f"""
<div class="metric-row">
    <div class="metric-card">
        <div class="metric-label">Agent status</div>
        <div class="metric-value">{"LIVE" if api_ready else "OFFLINE"}</div>
        <div class="metric-sub">
            <span class="status-dot {"dot-green" if api_ready else "dot-red"}"></span>
            {"Connected to API" if api_ready else "Start API server"}
        </div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Tickers covered</div>
        <div class="metric-value">{len(tickers_covered)}</div>
        <div class="metric-sub">AAPL · MSFT · GOOGL · AMZN</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Data source</div>
        <div class="metric-value">SEC</div>
        <div class="metric-sub">EDGAR 10-K · 10-Q filings</div>
    </div>
    <div class="metric-card">
        <div class="metric-label">Retrieval</div>
        <div class="metric-value">HYBRID</div>
        <div class="metric-sub">FAISS dense + BM25 sparse</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div style="font-size:16px; font-weight:600; color:#00d4aa; font-family:monospace; margin-bottom:1rem;">▸ FEIA Terminal</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">System status</div>', unsafe_allow_html=True)
    if api_ready:
        st.markdown('<span class="status-dot dot-green"></span><span style="font-size:12px; color:#00d4aa;">Agent online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-dot dot-red"></span><span style="font-size:12px; color:#e74c3c;">API not running</span>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:11px; color:#2d4a6b; margin-top:4px; font-family:monospace;">uvicorn api.main:app --reload</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Coverage</div>', unsafe_allow_html=True)
    st.markdown(" ".join([f'<span class="ticker-badge">{t}</span>' for t in tickers_covered]), unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Sample queries</div>', unsafe_allow_html=True)
    examples = [
        "What were Apple's key revenue drivers in their latest 10-K?",
        "How did Microsoft's cloud segment grow year-over-year?",
        "What risk factors did Alphabet highlight?",
        "Compare Apple and Microsoft gross margins.",
        "What did Apple say about AI investments?",
        "How did Amazon's AWS revenue grow?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True, key=f"ex_{ex[:20]}"):
            st.session_state["prefill"] = ex

    st.markdown('<div class="sidebar-section">Actions</div>', unsafe_allow_html=True)
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Chat history ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; padding: 3rem 1rem; color: #2d4a6b;">
        <div style="font-size:40px; margin-bottom:12px;">📊</div>
        <div style="font-size:16px; font-weight:500; color:#4a7fa5; margin-bottom:8px;">Ready for analysis</div>
        <div style="font-size:13px;">Ask a question about SEC filings or click a sample query from the sidebar.</div>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander(f"📄 {len(msg['citations'])} source(s)"):
                for c in msg["citations"]:
                    st.markdown(f"""
                    <div class="citation-row">
                        <span class="citation-tag">{c['ticker']}</span>
                        <span class="citation-tag">{c['form_type']}</span>
                        <span class="citation-tag">{c['filing_date']}</span>
                        <span style="color:#2d4a6b; font-size:11px;">· {c['section']}</span>
                    </div>
                    """, unsafe_allow_html=True)

# ── Chat input ────────────────────────────────────────────────────────────────
prefill  = st.session_state.pop("prefill", "")
question = st.chat_input("Query the filings database...")
if prefill and not question:
    question = prefill

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Analysing filings..."):
            try:
                resp = requests.post(
                    f"{API_URL}/query",
                    json={"question": question},
                    timeout=120,
                )
                resp.raise_for_status()
                data     = resp.json()
                answer   = data["answer"]
                citations = data["citations"]

                st.markdown(answer)

                if citations:
                    with st.expander(f"📄 {len(citations)} source(s)"):
                        for c in citations:
                            st.markdown(f"""
                            <div class="citation-row">
                                <span class="citation-tag">{c['ticker']}</span>
                                <span class="citation-tag">{c['form_type']}</span>
                                <span class="citation-tag">{c['filing_date']}</span>
                                <span style="color:#2d4a6b; font-size:11px;">· {c['section']}</span>
                            </div>
                            """, unsafe_allow_html=True)

                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   answer,
                    "citations": citations,
                })

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Run: uvicorn api.main:app --reload --port 8000")
            except Exception as e:
                st.error(f"Error: {e}")