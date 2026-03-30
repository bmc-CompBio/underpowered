"""
Step 1: Fetch Nature issue manifest via Crossref + Springer Meta API.

Target: Nature Vol 651, Issue 8106, published 2026-03-19.
Output: data/issue_manifest.json
"""

import json, time, sys
from pathlib import Path
import requests

DATA = Path("data")
DATA.mkdir(exist_ok=True)

NATURE_ISSN = "0028-0836"
ISSUE_DATE_FROM = "2026-03-19"
ISSUE_DATE_UNTIL = "2026-03-25"  # one week window to catch all online-firsts assigned to this issue

# ---------------------------------------------------------------------------
# 1a. Crossref
# ---------------------------------------------------------------------------

def fetch_crossref(issn, date_from, date_until):
    """Return all works from Crossref for the given date range."""
    url = f"https://api.crossref.org/journals/{issn}/works"
    params = {
        "filter": f"from-pub-date:{date_from},until-pub-date:{date_until}",
        "rows": 100,
        "select": "DOI,title,type,published,author,subject,container-title,volume,issue,page",
        "mailto": "research@example.com",   # polite-pool header
    }
    print(f"[Crossref] GET {url}")
    resp = requests.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("message", {}).get("items", [])
    total = data.get("message", {}).get("total-results", 0)
    print(f"[Crossref] total-results={total}, returned={len(items)}")
    return items

# ---------------------------------------------------------------------------
# 1b. Springer Nature Meta API v2 (free, no key needed for basic queries)
# ---------------------------------------------------------------------------

SPRINGER_META_URL = "https://api.springernature.com/meta/v2/json"

def fetch_springer_meta(volume, issue, api_key=None):
    """Return article records from Springer Meta API for a given volume/issue."""
    params = {
        "q": f"issn:{NATURE_ISSN} volume:{volume} issue:{issue}",
        "p": 100,
        "s": 1,
    }
    if api_key:
        params["api_key"] = api_key
    headers = {"User-Agent": "ResearchBot/1.0 TextDataMining (academic non-commercial)"}
    print(f"[Springer] GET {SPRINGER_META_URL} q={params['q']!r}")
    resp = requests.get(SPRINGER_META_URL, params=params, headers=headers, timeout=30)
    print(f"[Springer] HTTP {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        records = data.get("records", [])
        total = data.get("total", 0)
        print(f"[Springer] total={total}, returned={len(records)}")
        return records
    else:
        print(f"[Springer] Response: {resp.text[:300]}")
        return []

# ---------------------------------------------------------------------------
# Normalise and merge
# ---------------------------------------------------------------------------

LIFE_SCIENCE_SUBJECTS = {
    "biological sciences", "biology", "life sciences", "biochemistry",
    "genetics", "cell biology", "molecular biology", "neuroscience",
    "immunology", "microbiology", "structural biology", "cancer",
    "physiology", "ecology", "evolution", "developmental biology",
    "medicine", "pharmacology", "zoology", "botany", "genomics",
    "proteomics", "biophysics",
}

NON_LIFE_SUBJECTS = {
    "physics", "chemistry", "astronomy", "astrophysics", "materials science",
    "condensed matter", "quantum", "cosmology", "earth sciences", "geoscience",
    "climate science", "atmospheric science", "ocean sciences",
    "mathematics", "computer science",
}

def classify_subjects(subjects):
    """Return 'life_science', 'non_life_science', or 'uncertain'."""
    if not subjects:
        return "uncertain"
    low = {s.lower() for s in subjects}
    life_hits = sum(1 for s in low if any(ls in s for ls in LIFE_SCIENCE_SUBJECTS))
    nonlife_hits = sum(1 for s in low if any(ns in s for ns in NON_LIFE_SUBJECTS))
    if life_hits > 0 and nonlife_hits == 0:
        return "life_science"
    if nonlife_hits > 0 and life_hits == 0:
        return "non_life_science"
    if life_hits > 0 and nonlife_hits > 0:
        return "uncertain_mixed"
    return "uncertain"

def normalise_crossref(item):
    subjects = item.get("subject", [])
    title_list = item.get("title", [])
    pub = item.get("published", {}).get("date-parts", [[None]])[0]
    return {
        "doi": item.get("DOI", "").lower(),
        "title": title_list[0] if title_list else None,
        "crossref_type": item.get("type"),
        "volume": str(item.get("volume", "")),
        "issue": str(item.get("issue", "")),
        "published_date": "-".join(str(p) for p in pub if p),
        "subjects": subjects,
        "subject_classification": classify_subjects(subjects),
        "source": "crossref",
    }

def normalise_springer(rec):
    subjects = [c.get("term", "") for c in rec.get("subjects", [])]
    pub_date = rec.get("publicationDate", rec.get("onlineDate", ""))
    art_type = rec.get("contentType", rec.get("articleType", ""))
    return {
        "doi": rec.get("doi", "").lower(),
        "title": rec.get("title"),
        "springer_content_type": art_type,
        "volume": str(rec.get("volume", "")),
        "issue": str(rec.get("issue", "")),
        "published_date": pub_date,
        "subjects": subjects,
        "subject_classification": classify_subjects(subjects),
        "springer_url": rec.get("url", [{}])[0].get("value") if rec.get("url") else None,
        "source": "springer",
    }

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    api_key = None  # set via env var SPRINGER_API_KEY if available
    import os
    api_key = os.environ.get("SPRINGER_API_KEY")
    if api_key:
        print(f"[info] Springer API key found in environment.")
    else:
        print("[info] No SPRINGER_API_KEY env var — Springer query may be rate-limited or require key.")

    # Crossref
    cr_items = fetch_crossref(NATURE_ISSN, ISSUE_DATE_FROM, ISSUE_DATE_UNTIL)
    cr_records = [normalise_crossref(i) for i in cr_items]

    time.sleep(1)

    # Springer Meta API
    sp_records_raw = fetch_springer_meta(volume="651", issue="8106", api_key=api_key)
    sp_records = [normalise_springer(r) for r in sp_records_raw]

    # Build merged manifest keyed by DOI
    manifest = {}
    for r in cr_records:
        doi = r["doi"]
        manifest[doi] = r
    for r in sp_records:
        doi = r["doi"]
        if doi in manifest:
            manifest[doi].update({k: v for k, v in r.items() if k not in manifest[doi] or not manifest[doi][k]})
            manifest[doi]["source"] = "crossref+springer"
        else:
            manifest[doi] = r

    articles = list(manifest.values())

    # Summary
    print(f"\n=== Manifest summary ===")
    print(f"Total unique DOIs: {len(articles)}")
    for key, label in [
        ("crossref_type", "Crossref types"),
        ("springer_content_type", "Springer content types"),
        ("subject_classification", "Subject classification"),
    ]:
        from collections import Counter
        counts = Counter(a.get(key, "n/a") for a in articles)
        print(f"  {label}: {dict(counts)}")

    out = {
        "corpus_version": "nature_v651_i8106",
        "source_issue": {
            "journal": "Nature",
            "issn": NATURE_ISSN,
            "volume": 651,
            "issue": 8106,
            "date": "2026-03-19",
        },
        "query_date_range": {"from": ISSUE_DATE_FROM, "until": ISSUE_DATE_UNTIL},
        "total_articles": len(articles),
        "articles": articles,
    }

    out_path = DATA / "issue_manifest.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n[OK] Written {out_path} ({len(articles)} records)")

if __name__ == "__main__":
    main()
