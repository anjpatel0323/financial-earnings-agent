"""
Document Parser
---------------
Extracts clean text from SEC HTML filings.
Detects section headers like MD&A, Risk Factors, etc.
"""

import re
from pathlib import Path
from bs4 import BeautifulSoup

SEC_SECTIONS = [
    "business",
    "risk factors",
    "properties",
    "legal proceedings",
    "management.*discussion.*analysis",
    "quantitative.*qualitative.*market risk",
    "financial statements",
    "controls and procedures",
    "executive compensation",
]

SECTION_PATTERN = re.compile(
    r"(?:item\s+\d+[a-z]?[\.\s]+)(" + "|".join(SEC_SECTIONS) + r")",
    re.IGNORECASE,
)

def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^\x20-\x7E\n]", "", text)
    return text.strip()

def parse_html_filing(filepath: Path) -> list[dict]:
    html = filepath.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "table"]):
        tag.decompose()

    full_text = soup.get_text(separator="\n")
    full_text = _clean_text(full_text)

    sections = []
    current_section = "preamble"
    buffer = []

    for line in full_text.split("\n"):
        match = SECTION_PATTERN.search(line)
        if match:
            section_text = " ".join(buffer).strip()
            if section_text:
                sections.append({
                    "section_name": current_section,
                    "text": section_text,
                })
            current_section = match.group(1).strip().lower()
            buffer = [line]
        else:
            buffer.append(line)

    if buffer:
        sections.append({
            "section_name": current_section,
            "text": " ".join(buffer).strip(),
        })

    return sections

def parse_filing_with_metadata(filing_meta: dict) -> list[dict]:
    filepath = Path(filing_meta["filepath"])
    sections = parse_html_filing(filepath)

    enriched = []
    for sec in sections:
        if len(sec["text"]) < 200:
            continue
        enriched.append({
            **sec,
            "ticker":      filing_meta["ticker"],
            "form_type":   filing_meta["form_type"],
            "filing_date": filing_meta["filing_date"],
            "source_url":  filing_meta["source_url"],
            "source_file": str(filepath.name),
        })
    return enriched

if __name__ == "__main__":
    sample = {
        "filepath":    "data/raw/AAPL/AAPL_10-K_2024-11-01.html",
        "ticker":      "AAPL",
        "form_type":   "10-K",
        "filing_date": "2024-11-01",
        "source_url":  "https://sec.gov/...",
    }
    sections = parse_filing_with_metadata(sample)
    for s in sections[:3]:
        print(f"\n[{s['section_name']}] ({len(s['text'])} chars)")
        print(s["text"][:200])