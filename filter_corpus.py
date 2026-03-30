"""
Corpus refinement — two sequential filters applied after extraction:

  Filter 1: Exclude articles using the Ecological, evolutionary &
            environmental sciences RS form. These studies have a
            fundamentally different sample-size logic (sampling strategy
            rather than experimental replication), and their RS uses
            different field labels.

  Filter 2: Exclude articles that do not describe treatment / intervention
            effects in their title or abstract. Observational, descriptive,
            epidemiological, structural, and atlas studies are excluded.
            The filter uses a scored keyword approach on title + abstract.

Output:
  data/corpus_filtered.json   — refined records with filter flags
  data/corpus_filtered.tsv    — flat table
"""

import argparse, json, re, time
from pathlib import Path
import requests

DATA = Path("data")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
}

# ------------------------------------------------------------------
# Filter 1: ecological / evolutionary / environmental form
# ------------------------------------------------------------------

def is_ecological_form(rec: dict) -> bool:
    # Field is saved as "rs_form_type" in the dataset records
    ft = (rec.get("rs_form_type") or rec.get("form_type") or "").lower()
    return "ecological" in ft or "evolutionary" in ft or "environmental" in ft

# ------------------------------------------------------------------
# Fetch abstract
# ------------------------------------------------------------------

def fetch_abstract_crossref(doi: str) -> str | None:
    url = f"https://api.crossref.org/works/{doi}"
    try:
        resp = requests.get(url, params={"mailto": "research@example.com"}, timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json().get("message", {})
        abstract = data.get("abstract", "")
        if abstract:
            # Strip JATS XML tags
            abstract = re.sub(r"<[^>]+>", " ", abstract)
            abstract = re.sub(r"\s+", " ", abstract).strip()
            return abstract
    except Exception:
        pass
    return None

def fetch_abstract_nature_page(doi: str) -> str | None:
    suffix = doi.split("10.1038/")[-1]
    url = f"https://www.nature.com/articles/{suffix}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return None
        # Look for <meta name="description" content="..."> or <p class="article__teaser">
        m = re.search(
            r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
            resp.text, re.I | re.DOTALL,
        )
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
        # Try JSON-LD description
        m2 = re.search(r'"description"\s*:\s*"(.*?)"', resp.text, re.S)
        if m2:
            desc = m2.group(1).replace("\\n", " ").replace('\\"', '"')
            return re.sub(r"\s+", " ", desc).strip()[:600]
    except Exception:
        pass
    return None

# ------------------------------------------------------------------
# Filter 2: effect-language scoring
# ------------------------------------------------------------------

# Positive signals: verbs / phrases that indicate a measured effect
# of an intervention, manipulation, or mechanism
EFFECT_POSITIVE = [
    # causal / mechanistic verbs
    r"\bdrive[sd]?\b", r"\bdriving\b", r"\bpromote[sd]?\b", r"\bpromoting\b",
    r"\bsuppress(?:es|ed|ing)?\b", r"\binhibit(?:s|ed|ing)?\b",
    r"\bactivat(?:e[sd]?|ing)\b", r"\binduct(?:s|ed|ing|ion)\b",
    r"\binduce[sd]?\b", r"\binducing\b",
    r"\bimpair(?:s|ed|ing)?\b", r"\brescue[sd]?\b", r"\brestore[sd]?\b",
    r"\benhance[sd]?\b", r"\benhancing\b",
    r"\btrigger[sed]?\b",  r"\bfacilitat(?:e[sd]?|ing)\b",
    r"\brequire[sd]?\b", r"\brecruit[sed]?\b",
    r"\bcaus(?:e[sd]?|ing|ation)\b", r"\bmediat(?:e[sd]?|ing|or)\b",
    r"\bregulat(?:e[sd]?|ing|or|ion)\b",
    r"\bcontribute[sd]?\s+to\b", r"\bcontributing\s+to\b",
    r"\blead[s]?\s+to\b", r"\bdrove\b",
    r"\bblock(?:s|ed|ing)?\b", r"\babolish(?:es|ed|ing)?\b",
    r"\bimpede[sd]?\b", r"\babrogate[sd]?\b",
    r"\bconfer(?:s|red|ring)?\b",  r"\belicit[sed]?\b",
    r"\bpotentiat(?:e[sd]?|ing)\b", r"\bsensitiz(?:e[sd]?|ing)\b",
    r"\bhijack[sed]?\b", r"\bunmask[sed]?\b",
    r"\breprogramm?(?:ing|ed)\b", r"\bcontrol[sled]+\b",
    r"\bsynerg(?:y|istic|ize)\b",
    # experimental / intervention vocabulary
    r"\bintervention\b", r"\btreatment\s+effect\b",
    r"\bknockout\b", r"\bknock(?:-|\s*)out\b", r"\bknockdown\b",
    r"\boverexpression\b", r"\bablation\b", r"\bdepletion\b",
    r"\bengineering\b", r"\bmanipulation\b",
    r"\bin\s+vivo\b", r"\bin\s+vitro\b",
]

# Negative signals: language characteristic of purely observational,
# descriptive, epidemiological, or structural studies
EFFECT_NEGATIVE = [
    r"\bprediction\b", r"\bpredictive\b", r"\bpredict(?:s|ed|ing)\b",
    r"\bepidemiolog",
    r"\bobservational\b", r"\bcohort\s+study\b",
    r"\bprevalence\b", r"\bincidence\b",
    r"\bgenome.wide\s+association\b", r"\bGWAS\b",
    r"\batlas\b", r"\bcharacteriz(?:e[sd]?|ing|ation)\b",
    r"\blandscape\b",
    r"\bstructural\s+basis\b", r"\bmolecular\s+basis\b",
    r"\bcrystal\s+structure\b", r"\bcryo.?em\s+structure\b",
    r"\bphylogen(?:y|etic|omics)\b",
    r"\bevolutionary\s+history\b",
    r"\bsurveillance\b",
    r"\bregistr(?:y|ies)\b",
    r"\bUK\s+Biobank\b", r"\bbiobank\b",
    r"\bnatural\s+history\b",
    r"\bdescribe[sd]?\b", r"\bcharacterise[sd]?\b",
    r"\bmapping\b",
]

def score_effect_language(title: str, abstract: str | None) -> dict:
    """
    Returns a dict with positive_hits, negative_hits, score, and verdict.
    score = positive_hits - negative_hits
    verdict: 'include' (score >= 1) | 'exclude' (score <= -1) | 'uncertain' (0)
    """
    text = ((title or "") + " " + (abstract or "")).lower()
    pos = sum(1 for p in EFFECT_POSITIVE if re.search(p, text, re.I))
    neg = sum(1 for n in EFFECT_NEGATIVE if re.search(n, text, re.I))
    score = pos - neg
    if score >= 1:
        verdict = "include"
    elif score <= -1:
        verdict = "exclude"
    else:
        verdict = "uncertain"
    return {
        "effect_pos_hits": pos,
        "effect_neg_hits": neg,
        "effect_score": score,
        "effect_verdict": verdict,
    }

# ------------------------------------------------------------------
# Manual overrides — applied after automated scoring
# "exclude": force exclude regardless of score
# "include": force include regardless of score
# ------------------------------------------------------------------

MANUAL_OVERRIDES = {
    # ---- Issue 8107 ----
    # Palaeolithic population genetics — behavioural/social form, not experimental life science
    "10.1038/s41586-026-10170-x": "exclude",
    # Wearable-based insulin resistance — resource_constraint; abstract lacks effect verbs but study is experimental
    "10.1038/s41586-026-10219-x": "include",
    # Cinchona alkaloid biosynthesis — resource_constraint + replication_standard; effect language thin in abstract
    "10.1038/s41586-026-10226-y": "include",
    # Cinchona alkaloid synthesis — replication_standard; detailed justification in RS but not in abstract
    "10.1038/s41586-026-10227-x": "include",
    # NHP Neuropixels recording — replication_standard; PDF copy-protected, abstract has no effect keywords
    "10.1038/s41586-026-10267-3": "include",

    # ---- Issues 8096–8106 ----
    # Microflora Danica atlas — environmental microbiome atlas, rs_form_type missing but ecological in nature
    "10.1038/s41586-025-09794-2": "exclude",
    # Palaeometabolomes — archaeological specimens, no experimental manipulation
    "10.1038/s41586-025-09843-w": "exclude",
    # Nutrient requirements of organ-specific metastasis — experimental animal study
    "10.1038/s41586-025-09898-9": "include",
    # Homo sapiens ancient southern African genomes — ancient DNA, no experimental manipulation
    "10.1038/s41586-025-09811-4": "exclude",
    # Plastic landmark anchoring in zebrafish — experimental neuroscience
    "10.1038/s41586-025-09888-x": "include",
    # Distinct neuronal populations in human brain — recording study in epilepsy patients, no intervention
    "10.1038/s41586-025-09910-2": "exclude",
    # Oxygen-free metabolism in bird inner retina — experimental physiology
    "10.1038/s41586-025-09978-w": "include",
    # Ultra-high-throughput genetic design space — no treatment/intervention effects described
    "10.1038/s41586-025-09933-9": "exclude",
    # Prefrontal neural geometry of learned cues — experimental neuroscience
    "10.1038/s41586-025-09902-2": "include",
    # Language model-guided metabolite discovery — exploratory/descriptive, no intervention effects
    "10.1038/s41586-025-09969-x": "exclude",
    # Baby-to-baby microbiome strain transmission — observational but sample size justification relevant
    "10.1038/s41586-025-09983-z": "include",
    # Predictive coding of reward in hippocampus — experimental recording study
    "10.1038/s41586-025-09958-0": "include",
    # Cross-population gene–environment interactions — explorative GWAS, no intervention
    "10.1038/s41586-025-10054-6": "exclude",
}

# Override sample_size_category for records where automated classification was ambiguous.
# Applied after filtering; does not affect filter decisions.
CLASSIFICATION_OVERRIDES = {
    # "sought to include between 12–20 individuals per group" — convention-based minimum N
    "10.1038/s41586-025-09821-2": "replication_standard",
    # All 1,024 LUAD samples from existing Sherlock-Lung cohort — availability constrained
    "10.1038/s41586-025-09825-y": "resource_constraint",
    # Proof-of-concept; no a priori size; statistical testing applied post hoc — resource_constraint
    "10.1038/s41586-025-09929-5": "resource_constraint",
    # All UK Biobank data passing QC filters — availability constrained
    "10.1038/s41586-025-09866-3": "resource_constraint",
    # "at least N for in vitro experiments" — field-convention minimum replicates
    "10.1038/s41586-025-09896-x": "replication_standard",
    # "at least n=5 biological replicates/group to ensure unbiased representation" — replication standard
    "10.1038/s41586-025-10003-3": "replication_standard",
    # "Number of animals assigned per condition" — constrained by available material
    "10.1038/s41586-025-09898-9": "resource_constraint",
    # "Each individual animal represent one data point" — no justification provided
    "10.1038/s41586-025-09978-w": "no_justification",
    # Eight mice trained and recorded; constrained by recording-session capacity
    "10.1038/s41586-025-09958-0": "resource_constraint",
}

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/sample_size_dataset.json",
                        help="Input dataset JSON (default: data/sample_size_dataset.json)")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    stem = dataset_path.stem  # e.g. "multi_issue_dataset" or "sample_size_dataset"
    out_json = DATA / f"{stem}_filtered.json"
    out_tsv  = DATA / f"{stem}_filtered.tsv"

    dataset = json.loads(dataset_path.read_text())
    records = dataset["records"]

    print(f"Total records before filtering: {len(records)}\n")

    # ---- Filter 1: ecological form --------------------------------
    f1_keep = [r for r in records if not is_ecological_form(r)]
    f1_excl = [r for r in records if is_ecological_form(r)]
    print(f"Filter 1 — ecological/evolutionary/environmental form:")
    print(f"  Excluded ({len(f1_excl)}):")
    for r in f1_excl:
        print(f"    {r['doi']} | {(r['title'] or '')[:60]}")
    print(f"  Remaining: {len(f1_keep)}\n")

    # ---- Fetch abstracts for Filter 2 ----------------------------
    print("Fetching abstracts (Crossref first, nature.com fallback)...")
    abstract_cache_path = DATA / "abstracts_cache.json"
    abstract_cache = {}
    if abstract_cache_path.exists():
        abstract_cache = json.loads(abstract_cache_path.read_text())

    for i, rec in enumerate(f1_keep):
        doi = rec["doi"]
        if doi in abstract_cache:
            continue
        abs_cr = fetch_abstract_crossref(doi)
        if abs_cr:
            abstract_cache[doi] = {"source": "crossref", "text": abs_cr}
            print(f"  [{i+1:2d}] CR ✓ {doi[:40]}")
        else:
            time.sleep(0.5)
            abs_np = fetch_abstract_nature_page(doi)
            if abs_np:
                abstract_cache[doi] = {"source": "nature_page", "text": abs_np}
                print(f"  [{i+1:2d}] NP ✓ {doi[:40]}")
            else:
                abstract_cache[doi] = {"source": "none", "text": None}
                print(f"  [{i+1:2d}] MISS {doi[:40]}")
        time.sleep(1.0)

    abstract_cache_path.write_text(json.dumps(abstract_cache, indent=2))

    # ---- Filter 2: effect language --------------------------------
    print(f"\nFilter 2 — effect language in title + abstract:\n")
    annotated = []
    for rec in f1_keep:
        doi = rec["doi"]
        title = rec.get("title") or ""
        abstract = (abstract_cache.get(doi) or {}).get("text") or ""
        scores = score_effect_language(title, abstract)
        annotated.append({**rec, **scores,
                          "abstract": abstract[:400] if abstract else None,
                          "filter1_excluded": False})

    # Apply manual overrides
    for r in annotated:
        if r["doi"] in MANUAL_OVERRIDES:
            r["effect_verdict"] = MANUAL_OVERRIDES[r["doi"]]
            r["manual_override"] = True
        else:
            r["manual_override"] = False

    # Report
    for r in annotated:
        mark = {"include": "✓", "exclude": "✗", "uncertain": "?"}.get(r["effect_verdict"], "?")
        override_flag = " [override]" if r.get("manual_override") else ""
        print(f"  {mark} score={r['effect_score']:+d} ({r['effect_pos_hits']}+/{r['effect_neg_hits']}-)"
              f"  {r['doi'][:43]}  {(r['title'] or '')[:50]}{override_flag}")

    include   = [r for r in annotated if r["effect_verdict"] == "include"]
    uncertain = [r for r in annotated if r["effect_verdict"] == "uncertain"]
    exclude   = [r for r in annotated if r["effect_verdict"] == "exclude"]

    print(f"\n  Include:   {len(include)}")
    print(f"  Uncertain: {len(uncertain)}")
    print(f"  Exclude:   {len(exclude)}")

    # ---- Final corpus: include + uncertain (manual review) --------
    final = [r for r in annotated if r["effect_verdict"] in ("include", "uncertain")]

    # Apply classification overrides
    for r in final:
        if r["doi"] in CLASSIFICATION_OVERRIDES:
            r["sample_size_category"] = CLASSIFICATION_OVERRIDES[r["doi"]]
            r["classification_override"] = True

    print(f"\nFinal corpus (include + uncertain pending review): {len(final)}")

    from collections import Counter
    cats = Counter(r["sample_size_category"] for r in final)
    print(f"Category distribution: {dict(cats)}")

    # ---- Save -------------------------------------------------------
    out = {
        **{k: v for k, v in dataset.items() if k != "records"},
        "filter_log": {
            "f1_ecological_excluded": len(f1_excl),
            "f2_effect_include": len(include),
            "f2_effect_uncertain": len(uncertain),
            "f2_effect_exclude": len(exclude),
            "final_corpus_size": len(final),
        },
        "records": final,
    }
    out_json.write_text(json.dumps(out, indent=2))

    # TSV
    with open(out_tsv, "w") as f:
        cols = ["doi", "title", "issue", "form_type", "subject_classification",
                "effect_verdict", "effect_score",
                "sample_size_category", "extraction_confidence",
                "sample_size_raw", "abstract"]
        f.write("\t".join(cols) + "\n")
        for r in final:
            row = [str(r.get(c) or "").replace("\t", " ").replace("\n", " ")[:300]
                   for c in cols]
            f.write("\t".join(row) + "\n")

    print(f"\n[OK] Written {out_json} and {out_tsv}")

if __name__ == "__main__":
    main()
