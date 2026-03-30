"""
Merge per-issue dataset_{issue}.json files into a single
data/multi_issue_dataset.json.

Also writes data/multi_issue_dataset.tsv for easy inspection.

Run after all issues have been processed:
  python merge_datasets.py
"""

import json
from pathlib import Path
from collections import Counter

DATA = Path("data")

ISSUES = list(range(8096, 8108))  # 8096..8107 inclusive


def main():
    all_records = []
    issue_stats = []
    missing = []

    for issue in ISSUES:
        path = DATA / f"dataset_{issue}.json"
        # Fallback for issue 8107 legacy filename
        if not path.exists() and issue == 8107:
            path = DATA / "sample_size_dataset.json"
        if not path.exists():
            print(f"[!] Missing: dataset_{issue}.json")
            missing.append(issue)
            continue

        data = json.loads(path.read_text())
        records = data.get("records", [])
        all_records.extend(records)

        cats = Counter(r["sample_size_category"] for r in records)
        n_life = data.get("life_science_candidates", len(records))
        n_rs = data.get("articles_with_rs_url", sum(1 for r in records if r.get("reporting_summary_url")))
        issue_stats.append({
            "issue": issue,
            "source_issue": data.get("source_issue", {}),
            "life_science_candidates": n_life,
            "articles_with_rs_url": n_rs,
            "articles_extracted": len(records),
            "categories": dict(cats),
        })
        print(f"Issue {issue}: {len(records)} records — {dict(cats)}")

    if missing:
        print(f"\n[!] {len(missing)} issue(s) missing: {missing}")
        print("    Run run_multi_issue.py first, then re-run merge_datasets.py")

    print(f"\nTotal records across {len(issue_stats)} issues: {len(all_records)}")

    # Deduplicate by DOI (keep first occurrence — shouldn't happen but safety net)
    seen = set()
    unique_records = []
    for r in all_records:
        if r["doi"] not in seen:
            seen.add(r["doi"])
            unique_records.append(r)
    if len(unique_records) < len(all_records):
        print(f"[!] Removed {len(all_records) - len(unique_records)} duplicate DOIs")

    cats_total = Counter(r["sample_size_category"] for r in unique_records)
    print(f"Category distribution: {dict(cats_total)}")

    out = {
        "schema_version": "1.0",
        "issues_included": ISSUES,
        "issues_missing": missing,
        "total_records": len(unique_records),
        "category_distribution": dict(cats_total),
        "issue_stats": issue_stats,
        "classification_categories": {
            "power_calc": "Formal a priori power calculation (α, β, effect size specified)",
            "effect_size_estimate": "Quantitative estimate from pilot/literature, no formal calc",
            "replication_standard": "Appeal to field convention or replication of prior study",
            "resource_constraint": "Sample size limited by availability, budget, or cohort size",
            "methodology_determined": "Sample size inherently defined by measurement technique (stereology, cryo-EM, single-molecule); no separate determination step expected",
            "no_justification": "n stated but no reasoning provided",
            "na_or_blank": "Field empty, N/A, or not applicable",
            "ambiguous": "Text present but insufficient to classify",
        },
        "records": unique_records,
    }

    out_path = DATA / "multi_issue_dataset.json"
    out_path.write_text(json.dumps(out, indent=2))
    print(f"\n[OK] Written {out_path}")

    tsv_path = DATA / "multi_issue_dataset.tsv"
    with open(tsv_path, "w") as f:
        cols = ["doi", "title", "volume", "issue", "published_date",
                "rs_form_type", "sample_size_category", "extraction_confidence",
                "sample_size_raw"]
        f.write("\t".join(cols) + "\n")
        for rec in unique_records:
            row = [str(rec.get(c) or "").replace("\t", " ").replace("\n", " ")[:300]
                   for c in cols]
            f.write("\t".join(row) + "\n")
    print(f"[OK] Written {tsv_path}")


if __name__ == "__main__":
    main()
