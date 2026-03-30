"""
Build article manifests for multiple Nature issues in a single Crossref pass.

Fetches all s41586 research DOIs published between 2025-12-01 and 2026-03-27,
groups them by issue number, and writes data/manifest_{issue}.json for each
of the 12 target issues (8096–8107).

Issue 8107 is also (re-)written so its manifest uses the same wide-fetch
approach as all other issues.
"""

import json, re, time
from pathlib import Path
from collections import defaultdict
import requests

DATA = Path("data")
DATA.mkdir(exist_ok=True)

NATURE_ISSN = "0028-0836"

TARGET_ISSUES = list(range(8096, 8108))  # 8096 .. 8107 inclusive

# Volume mapping (verified from Crossref)
ISSUE_VOLUME = {
    **{i: 649 for i in range(8095, 8100)},   # 8095-8099 → Vol 649
    **{i: 650 for i in range(8100, 8104)},   # 8100-8103 → Vol 650
    **{i: 651 for i in range(8104, 8108)},   # 8104-8107 → Vol 651
}

# Approximate cover dates (Wednesdays)
ISSUE_DATE = {
    8096: "2026-01-08", 8097: "2026-01-15", 8098: "2026-01-22", 8099: "2026-01-29",
    8100: "2026-02-05", 8101: "2026-02-12", 8102: "2026-02-19", 8103: "2026-02-26",
    8104: "2026-03-05", 8105: "2026-03-12", 8106: "2026-03-19", 8107: "2026-03-26",
}

EXCLUDE_TITLE_RE = re.compile(
    r"^(retraction|correction|erratum|editorial expression|publisher correction|author correction)",
    re.I,
)

LIFE_KW = [
    "gene", "genes", "genomic", "genome", "protein", "enzyme", "receptor",
    "rna", "dna", "mrna", "crispr", "epigenetic", "chromatin", "histone",
    "transcription", "translation", "ribosome", "kinase", "ligase",
    "ubiquitin", "proteasome", "autophagy", "mitochondria",
    "cell", "cells", "stem cell", "neuron", "neural", "cortex", "synapse",
    "axon", "dendrite", "astrocyte", "microglia", "oligodendrocyte",
    "fibroblast", "macrophage", "lymphocyte", "t cell", "b cell",
    "immune", "immunotherapy", "cancer", "tumour", "tumor", "carcinoma",
    "metastasis", "apoptosis",
    "insulin", "glucose", "obesity", "diabetes", "cardiac", "heart",
    "liver", "kidney", "lung", "brain", "gut", "intestine", "microbiome",
    "pathogen", "bacteria", "virus", "viral", "infection", "antibiotic",
    "vaccine", "antibody", "antigen",
    "evolution", "evolutionary", "phylogenet", "species", "mammal",
    "dog", "primate", "rodent", "insect", "plant", "flower", "seed",
    "forest", "ecosystem", "biodiversity",
    "hippocampus", "amygdala", "dopamine", "serotonin", "purkinje",
    "cerebellum", "inferotemporal", "neocortex", "spinal",
    "alkaloid", "biosynthesis", "metabol", "hormone", "thymus", "thymic",
    "oocyte", "embryo", "fertility", "aging", "lifespan",
    "parasit", "worm", "cysteine", "glutathione",
]

NON_LIFE_KW = [
    "quantum", "photon", "laser", "optical", "optic", "superluminal",
    "gravitational", "black hole", "neutron star", "galaxy", "cosmic",
    "topological", "superconductor", "ferroelectric", "magnon",
    "soliton", "nanophotonic", "lithium niobate", "spin-correlated",
    "radical pair", "magnetic resonance",
    "solar cell", "perovskite", "memristor", "electrolyte", "battery",
    "electrode", "transistor", "semiconductor", "alloy", "ceramic",
    "corrosion", "dendrite growth", "anode",
    "co2", "methane", "climate", "glacial", "ice age", "tectonic",
    "volcanic", "seismic", "magma", "river", "precipitation", "ocean heat",
    "greenhouse gas", "radiative forcing",
    "backpropagation", "neural network", "ai research",
    "alkene", "alkyne", "electrochemical", "electrochem",
]


