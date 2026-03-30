"""
Build a clean manifest for Nature issue 8107 (26 March 2026).

Strategy:
  1. Pull all s41586 research DOIs from the past two weeks via Crossref.
  2. Exclude corrections, retractions, editorial notes.
  3. Label each article as life-science / non-life-science / uncertain
     using title-keyword heuristics (subjects are empty in Crossref for Nature).
  4. Write data/manifest_8107.json with candidate articles.
"""

import json, re, time
from pathlib import Path
import requests

DATA = Path("data")
DATA.mkdir(exist_ok=True)

NATURE_ISSN = "0028-0836"

# ------------------------------------------------------------------
# Exclusion patterns (corrections / retractions / expressions of concern)
# ------------------------------------------------------------------
EXCLUDE_TITLE_RE = re.compile(
    r"^(retraction|correction|erratum|editorial expression|publisher correction|author correction)",
    re.I,
)

# ------------------------------------------------------------------
# Life-science keyword sets (title-level heuristic)
# ------------------------------------------------------------------
LIFE_KW = [
    # molecular / cell biology
    "gene", "genes", "genomic", "genome", "protein", "enzyme", "receptor",
    "rna", "dna", "mrna", "crispr", "epigenetic", "chromatin", "histone",
    "transcription", "translation", "ribosome", "kinase", "ligase",
    "ubiquitin", "proteasome", "autophagy", "mitochondria",
    # cell biology
    "cell", "cells", "stem cell", "neuron", "neural", "cortex", "synapse",
    "axon", "dendrite", "astrocyte", "microglia", "oligodendrocyte",
    "fibroblast", "macrophage", "lymphocyte", "t cell", "b cell",
    "immune", "immunotherapy", "cancer", "tumour", "tumor", "carcinoma",
    "metastasis", "apoptosis",
    # physiology / medicine
    "insulin", "glucose", "obesity", "diabetes", "cardiac", "heart",
    "liver", "kidney", "lung", "brain", "gut", "intestine", "microbiome",
    "pathogen", "bacteria", "virus", "viral", "infection", "antibiotic",
    "vaccine", "antibody", "antigen",
    # ecology / evolution
    "evolution", "evolutionary", "phylogenet", "species", "mammal",
    "dog", "primate", "rodent", "insect", "plant", "flower", "seed",
    "forest", "ecosystem", "biodiversity",
    # neuroscience
    "hippocampus", "amygdala", "dopamine", "serotonin", "purkinje",
    "cerebellum", "inferotemporal", "neocortex", "spinal",
    # other bio
    "alkaloid", "biosynthesis", "metabol", "hormone", "thymus", "thymic",
    "oocyte", "embryo", "fertility", "aging", "lifespan",
    "parasit", "worm", "cysteine", "glutathione",
]

NON_LIFE_KW = [
    # physics
    "quantum", "photon", "laser", "optical", "optic", "superluminal",
    "gravitational", "black hole", "neutron star", "galaxy", "cosmic",
    "topological", "superconductor", "ferroelectric", "magnon",
    "soliton", "nanophotonic", "lithium niobate", "spin-correlated",
    "radical pair", "magnetic resonance",
    # materials / engineering
    "solar cell", "perovskite", "memristor", "electrolyte", "battery",
    "electrode", "transistor", "semiconductor", "alloy", "ceramic",
    "corrosion", "dendrite growth", "anode",
    # geoscience / climate
    "co2", "methane", "climate", "glacial", "ice age", "tectonic",
    "volcanic", "seismic", "magma", "river", "precipitation", "ocean heat",
    "greenhouse gas", "radiative forcing",
    # computer science / AI (borderline)
    "backpropagation", "neural network", "ai research",
    # chemistry (non-bio)
    "alkene", "alkyne", "electrochemical", "electrochem",
]

def score_title(title: str) -> str:
    """Return 'life_science', 'non_life_science', or 'uncertain'."""
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

# ------------------------------------------------------------------
# Fetch from Crossref
# ------------------------------------------------------------------

def fetch_crossref_research(date_from, date_until):
    url = f"https://api.crossref.org/journals/{NATURE_ISSN}/works"
    all_items = []
    cursor = "*"
    while True:
        params = {
            "filter": f"from-pub-date:{date_from},until-pub-date:{date_until}",
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
        if len(all_items) >= total:
            break
        if cursor is None:
            break
        time.sleep(0.5)
    print()
    return all_items

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    print("[1] Fetching Crossref records (March 15–27, 2026)...")
    raw = fetch_crossref_research("2026-03-15", "2026-03-27")
    print(f"    Total raw records: {len(raw)}")

    # Keep only s41586 research DOIs
    research = [i for i in raw if "10.1038/s41586" in i.get("DOI", "")]
    print(f"    After s41586 filter: {len(research)}")

    # Exclude corrections / retractions
    clean = [i for i in research if not EXCLUDE_TITLE_RE.match(
        (i.get("title") or [""])[0]
    )]
    print(f"    After excluding corrections/retractions: {len(clean)}")

    # Build records
    articles = []
    for item in clean:
        title = (item.get("title") or [""])[0]
        pub = item.get("published", {}).get("date-parts", [[None]])[0]
        pub_date = "-".join(str(p) for p in pub if p) if pub else ""
        doi = item.get("DOI", "").lower()
        vol = str(item.get("volume", ""))
        iss = str(item.get("issue", ""))
        classification = score_title(title)

        articles.append({
            "doi": doi,
            "title": title,
            "volume": vol,
            "issue": iss,
            "published_date": pub_date,
            "subject_classification": classification,
            "reporting_summary_url": None,
            "sample_size_raw": None,
            "sample_size_category": None,
        })

    # Sort: issue-assigned first, then by DOI
    articles.sort(key=lambda a: (0 if a["issue"] == "8107" else 1, a["doi"]))

    # Summary
    from collections import Counter
    cls = Counter(a["subject_classification"] for a in articles)
    iss_dist = Counter(a["issue"] or "unassigned" for a in articles)
    print(f"\n=== Clean manifest ===")
    print(f"  Total articles: {len(articles)}")
    print(f"  By issue: {dict(iss_dist)}")
    print(f"  By subject classification: {dict(cls)}")
    print()
    print("Life-science candidates:")
    for a in articles:
        if a["subject_classification"] == "life_science":
            print(f"  [{a['issue'] or '?'}] {a['doi']} | {a['title'][:70]}")
    print()
    print("Non-life-science:")
    for a in articles:
        if a["subject_classification"] == "non_life_science":
            print(f"  [{a['issue'] or '?'}] {a['doi']} | {a['title'][:70]}")
    print()
    print("Uncertain:")
    for a in articles:
        if "uncertain" in a["subject_classification"]:
            print(f"  [{a['issue'] or '?'}] {a['doi']} | {a['title'][:70]}")

    out = {
        "corpus_version": "nature_v651_i8107",
        "source_issue": {
            "journal": "Nature",
            "issn": NATURE_ISSN,
            "volume": 651,
            "issue": 8107,
            "date": "2026-03-26",
        },
        "total_articles": len(articles),
        "articles": articles,
    }
    path = DATA / "manifest_8107.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"\n[OK] Written {path}")

if __name__ == "__main__":
    main()
