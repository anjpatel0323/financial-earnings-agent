"""
SEC EDGAR Fetcher
-----------------
Downloads 10-K and 10-Q filings from SEC EDGAR.
No API key needed. Completely free.
"""

import time
import requests
from pathlib import Path
from typing import Optional

EDGAR_HEADERS = {
    "User-Agent": "FinancialEarningsAgent dev@example.com",
}

def get_cik(ticker: str) -> Optional[str]:
    mapping_url = "https://www.sec.gov/files/company_tickers.json"
    data = requests.get(mapping_url, headers=EDGAR_HEADERS, timeout=10).json()
    for entry in data.values():
        if entry["ticker"].upper() == ticker.upper():
            return str(entry["cik_str"]).zfill(10)
    return None

def get_recent_filings(cik: str, form_type: str = "10-K", count: int = 3) -> list[dict]:
    url = f"https://data.sec.gov/submissions/CIK{cik}.json"
    resp = requests.get(url, headers=EDGAR_HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    filings = data.get("filings", {}).get("recent", {})
    forms      = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    dates      = filings.get("filingDate", [])
    primary    = filings.get("primaryDocument", [])

    results = []
    for i, form in enumerate(forms):
        if form == form_type and len(results) < count:
            acc = accessions[i].replace("-", "")
            results.append({
                "form_type":    form,
                "filing_date":  dates[i],
                "accession":    accessions[i],
                "primary_doc":  primary[i],
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc}/{primary[i]}",
            })
    return results

def download_filing(filing: dict, ticker: str, save_dir: Path) -> Path:
    save_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{ticker}_{filing['form_type']}_{filing['filing_date']}.html"
    filepath = save_dir / filename

    if filepath.exists():
        print(f"  [cache] {filename}")
        return filepath

    time.sleep(0.15)
    resp = requests.get(filing["url"], headers=EDGAR_HEADERS, timeout=30)
    resp.raise_for_status()
    filepath.write_text(resp.text, encoding="utf-8")
    print(f"  [downloaded] {filename}")
    return filepath

def fetch_filings_for_ticker(ticker: str, save_dir: Path,
                              form_types: list = ["10-K", "10-Q"],
                              count_per_type: int = 3) -> list[dict]:
    print(f"\nFetching filings for {ticker}...")
    cik = get_cik(ticker)
    if not cik:
        raise ValueError(f"Could not find CIK for ticker: {ticker}")
    print(f"  CIK: {cik}")

    results = []
    for form_type in form_types:
        filings = get_recent_filings(cik, form_type=form_type, count=count_per_type)
        for filing in filings:
            filepath = download_filing(filing, ticker, save_dir)
            results.append({
                "filepath":     filepath,
                "ticker":       ticker,
                "form_type":    filing["form_type"],
                "filing_date":  filing["filing_date"],
                "source_url":   filing["url"],
            })

    print(f"  Done — {len(results)} filings fetched.")
    return results

if __name__ == "__main__":
    results = fetch_filings_for_ticker("AAPL", Path("data/raw/AAPL"))
    for r in results:
        print(r)