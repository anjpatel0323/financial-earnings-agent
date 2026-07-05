"""
Chunker
-------
Splits sections into overlapping 512-token chunks.
Every chunk keeps its source metadata attached.
"""

import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

CHUNK_SIZE = 512
CHUNK_OVERLAP = 50

def _make_chunk_id(ticker: str, filing_date: str, section: str, index: int) -> str:
    key = f"{ticker}_{filing_date}_{section}_{index}"
    return hashlib.md5(key.encode()).hexdigest()[:12]

def chunk_sections(sections: list[dict]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
    )

    documents = []
    for section in sections:
        chunks = splitter.split_text(section["text"])
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) < 80:
                continue
            doc = Document(
                page_content=chunk_text,
                metadata={
                    "chunk_id":    _make_chunk_id(section["ticker"], section["filing_date"], section["section_name"], i),
                    "chunk_index": i,
                    "section_name": section["section_name"],
                    "ticker":      section["ticker"],
                    "form_type":   section["form_type"],
                    "filing_date": section["filing_date"],
                    "source_url":  section["source_url"],
                    "source_file": section["source_file"],
                },
            )
            documents.append(doc)
    return documents

if __name__ == "__main__":
    sample = [{
        "section_name": "management discussion and analysis",
        "text": "Revenue increased 6% to $94.9 billion driven by iPhone and Services. " * 30,
        "ticker":      "AAPL",
        "form_type":   "10-K",
        "filing_date": "2024-11-01",
        "source_url":  "https://sec.gov/...",
        "source_file": "AAPL_10-K_2024-11-01.html",
    }]
    docs = chunk_sections(sample)
    print(f"Generated {len(docs)} chunks")
    print(docs[0].metadata)
    print(docs[0].page_content[:200])