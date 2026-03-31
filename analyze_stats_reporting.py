"""
analyze_stats_reporting.py

For every article without a formal power calculation, assess:
  1. nhst_used      — whether null-hypothesis statistical testing was used
                      to confirm hypotheses
  2. ns_as_evidence — whether a non-significant result was used as a positive
                      argument (claiming equivalence / absence of effect without
                      adequate power)

Detection sources:
  Full paper PDF (data/pdfs/{doi-suffix}_full.pdf)
    Nature PDFs use a two-column layout; pdfplumber's text extraction does not
    reliably separate sections. We therefore search the ENTIRE paper text
    (excluding the Methods section if locatable) for NHST and NS patterns.
    P-values appearing in figure legends are valid evidence of NHST.
  Abstract (cached, always available — used when no full text)
  RS PDF Data analysis field (fallback proxy via stats software names)

Run download_full_papers.py first to obtain full-text PDFs.

Input:  data/multi_issue_dataset_filtered.json
Output: data/stats_reporting_analysis.json
        data/stats_reporting_analysis.tsv
"""

import json
import re
from collections import Counter
from pathlib import Path

import pdfplumber

DATA = Path("data")
PDFS = DATA / "pdfs"

EXCLUDE_CATS = {"power_calc", "methodology_determined"}

# ── Methods section boundary (to exclude from NS search) ─────────────────────
# Nature papers end with a Methods section; we want to find NS-as-evidence
# in body/Results text, not method descriptions.
METHODS_START = re.compile(
    r"\n(?:Methods|METHODS|Online Methods)\s*\n",
)

# ── NHST detection ────────────────────────────────────────────────────────────
# Searched across entire full-text PDF (incl. figure legends).
NHST_RE = re.compile(
    r"""
    \bP\s*[<=>≤≥]\s*0\.\d             # P < 0.05 / P = 0.001  (capital P common)
    | \bp\s*[<=>≤≥]\s*0\.\d           # p < 0.05 / p = 0.001  (lowercase)
    | \bP\s*=\s*\d                     # P = 3 × 10^-4 etc.
    | \bp[\s\-]?value\b                # p-value / p value
    | \bstatistically\s+significant
    | \bsignificant(?:ly)?\s+
        (?:difference|increase|decrease|reduction|elevation|
           inhibit|activat|higher|lower|greater|less|
           change|effect|correlat|associat|improv|express|enrich)
    | \b(?:t|F|z)\s*[\(\[]\d          # t(48) = / F(2,30) =
    | \bchi.squar
    | \b(?:one|two).way\s+anova\b
    | \b(?:student'?s?\s+)?t.test\b
    | \bmann.whitney\b | \bwilcoxon\b | \bkruskal.wallis\b
    | \blogistic\s+regression\b | \bcox\s+proportional\b
    | \bfalse\s+discovery\s+rate\b | \bfdr\b
    | \bbenjamini.hochberg\b | \bbonferroni\b | \btukey\b
    | \bpost.hoc\b
    | \bmixed.effects?\s+model\b | \blme4\b
    | \bconfidence\s+interval\b | \b95\s*%\s*ci\b
    | \bhazard\s+ratio\b | \bodds\s+ratio\b
    """,
    re.VERBOSE,  # Note: NOT re.IGNORECASE — "P =" is capitalised in Nature figures
)

# Stats software (fallback when no full text)
STATS_SOFTWARE_RE = re.compile(
    r"\b(?:GraphPad|Prism|SPSS|STATA|SAS)\b"
    r"|\bR\s+(?:version|v\.?\s*\d|software)"
    r"|\bscipy(?:\.stats)?\b|\bstatsmodels\b",
    re.I,
)

