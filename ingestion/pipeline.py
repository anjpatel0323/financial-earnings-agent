"""
Pipeline
--------
Orchestrates the full ingestion flow:
fetch → parse → chunk → embed → store

Run with:
    python -m ingestion.pipeline --tickers AAPL
"""

import argparse
from pathlib import Path
from dotenv import load_dotenv

from ingestion.edgar_fetcher import fetch_filings_for_ticker
from ingestion.parser import parse_filing_with_metadata
from ingestion.chunker import chunk_sections
from ingestion.vector_store import build_and_save_index

load_dotenv()

RAW_DIR   = Path("data/raw")
INDEX_PATH = "data/index/faiss_index"

def run_pipeline(tickers: list[str]):
    all_documents = []

    for ticker in tickers:
        print(f"\n{'='*50}")
        print(f"Processing {ticker}")
        print("="*50)

        # Step 1 — Fetch
        filings_meta = fetch_filings_for_ticker(
            ticker=ticker,
            save_dir=RAW_DIR / ticker,
            form_types=["10-K", "10-Q"],
            count_per_type=2,
        )

        # Step 2 — Parse
        all_sections = []
        for filing_meta in filings_meta:
            sections = parse_filing_with_metadata(filing_meta)
            all_sections.extend(sections)
            print(f"  Parsed {len(sections)} sections from {filing_meta['form_type']} ({filing_meta['filing_date']})")

        # Step 3 — Chunk
        documents = chunk_sections(all_sections)
        print(f"  Generated {len(documents)} chunks from {ticker}")
        all_documents.extend(documents)

    # Step 4 — Embed + Store
    print(f"\n{'='*50}")
    print(f"Building index for {len(all_documents)} total chunks...")
    build_and_save_index(all_documents, INDEX_PATH)
    print("\nIngestion complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=["AAPL"],
        help="Ticker symbols to ingest",
    )
    args = parser.parse_args()
    run_pipeline(args.tickers)