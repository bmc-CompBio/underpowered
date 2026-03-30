"""
Step 3: Discover Reporting Summary PDF URLs from Nature article pages.

For each life-science candidate DOI, fetch the article HTML page and
look for a supplementary-file link labelled "Reporting Summary".

Findings from pre-pilot research:
  - URL pattern: https://www.nature.com/articles/{DOI_SUFFIX}
  - Reporting Summary appears in the supplementary files section
  - Link text: "Reporting Summary" or "Nature Research Reporting Summary"
  - File is a PDF hosted at media.springernature.com or similar

Rate limiting: 1 req/sec (Springer TDM policy without API key)
User-Agent: standard browser string (not AI bot)
"""

import argparse, json, re, time
from pathlib import Path
import requests
from bs4 import BeautifulSoup

DATA = Path("data")
PDFS = Path("data/pdfs")
PDFS.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def doi_to_url(doi: str) -> str:
    suffix = doi.split("10.1038/", 1)[-1]
    return f"https://www.nature.com/articles/{suffix}"

def find_reporting_summary_link(soup, article_url: str):
    """
    Search the parsed HTML for a link to the Reporting Summary PDF.
    Returns (link_text, href) or (None, None).

    Nature renders supplementary file links like:
      <a data-track-label="reporting summary" href="https://static-content.springer.com/...MOESM2_ESM.pdf">
    The data-track-label is the most reliable signal.
    """
    # Strategy 1 (most reliable): data-track-label="reporting summary" with a full CDN URL
    for a in soup.find_all("a", attrs={"data-track-label": re.compile(r"reporting.summary", re.I)}):
        href = a.get("href", "")
        if href.startswith("http") and re.search(r"\.pdf", href, re.I):
            return a.get_text(strip=True), href

    # Strategy 2: <div id="MOESM*"> that contains an <a> with "reporting" in text/href
    for div in soup.find_all("div", id=re.compile(r"^MOESM", re.I)):
        for a in div.find_all("a", href=True):
            text = a.get_text(strip=True)
            href = a["href"]
            if re.search(r"reporting", text, re.I) and re.search(r"\.pdf", href, re.I):
                if not href.startswith("http"):
                    href = "https://www.nature.com" + href
                return text, href

    # Strategy 3: any <a> with a Springer CDN href that contains "report"
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "static-content.springer.com" in href and re.search(r"report", href, re.I):
            return a.get_text(strip=True), href

    # Strategy 4: any <a> with text "reporting summary" pointing to a PDF
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True)
        href = a["href"]
        if re.search(r"reporting\s+summary", text, re.I) and re.search(r"\.pdf", href, re.I):
            if not href.startswith("http"):
                href = "https://www.nature.com" + href
            return text, href

    return None, None

def find_all_supp_links(soup):
    """Return all supplementary/PDF links for debugging."""
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = a.get_text(strip=True)
        if re.search(r"\.pdf|supplementary|supp|additional", href, re.I) or \
           re.search(r"supplementary|supp|reporting|checklist|extended data", text, re.I):
            links.append({"text": text[:80], "href": href[:120]})
    return links

def fetch_article_page(doi: str, verbose=False):
    url = doi_to_url(doi)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        status = resp.status_code
        if status == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            link_text, rs_url = find_reporting_summary_link(soup, url)
            supp_links = find_all_supp_links(soup) if verbose else []
            return {
                "status": status,
                "final_url": resp.url,
                "reporting_summary_text": link_text,
                "reporting_summary_url": rs_url,
                "supp_links": supp_links,
                "html_length": len(resp.text),
            }
        else:
            return {"status": status, "final_url": resp.url, "reporting_summary_url": None}
    except Exception as e:
        return {"status": "error", "error": str(e), "reporting_summary_url": None}

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, default=8107)
    args = parser.parse_args()
    issue = args.issue

    manifest = json.loads((DATA / f"manifest_{issue}.json").read_text())
    articles = manifest["articles"]

    # Select life-science candidates; skip any already resolved from previous run
    candidates = [a for a in articles if a["subject_classification"] == "life_science"]
    already_done = {a["doi"] for a in candidates if a.get("reporting_summary_url") or a.get("page_status")}
    todo = [a for a in candidates if a["doi"] not in already_done]
    print(f"Life-science candidates: {len(candidates)} | already resolved: {len(already_done)} | to fetch: {len(todo)}\n")
    pilot = todo  # process all remaining

    results = []
    for i, art in enumerate(pilot):
        doi = art["doi"]
        title = (art["title"] or "")[:65]
        print(f"[{i+1:2d}/{len(pilot)}] {doi}")
        print(f"       {title}")
        res = fetch_article_page(doi, verbose=(i < 3))  # verbose for first 3
        art["reporting_summary_url"] = res.get("reporting_summary_url")
        art["page_status"] = res.get("status")
        art["page_final_url"] = res.get("final_url")

        rs = res.get("reporting_summary_url")
        status = res.get("status")
        print(f"       HTTP {status} | RS link: {rs or 'NOT FOUND'}")
        if res.get("supp_links"):
            print(f"       Supp links found ({len(res['supp_links'])}):")
            for sl in res["supp_links"][:6]:
                print(f"         [{sl['text'][:40]}] -> {sl['href'][:80]}")
        print()
        results.append({**art, **{k: v for k, v in res.items() if k != "supp_links"}})
        time.sleep(1.1)  # respect 1 req/sec TDM policy

    # Summary
    found = sum(1 for r in results if r.get("reporting_summary_url"))
    print(f"=== Results: {found}/{len(results)} Reporting Summary links found ===")
    for r in results:
        mark = "✓" if r.get("reporting_summary_url") else "✗"
        print(f"  {mark} [{r['page_status']}] {r['doi'][:45]} | {(r['title'] or '')[:50]}")

    # Update manifest
    doi_to_result = {r["doi"]: r for r in results}
    for a in articles:
        if a["doi"] in doi_to_result:
            a.update({k: doi_to_result[a["doi"]].get(k) for k in
                      ["reporting_summary_url", "page_status", "page_final_url"]})

    out = {**manifest, "articles": articles}
    path = DATA / f"manifest_{issue}_with_rs.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\n[OK] Written {path}")

if __name__ == "__main__":
    main()
