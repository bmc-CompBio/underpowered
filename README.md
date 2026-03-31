# underpowered

Automated audit of sample-size justifications and statistical practices in Nature (issues 8096–8107, January–March 2026).

Extracts the sample-size disclosure field from Nature Reporting Summary PDFs, classifies it, and cross-references it with full-text statistical analysis. Findings: 9/83 articles (11%) reported a formal power calculation; 69/69 experimental articles without a power calculation used NHST to draw conclusions.

**Reports:** [`multiple_issue_report.md`](multiple_issue_report.md) · [`blog.md`](blog.md)

---

## Requirements

Python ≥ 3.10. Install dependencies:

```bash
pip install requests beautifulsoup4 pdfplumber
```

Optional — OCR fallback for scanned PDFs (rarely needed):

```bash
pip install pdf2image pytesseract
brew install tesseract   # macOS
```

---

## Pipeline overview

```
Crossref API
     │
     ▼
build_manifest_multi.py      →  data/manifest_{issue}.json          (one per issue)
     │
     ▼
find_reporting_summaries.py  →  data/manifest_{issue}_with_rs.json  (RS PDF URLs added)
     │
     ▼
extract_sample_size.py       →  data/dataset_{issue}.json           (classifications)
     │
     ▼
merge_datasets.py            →  data/multi_issue_dataset.json       (merged)
     │
     ▼
filter_corpus.py             →  data/multi_issue_dataset_filtered.json  ← main output
     │
     ▼
download_full_papers.py      →  data/pdfs/{suffix}_full.pdf         (requires institutional access)
     │
     ▼
analyze_stats_reporting.py   →  data/stats_reporting_analysis.json  ← analysis output
```

---

## Step-by-step instructions

### 1. Build article manifests

Fetches all `10.1038/s41586-` DOIs from Crossref for a given date window and groups them by issue number. Edit `TARGET_ISSUES` and `ISSUE_DATE` at the top of the script to cover different issues.

```bash
python build_manifest_multi.py
```

Output: `data/manifest_{issue}.json` for each target issue.

### 2. Find Reporting Summary PDF links

For each life-science candidate in a manifest, fetches the article HTML page and extracts the link to the Reporting Summary PDF.

```bash
# Single issue
python find_reporting_summaries.py --issue 8107

# All issues in sequence (8096–8106; 8107 handled separately above)
python run_multi_issue.py --start 8096
```

Output: `data/manifest_{issue}_with_rs.json`.

### 3. Extract and classify sample-size fields

Downloads the Reporting Summary PDFs (cached in `data/pdfs/`) and extracts the "Sample size" free-text field. Classifies each answer into one of eight categories using regex patterns with an OCR fallback for scanned PDFs.

```bash
# Single issue
python extract_sample_size.py --issue 8107

# All issues (via orchestrator)
python run_multi_issue.py
```

Output: `data/dataset_{issue}.json`.

Classification categories:

| Category | Description |
|----------|-------------|
| `power_calc` | Formal a priori power calculation (α, β, effect size specified) |
| `effect_size_estimate` | Quantitative estimate from pilot data or literature; no formal calculation |
| `replication_standard` | Appeal to field convention or replication of a prior study's n |
| `resource_constraint` | Sample size limited by availability, budget, or cohort size |
| `methodology_determined` | n inherently determined by the technique (stereology, cryo-EM, single-molecule) |
| `no_justification` | n stated with no reasoning |
| `na_or_blank` | Field empty, N/A, or not applicable |
| `ambiguous` | Text present but insufficient to classify |

### 4. Merge per-issue datasets

Combines all per-issue JSON files, deduplicates by DOI, and writes a single merged dataset.

```bash
python merge_datasets.py
```

Output: `data/multi_issue_dataset.json`.

### 5. Filter corpus

Applies two sequential filters:

- **Filter 1** — removes articles using the *Ecological, evolutionary & environmental sciences* Reporting Summary form (different sample-size logic)
- **Filter 2** — removes non-experimental articles (structural, observational, palaeontological) using a keyword-scoring heuristic on title and abstract

