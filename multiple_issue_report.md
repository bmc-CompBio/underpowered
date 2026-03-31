# Sample-Size Justification in Nature: Multi-Issue Report

**Issues:** Nature Vol. 649–651, Issues 8096–8107 (8 January – 26 March 2026)
**Date of analysis:** 30 March 2026
**Pipeline:** automated extraction from Reporting Summary PDFs with manual review of ambiguous cases, plus full-text statistical analysis

---

## 1. Corpus construction

### Starting pool

Crossref was queried for all articles published in Nature (ISSN 0028-0836, DOI prefix `10.1038/s41586-`) across a wide date window (2025-12-01 to 2026-03-27) and grouped by the Crossref `issue` field. Issues 8096–8107 span three volumes:

| Volume | Issues |
|--------|--------|
| Vol. 649 | 8096–8099 |
| Vol. 650 | 8100–8103 |
| Vol. 651 | 8104–8107 |

Correction and retraction notices were excluded by DOI prefix (`d41586-`). This yielded **120 life-science candidates** across 12 issues. Reporting Summary PDF links were located by fetching each article's HTML page and extracting the `data-track-label="reporting summary"` anchor.

**113 articles** had accessible Reporting Summary PDFs. 7 could not be parsed (scanned PDFs or missing RS links).

### Filter 1 — Ecological, evolutionary & environmental sciences form

Articles using the *Ecological, evolutionary & environmental sciences* Reporting Summary were excluded. These studies apply a different sample-size logic (sampling strategy rather than experimental replication) and use a different RS field label. Filter 1 excluded **9 articles**, leaving **104**.

### Filter 2 — Effect/intervention language

A keyword-scoring heuristic applied to title and abstract text identified articles describing experimental interventions or mechanistic findings (positive scores) versus observational, structural, epidemiological, or palaeontological work (negative scores). Articles with score ≤ −1 were auto-excluded; score 0 cases were resolved by manual inspection.

- Auto-excluded: 17
- Manual override — excluded: 4 (non-experimental despite neutral score)
- Manual override — included: 0

This left a **final corpus of 83 articles**.

### Corpus overview by issue

| Issue | Life-science candidates | RS accessible | Final corpus |
|-------|------------------------|---------------|-------------|
| 8096  | —  | 4  | 4  |
| 8097  | —  | 1  | 1  |
| 8098  | —  | 4  | 3  |
| 8099  | —  | 8  | 5  |
| 8100  | —  | 8  | 4  |
| 8101  | —  | 8  | 4  |
| 8102  | —  | 11 | 7  |
| 8103  | —  | 13 | 8  |
| 8104  | —  | 8  | 8  |
| 8105  | —  | 9  | 6  |
| 8106  | —  | 12 | 7  |
| 8107  | —  | 27 | 26 |
| **Total** | **120** | **113** | **83** |

---

## 2. Sample-size category distribution

### Classification scheme

Each article's Reporting Summary "Sample size" field was extracted and classified into one of eight categories:

| Category | Definition |
|----------|------------|
| `power_calc` | Formal a priori power calculation (α, β, effect size specified) |
| `effect_size_estimate` | Quantitative estimate from pilot data or literature; no formal calculation |
| `replication_standard` | Appeal to field convention or replication of a prior study's n |
| `resource_constraint` | Sample size limited by biological availability, budget, or cohort size |
| `methodology_determined` | n inherently defined by the measurement technique (stereology, cryo-EM, single-molecule); no separate determination expected |
| `no_justification` | n stated with no reasoning |
| `na_or_blank` | Field empty, N/A, or not applicable |
| `ambiguous` | Text present but insufficient to classify |

22 initially-ambiguous classifications were resolved by manual review; 9 classifications were overridden based on manual inspection of the verbatim RS text.

### Results

| Category | n | % |
|----------|---|---|
| `replication_standard` | 27 | 33% |
| `resource_constraint` | 23 | 28% |
| `effect_size_estimate` | 13 | 16% |
| `power_calc` | 9 | 11% |
| `na_or_blank` | 6 | 7% |
| `methodology_determined` | 3 | 4% |
| `no_justification` | 2 | 2% |
| **Total** | **83** | |

