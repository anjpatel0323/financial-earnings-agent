"""
Agent Tools
-----------
Three tools the agent can use:
1. retrieve_filings  — searches the vector store
2. calculate         — safe math evaluator
3. search_news       — optional live news search
"""

import os
import math
import requests
from langchain.tools import tool
from langchain.schema import Document

_retriever = None

def set_retriever(retriever):
    global _retriever
    _retriever = retriever

def _format_docs(docs: list[Document]) -> str:
    parts = []
    for i, doc in enumerate(docs, 1):
        m = doc.metadata
        citation = f"[Source {i}: {m.get('ticker','?')} {m.get('form_type','?')} {m.get('filing_date','?')} — {m.get('section_name','?')}]"
        parts.append(f"{citation}\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)

@tool
def retrieve_filings(query: str) -> str:
    """
    Search SEC filings for information relevant to the query.
    Returns excerpts with source citations.
    Use this for any question about financial performance,
    risk factors, or management commentary.
    """
    if _retriever is None:
        return "Error: retriever not initialised. Run the ingestion pipeline first."
    docs = _retriever.invoke(query)
    if not docs:
        return "No relevant filings found for this query."
    return _format_docs(docs)

@tool
def calculate(expression: str) -> str:
    """
    Evaluate a math expression and return the result.
    Use for financial calculations like growth rates and margins.
    Example: (94.9 - 89.5) / 89.5 * 100
    """
    allowed = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    allowed.update({"__builtins__": {}, "abs": abs, "round": round})
    try:
        result = eval(expression, allowed)
        return f"Result: {round(result, 4)}"
    except Exception as e:
        return f"Calculation error: {e}"

@tool
def search_news(query: str) -> str:
    """
    Search for recent financial news about a company or topic.
    Use this for context beyond the filings.
    """
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        return "NEWS_API_KEY not set. Skipping news search."
    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={"q": query, "language": "en", "pageSize": 5, "apiKey": api_key},
            timeout=8,
        )
        articles = resp.json().get("articles", [])
        if not articles:
            return "No recent news found."
        return "\n".join([f"- [{a['publishedAt'][:10]}] {a['title']}" for a in articles])
    except Exception as e:
        return f"News search failed: {e}"

ALL_TOOLS = [retrieve_filings, calculate, search_news]