Manual overrides for borderline cases are hardcoded in `MANUAL_OVERRIDES` and `CLASSIFICATION_OVERRIDES` dicts at the top of the script.

```bash
python filter_corpus.py
# or, to filter a different input file:
python filter_corpus.py --dataset data/multi_issue_dataset.json
```

Output: `data/multi_issue_dataset_filtered.json` — **the main classified corpus**.

### 6. Download full-text PDFs

Downloads full-text PDFs from `nature.com`. Requires institutional network access (on-campus or VPN). Already-downloaded files are skipped.

```bash
# Check what's missing without downloading
python download_full_papers.py --check

# Download all pending
python download_full_papers.py
```

PDFs saved to `data/pdfs/{doi-suffix}_full.pdf`.

If institutional access is unavailable for some articles, the script prints a list of direct URLs for manual download. Save each file as `data/pdfs/{doi-suffix}_full.pdf`.

### 7. Analyse statistical reporting

Scans full-text PDFs for NHST usage and non-significant-as-evidence patterns. Falls back to abstract text for articles without a full-text PDF.

```bash
python analyze_stats_reporting.py
```

Output: `data/stats_reporting_analysis.json`.

Two flags per article:
- **`nhst_used`** — p-values, named statistical tests, confidence intervals, FDR, odds ratios, etc. detected anywhere in the full text (including figure legends)
- **`ns_as_evidence`** — a non-significance phrase ("no significant difference", "non-significant", etc.) appearing within 300 characters of conclusion language ("suggest", "indicate", "demonstrate", "consistent with", etc.)

---

## Extending to new issues

1. Add the new issue numbers and their publication dates to `TARGET_ISSUES` and `ISSUE_DATE` in `build_manifest_multi.py`
2. Re-run steps 1–5
3. Add any new manual overrides to `filter_corpus.py` if ambiguous cases arise
4. Re-run steps 6–7

---

## Repository contents

```
.
├── build_manifest_multi.py      Crossref fetch → per-issue article manifests
├── find_reporting_summaries.py  Locate RS PDF links on article HTML pages
├── extract_sample_size.py       Download RS PDFs, extract + classify sample-size field
├── run_multi_issue.py           Orchestrate steps 2–3 across multiple issues
├── merge_datasets.py            Merge per-issue datasets into one file
├── filter_corpus.py             Filter 1 (ecological form) + Filter 2 (study design)
├── download_full_papers.py      Download full-text PDFs (institutional access)
├── analyze_stats_reporting.py   NHST usage + NS-as-evidence detection
├── build_manifest.py            (pilot script for single issue, superseded)
├── fetch_issue_manifest.py      (pilot script, superseded)
├── data/
│   ├── multi_issue_dataset_filtered.json   Classified corpus — 83 articles
│   └── stats_reporting_analysis.json       NHST + NS-as-evidence flags — 71 articles
├── multiple_issue_report.md     Full analysis report
├── blog.md                      Blog post draft
└── single_issue_report.md       Pilot report (issue 8107 only)
```

---

## Data files

The two canonical outputs committed to this repository:

**`data/multi_issue_dataset_filtered.json`** — 83 classified articles. Each record contains DOI, title, issue, RS form type, verbatim sample-size text, classification category, extraction confidence, and filter metadata.

**`data/stats_reporting_analysis.json`** — NHST and NS-as-evidence flags for 71 articles (excluding `power_calc` and `methodology_determined`). Each record includes the source (full text vs. abstract), evidence snippets, and article metadata.

All intermediate files (`data/manifest_*.json`, `data/dataset_*.json`, `data/abstracts_cache.json`, `data/pdfs/`) are excluded from version control and must be regenerated by running the pipeline.

---

## Citation

Straub T. (2026). *underpowered: automated audit of sample-size justifications in Nature.* https://github.com/bmc-CompBio/underpowered