### Binary adequacy framing

The operative analytic variable is whether a formal power calculation was performed. All other categories — while descriptively distinct — represent variations of "we did not do a power calculation":

| Adequate justification | n | % |
|------------------------|---|---|
| `power_calc` | 9 | 11% |
| `methodology_determined` (principled exception) | 3 | 4% |
| **All other categories** | **71** | **86%** |

**89% of articles lacked a formal power calculation.** The two largest categories — `replication_standard` (33%) and `resource_constraint` (28%) — reflect the dominant practices in Nature life-science papers: copying a predecessor's n or using whatever biological material was available.

---

## 3. Statistical testing in articles without a power calculation

### Motivation

A power calculation quantifies the minimum sample size needed to detect a hypothesised effect with specified probability. Without it, the Type II error rate (probability of missing a real effect) is unknown. The question therefore arises: do the 71 articles that lacked a power calculation still use null-hypothesis statistical testing (NHST) to draw conclusions? And do any use non-significant results as positive evidence — a particularly problematic practice in underpowered studies?

### Method

Full-text PDFs were downloaded for all 71 articles and analysed with regex-based pattern matching across the entire paper text (including figure legends, which carry p-values in Nature format). Two flags were applied:

**`nhst_used`** — any of: explicit p-values (`P < 0.05`, `P = 0.001`, etc.), named statistical tests (t-test, ANOVA, Mann–Whitney, Wilcoxon, Kruskal–Wallis, logistic regression, Cox proportional hazards, etc.), or derived statistics (confidence intervals, FDR, odds ratios, hazard ratios).

**`ns_as_evidence`** — a non-significance phrase ("no significant difference", "not significantly altered", "non-significant", "absence of significant…") appearing within ±300 characters of conclusion language ("suggest", "indicate", "demonstrate", "consistent with", "therefore", "conclude", etc.).

Two of the 71 articles had no experimental setup (one structural biology, one technology development paper) and were correctly excluded from the NHST analysis as non-applicable.

### Results

| Indicator | n | % of 69 experimental |
|-----------|---|----------------------|
| NHST used | 69 | **100%** |
| Non-significant result used as positive evidence | 11 | **16%** |
| Both | 11 | 16% |

Every experimental article that failed to justify its sample size used NHST to draw conclusions. Note that this is detected from the full paper text, not just the abstract; p-values in figure legends count as NHST use.

### Per-category breakdown

| Category | n | NHST | NS as evidence |
|----------|---|------|----------------|
| `replication_standard` | 27 | 27 (100%) | 4 (15%) |
| `resource_constraint` | 23 | 22 (96%) | 4 (17%) |
| `effect_size_estimate` | 13 | 13 (100%) | 2 (15%) |
| `no_justification` | 2 | 2 (100%) | 0 |
| `na_or_blank` | 6 | 5 (83%) | 1 (17%) |

The one `resource_constraint` paper not flagged for NHST and the one `na_or_blank` paper without NHST are the two confirmed non-experimental papers.

### NS-as-evidence cases

The 11 articles where non-significant results were used as positive arguments:

| DOI | Title | Category | Representative snippet |
|-----|-------|----------|----------------------|
| 10.1038/s41586-025-09821-2 | Mutations in mitochondrial ferredoxin FDX2 suppress frataxin deficiency | replication_standard | "was not significantly different from the homozygous fdx-2(A126V) suppressor mutations" |
| 10.1038/s41586-025-09809-y | Viral RNA blocks circularization to evade host codon usage control | replication_standard | "no significant effect on 2A protein or CVB3 RNA levels, suggesting that…" |
| 10.1038/s41586-025-09836-9 | Sterilization and contraception increase lifespan across vertebrates | effect_size_estimate | "not significantly correlated with testes mass after controlling for body mass" |
| 10.1038/s41586-025-09888-x | Plastic landmark anchoring in zebrafish compass neurons | effect_size_estimate | "No significant increase was detected (sign-rank test)" |
| 10.1038/s41586-025-09943-7 | CFAP20 salvages arrested RNAPII from the path of co-directional replisomes | replication_standard | "no significant difference between WT and CFAP20-KO (adjusted p-values:…)" |
| 10.1038/s41586-025-09902-2 | Prefrontal neural geometry of learned cues guides motivated behaviours | na_or_blank | "nonsignificant performance… results indicate that valence and salience information lie…" |
| 10.1038/s41586-025-09983-z | Baby-to-baby strain transmission shapes the developing gut microbiome | resource_constraint | "pairwise comparisons are non significant" (used as substantive finding) |
| 10.1038/s41586-025-10055-5 | Rete ridges form via evolutionarily distinct mechanisms in mammalian skin | replication_standard | "letters indicate no significant difference (P > 0.05)" |
| 10.1038/s41586-025-09958-0 | Predictive coding of reward in the hippocampus | resource_constraint | "no significant correlation with MI… these patterns are consistent" |
| 10.1038/s41586-026-10219-x | Functional hierarchy of the human neocortex across the lifespan | resource_constraint | "non-significant terms would suggest insufficient evidence for systematically distinct…" |
| 10.1038/s41586-026-10266-4 | Exposed phosphatidylserine is an inhibitory molecule in T cell exhaustion | resource_constraint | "showed no significant difference in induced transcriptional changes… Extended Data" |

Two cases (10055-5 and 10219-x) are borderline — the first may reflect figure-annotation convention (P > 0.05 labelling) rather than a substantive claim; the second refers to model terms rather than the primary hypothesis. The remaining 9 involve substantive interpretations based on non-significant tests.

---

## 4. Key observations

**1. Power calculations are rare.** Only 9/83 articles (11%) reported a formal a priori power calculation. This figure is broadly consistent with prior audits of experimental biology literature.

**2. The dominant practices are convention-copying and resource-limitation.** Together, `replication_standard` (33%) and `resource_constraint` (28%) account for 61% of the corpus. In most cases these represent not a determination of sample size but a post-hoc description of how many animals or patients happened to be available or how many the field customarily uses — without any quantitative basis for believing this number provides adequate power.

**3. NHST is universal in experimental papers without power calculations.** 69/69 (100%) of experimental articles that lacked a formal power calculation nonetheless drew conclusions from null-hypothesis significance tests. Without a power calculation, the false-negative rate is unknown; p-values in underpowered studies are unreliable as arbiters of truth.

**4. Non-significant results are regularly used as positive evidence.** In 9–11 of 71 articles (13–15%), a non-significant result was explicitly used to support a claim — for example, arguing that an experimental manipulation had no effect, or that two conditions were equivalent, based on p ≥ 0.05. In the absence of a power calculation, such studies cannot distinguish "no effect" from "effect present but undetected."

**5. The `methodology_determined` category is the only principled exception.** Three articles (4%) used techniques — stereology, cryo-EM particle picking, single-molecule imaging — where sample size is inherently determined by the measurement and independent statistical power calculations are not expected by field convention.

---

## 5. Pipeline

| Script | Function |
|--------|----------|
| `build_manifest_multi.py` | Crossref fetch across issues 8096–8107; groups articles by issue field |
| `find_reporting_summaries.py` | Fetches article HTML pages; extracts Reporting Summary PDF links |
| `extract_sample_size.py` | Downloads RS PDFs; extracts and classifies the sample-size field |
| `filter_corpus.py` | Applies Filter 1 (ecological form) and Filter 2 (effect/intervention language); resolves ambiguous and manual-override cases |
| `run_multi_issue.py` | Orchestrates the three per-issue steps for issues 8096–8106 |
| `merge_datasets.py` | Merges per-issue datasets into `data/multi_issue_dataset.json`; deduplicates by DOI |
| `download_full_papers.py` | Downloads full-text PDFs from nature.com for all non-power-calc articles |
| `analyze_stats_reporting.py` | Scans full-text PDFs for NHST usage and non-significant-as-evidence patterns |

**Data files:**
- `data/multi_issue_dataset_filtered.json` — 83 classified articles, fully reviewed
- `data/stats_reporting_analysis.json` — NHST and NS-as-evidence flags for 71 articles
- `data/stats_reporting_analysis.tsv` — tab-separated for spreadsheet inspection

---

*Analysis performed with Claude Code (claude-sonnet-4-6) on 30 March 2026.*