def score_title(title: str) -> str:
    if not title:
        return "uncertain"
    t = title.lower()
    life_hits = sum(1 for kw in LIFE_KW if kw in t)
    non_life_hits = sum(1 for kw in NON_LIFE_KW if kw in t)
    if life_hits > 0 and non_life_hits == 0:
        return "life_science"
    if non_life_hits > 0 and life_hits == 0:
        return "non_life_science"
    if life_hits > 0 and non_life_hits > 0:
        return "uncertain_mixed"
    return "uncertain"


def fetch_crossref_wide():
    """Fetch all s41586 DOIs published Dec 2025 – Mar 2026 in a single paginated pass."""
    url = f"https://api.crossref.org/journals/{NATURE_ISSN}/works"
    all_items = []
    cursor = "*"
    while True:
        params = {
            "filter": "from-pub-date:2025-12-01,until-pub-date:2026-03-27",
            "rows": 200,
            "select": "DOI,title,type,published,subject,volume,issue,URL,abstract",
            "cursor": cursor,
            "mailto": "research@example.com",
        }
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        msg = resp.json()["message"]
        items = msg.get("items", [])
        if not items:
            break
        all_items.extend(items)
        cursor = msg.get("next-cursor")
        total = msg.get("total-results", 0)
        print(f"  fetched {len(all_items)}/{total} ...", end="\r")
        if len(all_items) >= total or cursor is None:
            break
        time.sleep(0.5)
    print()
    return all_items


def build_article(item: dict) -> dict:
    title = (item.get("title") or [""])[0]
    pub = item.get("published", {}).get("date-parts", [[None]])[0]
    pub_date = "-".join(str(p) for p in pub if p) if pub else ""
    return {
        "doi": item.get("DOI", "").lower(),
        "title": title,
        "volume": str(item.get("volume", "")),
        "issue": str(item.get("issue", "")),
        "published_date": pub_date,
        "subject_classification": score_title(title),
        "reporting_summary_url": None,
        "sample_size_raw": None,
        "sample_size_category": None,
    }


def main():
    print("[1] Fetching Crossref records (Dec 2025 – Mar 2026)...")
    raw = fetch_crossref_wide()
    print(f"    Total raw records: {len(raw)}")

    # Keep only s41586 research DOIs, no corrections
    research = [
        i for i in raw
        if "10.1038/s41586" in i.get("DOI", "")
        and not EXCLUDE_TITLE_RE.match((i.get("title") or [""])[0])
    ]
    print(f"    After filtering: {len(research)} research articles\n")

    # Group by issue
    by_issue = defaultdict(list)
    for item in research:
        iss = item.get("issue")
        if iss:
            by_issue[iss].append(item)

    print("Issue coverage:")
    for iss in sorted(by_issue.keys()):
        n = len(by_issue[iss])
        print(f"  Issue {iss}: {n} articles")

    # Write per-issue manifests for target issues
    print()
    for issue_num in TARGET_ISSUES:
        issue_str = str(issue_num)
        articles_raw = by_issue.get(issue_str, [])
        if not articles_raw:
            print(f"[!] Issue {issue_num}: no articles found — skipping")
            continue

        articles = [build_article(i) for i in articles_raw]
        articles.sort(key=lambda a: a["doi"])

        from collections import Counter
        cls = Counter(a["subject_classification"] for a in articles)
        life_n = cls.get("life_science", 0)
        vol = ISSUE_VOLUME.get(issue_num, "?")
        date = ISSUE_DATE.get(issue_num, "?")
        print(f"Issue {issue_num} (Vol {vol}, {date}): {len(articles)} total, {life_n} life-science candidates")

        out = {
            "corpus_version": f"nature_v{vol}_i{issue_num}",
            "source_issue": {
                "journal": "Nature",
                "issn": NATURE_ISSN,
                "volume": vol,
                "issue": issue_num,
                "date": date,
            },
            "total_articles": len(articles),
            "articles": articles,
        }
        path = DATA / f"manifest_{issue_num}.json"
        path.write_text(json.dumps(out, indent=2))
        print(f"  -> {path}")

    print("\n[OK] All manifests written.")


if __name__ == "__main__":
    main()