# ── NS-as-evidence detection ──────────────────────────────────────────────────
# Searched in body text (up to start of Methods), or abstract.
NS_PHRASE = re.compile(
    r"""
    \bno\s+significant\s+(?:difference|change|effect|increase|decrease|
                             alteration|variation|impact|association|
                             correlation)\b
    | \bnot\s+significantly?\s+(?:different|altered|changed|affected|
                                   associated|correlated|elevated|reduced)\b
    | \bnon.significant\b | \bnonsignificant\b
    | \babsence\s+of\s+(?:a\s+)?significant
    | \bno\s+(?:detectable|observable|measurable)\s+\w+\s+
        (?:difference|effect|change|alteration)\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

CONCLUSION_LANG = re.compile(
    r"""
    \b(?:suggest|indicate|demonstrat|show|reveal|confirm|establish|
        support|imply|therefore|thus|hence|consequently|
        consistent\s+with|evidence\s+(?:that|for)|conclud|
        rule\s+out|exclude|discount|argue)\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# ── RS checklist boilerplate ─────────────────────────────────────────────────
RS_CHECKLIST_RE = re.compile(
    r"For all statistical analyses.*?Our web collection[^\n]*\n",
    re.DOTALL | re.IGNORECASE,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _pdf_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        pages = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
        return "\n".join(pages)
    except Exception:
        return ""


def _body_text(full_text: str) -> str:
    """Return full text up to (not including) the Methods section."""
    m = METHODS_START.search(full_text)
    return full_text[:m.start()] if m else full_text


def _rs_data_analysis(rs_text: str) -> str:
    clean = RS_CHECKLIST_RE.sub("\n", rs_text)
    m = re.search(
        r"Data analysis\s+(.{10,600}?)(?=\nFor manuscripts|\nData\n|\Z)",
        clean, re.S,
    )
    return m.group(1).strip() if m else ""


def _snippets(text: str, pattern: re.Pattern,
              before: int = 60, after: int = 120, limit: int = 3) -> list[str]:
    hits = []
    for m in pattern.finditer(text):
        s = max(0, m.start() - before)
        e = min(len(text), m.end() + after)
        hits.append(text[s:e].replace("\n", " ").strip())
        if len(hits) >= limit:
            break
    return hits


def _nhst_hits(text: str) -> list[str]:
    return _snippets(text, NHST_RE)


def _ns_evidence_hits(text: str) -> list[str]:
    hits = []
    for m in NS_PHRASE.finditer(text):
        window = text[max(0, m.start() - 300): min(len(text), m.end() + 300)]
        if CONCLUSION_LANG.search(window):
            s = max(0, m.start() - 100)
            e = min(len(text), m.end() + 250)
            hits.append(text[s:e].replace("\n", " ").strip())
            if len(hits) >= 5:
                break
    return hits


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    dataset = json.loads((DATA / "multi_issue_dataset_filtered.json").read_text())
    abstracts = json.loads((DATA / "abstracts_cache.json").read_text())

    records = [
        r for r in dataset["records"]
        if r["sample_size_category"] not in EXCLUDE_CATS
    ]

    n_full_pdf = sum(
        1 for r in records
        if (PDFS / f"{r['doi'].split('/')[-1]}_full.pdf").exists()
    )
    print(f"Analysing {len(records)} records "
          f"(excluded: power_calc + methodology_determined)")
    print(f"Full-text PDFs available: {n_full_pdf} / {len(records)}\n")

    results = []
    nhst_count = 0
    ns_evidence_count = 0

    for i, rec in enumerate(records, 1):
        doi = rec["doi"]
        suffix = doi.split("/")[-1]

        abstract = (abstracts.get(doi) or {}).get("text") or ""
        full_text = _pdf_text(PDFS / f"{suffix}_full.pdf")
        rs_text = _pdf_text(PDFS / f"{suffix}_RS.pdf")

        has_full = bool(full_text)

        if has_full:
            body = _body_text(full_text)
            nhst_hits = _nhst_hits(full_text)   # NHST anywhere (incl. fig legends)
            ns_hits = _ns_evidence_hits(body)   # NS-as-evidence only in body
            nhst_source = "full_text" if nhst_hits else "none"
            ns_source = "full_text" if ns_hits else "none"
        else:
            rs_da = _rs_data_analysis(rs_text)
            nhst_hits = _nhst_hits(abstract)
            if not nhst_hits:
                nhst_hits = _snippets(rs_da, STATS_SOFTWARE_RE, before=0, after=60)
                nhst_source = "rs_data_analysis" if nhst_hits else "none"
            else:
                nhst_source = "abstract"
            ns_hits = _ns_evidence_hits(abstract)
            ns_source = "abstract" if ns_hits else "none"

        nhst_used = bool(nhst_hits)
        ns_as_evidence = bool(ns_hits)

        if nhst_used:
            nhst_count += 1
        if ns_as_evidence:
            ns_evidence_count += 1

        result = {
            "doi": doi,
            "title": rec.get("title", ""),
            "issue": rec.get("issue"),
            "sample_size_category": rec["sample_size_category"],
            "full_text_available": has_full,
            "nhst_used": nhst_used,
            "nhst_source": nhst_source,
            "nhst_evidence_snippets": nhst_hits[:3],
            "ns_as_evidence": ns_as_evidence,
            "ns_source": ns_source,
            "ns_evidence_snippets": ns_hits[:5],
        }
        results.append(result)

        status = []
        if nhst_used:
            status.append("NHST")
        if ns_as_evidence:
            status.append("NS-as-evidence")
        flag = " | ".join(status) if status else "—"
        src_marker = "F" if has_full else "a"
        print(f"  [{i:2d}/{len(records)}] [{src_marker}] {suffix[:30]:<32} "
              f"{rec['sample_size_category']:<22} {flag}")

    # ── Summary ───────────────────────────────────────────────────────────────
    n = len(records)
    n_full = sum(1 for r in results if r["full_text_available"])
    print(f"\nSummary ({n} articles without power calc; {n_full} with full text):")
    print(f"  NHST used:                           {nhst_count:3d} / {n} ({nhst_count/n*100:.0f}%)")
    print(f"    (of {n_full} with full text:        "
          f"{sum(1 for r in results if r['full_text_available'] and r['nhst_used']):3d} / {n_full})")
    print(f"    (of {n-n_full} abstract-only:       "
          f"{sum(1 for r in results if not r['full_text_available'] and r['nhst_used']):3d} / {n-n_full})")
    print(f"  Non-significant used as evidence:    {ns_evidence_count:3d} / {n} ({ns_evidence_count/n*100:.0f}%)")
    print(f"  Both NHST + NS-as-evidence:          "
          f"{sum(1 for r in results if r['nhst_used'] and r['ns_as_evidence']):3d}")

    cats = sorted(set(r["sample_size_category"] for r in results))
    print("\nPer-category breakdown:")
    for cat in cats:
        sub = [r for r in results if r["sample_size_category"] == cat]
        nhst = sum(1 for r in sub if r["nhst_used"])
        ns = sum(1 for r in sub if r["ns_as_evidence"])
        print(f"  {cat:<25} n={len(sub):2d}  NHST={nhst:2d}  NS-evidence={ns:2d}")

    ns_cases = [r for r in results if r["ns_as_evidence"]]
    if ns_cases:
        print(f"\nNS-as-evidence cases ({len(ns_cases)}):")
        for r in ns_cases:
            print(f"\n  {r['doi']}  [{r['sample_size_category']}]")
            for s in r["ns_evidence_snippets"][:2]:
                print(f"  > {s[:250]}")

    out_json = DATA / "stats_reporting_analysis.json"
    out_json.write_text(json.dumps({
        "schema_version": "2.1",
        "source_dataset": "data/multi_issue_dataset_filtered.json",
        "records_analysed": n,
        "excluded_categories": sorted(EXCLUDE_CATS),
        "full_text_available": n_full,
        "summary": {
            "nhst_used": nhst_count,
            "nhst_with_full_text": sum(1 for r in results if r["full_text_available"] and r["nhst_used"]),
            "nhst_abstract_only": sum(1 for r in results if not r["full_text_available"] and r["nhst_used"]),
            "ns_as_evidence": ns_evidence_count,
            "both": sum(1 for r in results if r["nhst_used"] and r["ns_as_evidence"]),
        },
        "results": results,
    }, indent=2))
    print(f"\n[OK] Written {out_json}")

    out_tsv = DATA / "stats_reporting_analysis.tsv"
    cols = ["doi", "issue", "sample_size_category", "full_text_available",
            "nhst_used", "nhst_source", "ns_as_evidence", "ns_source", "title"]
    with open(out_tsv, "w") as f:
        f.write("\t".join(cols) + "\n")
        for r in results:
            row = [str(r.get(c, "")).replace("\t", " ").replace("\n", " ")
                   for c in cols]
            f.write("\t".join(row) + "\n")
    print(f"[OK] Written {out_tsv}")


if __name__ == "__main__":
    main()
