"""
Streamlit UI
------------
Chat interface for the Financial Earnings Intelligence Agent.
Make sure FastAPI server is running first on port 8000.
"""

import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Financial Earnings Agent",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Financial Earnings Intelligence Agent")
st.caption("RAG-powered analysis over SEC filings · LangChain + Amazon Bedrock")

# Sidebar
with st.sidebar:
    st.header("💡 Example Questions")
    examples = [
        "What were Apple's key revenue drivers in their latest 10-K?",
        "What risk factors did Apple highlight?",
        "How did Apple's gross margin change year over year?",
        "What did Apple say about Services growth?",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["prefill"] = ex

    st.divider()
    st.header("ℹ️ Status")
    try:
        resp = requests.get(f"{API_URL}/health", timeout=3)
        if resp.json().get("agent_loaded"):
            st.success("Agent is ready")
        else:
            st.warning("Agent loading...")
    except:
        st.error("API not running. Start with: uvicorn api.main:app --reload")

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander(f"📄 Sources ({len(msg['citations'])})"):
                for c in msg["citations"]:
                    st.markdown(
                        f"`{c['ticker']}` · {c['form_type']} · "
                        f"{c['filing_date']} · *{c['section']}*"
                    )

# Input
prefill  = st.session_state.pop("prefill", "")
question = st.chat_input("Ask a question about SEC filings...")
if prefill and not question:
    question = prefill

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
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
                    with st.expander(f"📄 Sources ({len(citations)})"):
                        for c in citations:
                            st.markdown(
                                f"`{c['ticker']}` · {c['form_type']} · "
                                f"{c['filing_date']} · *{c['section']}*"
                            )

                st.session_state.messages.append({
                    "role":      "assistant",
                    "content":   answer,
                    "citations": citations,
                })

            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Run: uvicorn api.main:app --reload")
            except Exception as e:
                st.error(f"Error: {e}")
                