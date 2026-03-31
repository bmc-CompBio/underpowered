"""
download_full_papers.py

Download full-text PDFs for all articles in the filtered dataset that do
NOT have a formal power calculation (i.e., the articles we need to analyse
for NHST usage and non-significant-as-evidence).

Requires institutional network access (on-campus or VPN).
Nature/Springer full-paper PDFs are served at:
  https://www.nature.com/articles/{doi-suffix}.pdf

PDFs are saved as: data/pdfs/{doi-suffix}_full.pdf
Already-downloaded files are skipped.

Usage:
  python download_full_papers.py            # download all pending
  python download_full_papers.py --check    # just report which are missing
"""

import argparse
import json
import time
from pathlib import Path

import requests

DATA = Path("data")
PDFS = DATA / "pdfs"
PDFS.mkdir(parents=True, exist_ok=True)

EXCLUDE_CATS = {"power_calc", "methodology_determined"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

RATE_LIMIT_S = 1.2   # seconds between requests


def pdf_url(doi_suffix: str) -> str:
    return f"https://www.nature.com/articles/{doi_suffix}.pdf"


def download_one(doi: str, suffix: str, dry_run: bool = False) -> dict:
    dest = PDFS / f"{suffix}_full.pdf"
    if dest.exists() and dest.stat().st_size > 50_000:
        return {"status": "cached", "path": str(dest)}

    url = pdf_url(suffix)
    if dry_run:
        return {"status": "pending", "url": url}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, stream=True)
        http_status = resp.status_code

        if http_status == 200:
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type and b"%PDF" not in resp.content[:10]:
                # Got HTML (paywall or redirect) instead of PDF
                return {"status": "paywall", "http": http_status, "url": url}
            data = resp.content
            if len(data) < 10_000:
                return {"status": "too_small", "http": http_status, "size": len(data)}
            dest.write_bytes(data)
            return {"status": "ok", "http": http_status, "size": len(data), "path": str(dest)}
        elif http_status in (401, 403):
            return {"status": "access_denied", "http": http_status, "url": url}
        else:
            return {"status": "error", "http": http_status, "url": url}
    except Exception as e:
        return {"status": "exception", "error": str(e), "url": url}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true",
                        help="Report missing PDFs without downloading")
    parser.add_argument("--all", action="store_true",
                        help="Download all articles (not just non-power-calc)")
    args = parser.parse_args()

    dataset = json.loads((DATA / "multi_issue_dataset_filtered.json").read_text())

    if args.all:
        records = dataset["records"]
    else:
        records = [r for r in dataset["records"]
                   if r["sample_size_category"] not in EXCLUDE_CATS]

    print(f"Target: {len(records)} articles")

    pending = []
    cached = []
    for r in records:
        suffix = r["doi"].split("/")[-1]
        dest = PDFS / f"{suffix}_full.pdf"
        if dest.exists() and dest.stat().st_size > 50_000:
            cached.append(r["doi"])
        else:
            pending.append(r)

    print(f"Already downloaded: {len(cached)}")
    print(f"Pending:            {len(pending)}")

    if args.check or not pending:
        if pending:
            print("\nMissing full-text PDFs:")
            for r in pending:
                print(f"  {r['doi'].split('/')[-1]}  [{r['sample_size_category']}]")
        else:
            print("\nAll full-text PDFs present.")
        return

    print("\nNOTE: institutional access required (ensure VPN/campus network is active)")
    print(f"Downloading {len(pending)} PDFs at {RATE_LIMIT_S}s/req …\n")

    ok = access_denied = paywall = error = 0

    for i, rec in enumerate(pending, 1):
        doi = rec["doi"]
        suffix = doi.split("/")[-1]
        result = download_one(doi, suffix)
        status = result["status"]

        if status == "ok":
            ok += 1
            size_kb = result["size"] // 1024
            print(f"  [{i:2d}/{len(pending)}] ✓ {suffix[:40]}  ({size_kb} KB)")
        elif status == "cached":
            ok += 1
            print(f"  [{i:2d}/{len(pending)}] = {suffix[:40]}  (cached)")
        elif status in ("access_denied", "paywall"):
            access_denied += 1
            print(f"  [{i:2d}/{len(pending)}] ✗ {suffix[:40]}  ACCESS DENIED "
                  f"(HTTP {result.get('http')}) — check institutional access")
        else:
            error += 1
            print(f"  [{i:2d}/{len(pending)}] ! {suffix[:40]}  {status} "
                  f"HTTP={result.get('http', '?')}")

        if i < len(pending):
            time.sleep(RATE_LIMIT_S)

    print(f"\nDone: {ok} ok / {access_denied} access-denied / {error} errors")
    if access_denied:
        print("  → Access-denied responses usually mean the institutional IP is not")
        print("    recognised. Connect to your institution's VPN and re-run.")


if __name__ == "__main__":
    main()
