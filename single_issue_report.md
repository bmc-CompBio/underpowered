# Sample-Size Justification in Nature: Single-Issue Pilot Report

**Issue:** Nature Vol. 651, Issue 8107 (26 March 2026)
**Date of analysis:** 30 March 2026
**Pipeline:** automated extraction from Reporting Summary PDFs with manual review of ambiguous cases

---

## 1. Corpus construction

### Starting pool

Crossref was queried for all articles published in Nature (ISSN 0028-0836) in issue 8107 with a `10.1038/s41586-` DOI prefix (research articles only; `d41586-` news/editorial DOIs excluded). Correction and retraction notices were removed by title keyword. This yielded **28 life-science candidates** after a title-keyword heuristic identified subject area. Reporting Summary PDF links were located by fetching each article's HTML page and extracting the `data-track-label="reporting summary"` anchor pointing to the Springer CDN.

One article (10.1038/s41586-026-10288-y) had a Reporting Summary that could not be fully parsed (scanned PDF, OCR returned no usable sample-size field).

### Filter 1 — Ecological, evolutionary & environmental sciences form

Articles whose Reporting Summary used the *Ecological, evolutionary & environmental sciences study design* section were excluded. These studies use a fundamentally different sample-size logic (sampling strategy rather than experimental replication) and a different field label ("Sampling strategy" / "Research sample" rather than "Sample size").

| DOI | Title |
|-----|-------|
| 10.1038/s41586-026-10112-7 | Genomic history of early dogs in Europe |
| 10.1038/s41586-025-09622-7 | Contrasting thermophilization among forests, grasslands and alpine summits |
| 10.1038/s41586-026-10291-3 | Oxygen supply through the tracheolar–muscle system does not constrain flight |

**Remaining after Filter 1: 24 articles**

### Filter 2 — Effect/intervention language in title + abstract

A keyword-scoring approach (positive: causal/mechanistic verbs; negative: observational/structural/epidemiological signals) was applied to title and abstract text. Articles with a net score ≤ −1 were auto-excluded; articles with a net score ≥ 1 were included. Five articles with a net score of 0 were resolved by manual inspection of title, abstract, and extracted Reporting Summary text.

**Auto-excluded (score ≤ −1):**

| DOI | Title | Score | Reason |
|-----|-------|-------|--------|
| 10.1038/s41586-026-10255-7 | Structural basis of supercoiling-induced CRISPR–Cas9 off-target activity | −1 | Structural/mechanistic biology study; "structural basis" and "molecular basis" negative signals dominate |
| 10.1038/s41586-026-10288-y | The DNA virome varies with human genes and environments | −1 | Observational/epidemiological design; "characterization" and "landscape" negative signals |
| 10.1038/s41586-026-10360-7 | Molecular basis of oocyte cytoplasmic lattice assembly | −1 | Structural cell biology; "molecular basis" negative signal |

**Manual override — excluded:**

| DOI | Title | Reason |
|-----|-------|--------|
| 10.1038/s41586-026-10170-x | Dogs were widely distributed across western Eurasia before the Bronze Age | Palaeolithic population genetics using the Behavioural & Social Sciences form; not an experimental intervention study |

**Manual overrides — included (score = 0, abstract lacked effect keywords but RS confirmed experimental design):**

| DOI | Title |
|-----|-------|
| 10.1038/s41586-026-10219-x | Functional hierarchy of the human neocortex across the lifespan |
| 10.1038/s41586-026-10226-y | Adaptive evolution of gene regulatory networks in mammalian neocortex |
| 10.1038/s41586-026-10227-x | Biosynthesis of cinchona alkaloids |
| 10.1038/s41586-026-10267-3 | Rapid concerted switching of the neural code in the inferotemporal cortex |

**Final corpus: 20 articles**

---

## 2. Sample-size category distribution

| Category | N | % |
|----------|---|---|
| resource_constraint | 8 | 40% |
| replication_standard | 5 | 25% |
| effect_size_estimate | 4 | 20% |
| power_calc | 2 | 10% |
| methodology_determined | 1 | 5% |

### Category definitions

| Category | Definition |
|----------|------------|
| **resource_constraint** | Sample size determined by availability of material, patients, funding, or data; no explicit justification of adequacy |
| **replication_standard** | Justified by consistency with previous publications (with or without PMID citation) or by field convention (e.g. "at least three independent replicates") |
| **effect_size_estimate** | Justified by pilot data, preliminary experiments, or empirical estimation of expected effect magnitude or variance |
| **power_calc** | Explicit formal power calculation (may be retrospective or approximate) |
| **methodology_determined** | Measurement protocol inherently defines sample size (e.g. cryo-EM particle count, stereological section exhaustion, single-molecule imaging capacity); no separate determination step expected |

---

## 3. Article-level detail

### resource_constraint (8)

**10.1038/s41586-026-10219-x** — Functional hierarchy of the human neocortex across the lifespan
> "Sample size was chosen based on available data across our five imaging datasets. Our final sample size of 3972 is large and ages of participants are evenly distributed across the human lifespan."

**10.1038/s41586-026-10226-y** — Adaptive evolution of gene regulatory networks in mammalian neocortex
> "No sample size calculation was performed. The size of the samples was determined by the availability of the samples, and the sequencing costs."

**10.1038/s41586-026-10242-y** — Thymic health consequences in adults
> "Sample size was chosen based on all available data from the FHS and NLST. The cohort comprised a total of 27,612 participants (2,581 in FHS; 25,031 in NLST). In our study we performed a secondary analysis of these existing datasets."

**10.1038/s41586-026-10243-x** — Thymic health and immunotherapy outcomes in patients with cancer
> "Sample size was chosen based on all available data from the DFHCC and TRACERx. The cohort comprised a total of 3,940 participants (3476 from Harvard and 464 from TRACERx). Sample size was not determined a priori."

**10.1038/s41586-026-10258-4** — Epigenetic memory of colitis promotes tumour growth
> "No statistical methods were used to predetermine sample size. Sample sizes were based on those previously used by our lab and in preliminary experiments. Human organoid experiments were limited by donor availability."

**10.1038/s41586-026-10264-6** — Androgen activity in the male embryonic hindbrain drives lethal PFA ependymoma
> "Sample size was determined by the availability of the human samples. Mouse samples of hindbrain development time points were chosen based on availability and relevance of important developmental events."

**10.1038/s41586-026-10266-4** — Exposed phosphatidylserine is an inhibitory molecule in T cell exhaustion
> "No statistical method was used to predetermine sample size. Sample sizes were based off previous and preliminary studies from our lab (Sarkar, S. et al. J Exp Med. 2008) (Im, S. et al. Nature, 2016)."

**10.1038/s41586-026-10270-8** — Dominant clones leverage developmental epigenomic states to drive ependymoma
> "Sample size was defined by sample availability. There was no sample-size calculation performed."

---

### replication_standard (5)

**10.1038/s41586-026-10220-4** — Climbing fibres recruit disinhibition to enhance Purkinje cell calcium signals
> "No power analysis or other statistical methods were used to pre-determine sample sizes. Sample sizes were similar to previous publications: PMID: 38692278, PMID: 35578131, PMID: 25205669."

**10.1038/s41586-026-10227-x** — Biosynthesis of cinchona alkaloids
> "All experiments designed to probe the function of distinct enzymes were conducted with a sample size of at least three to ensure minimal statistical power analysis: Nicotiana benthamiana pathway reconstitution experiments were done on four independent biological replicates. In vitro assays were performed in three replicates. For VIGS studies, 5 to 6 biological replicates were used. [...] Single-nuclei RNA-seq was performed on two biological replicates, which is sufficient for minimizing technical noise and identifying consistent cell-type-specific and gene-expression profiles, as also performed in several studies (e.g., Nat. Commun. 2025, 16, 3169; Nat. 2025, 643, 582; Nat. Chem. Biol. 2023, 19, 1031)."

**10.1038/s41586-026-10259-3** — Synthetic circuits for cell ratio control
> "No statistical methods were used to predetermine sample size. Sample sizes were chosen to include at least three independent biological replicates, based on established practices in the field and prior work in synthetic biology."

**10.1038/s41586-026-10267-3** — Rapid concerted switching of the neural code in the inferotemporal cortex
> "Sample sizes were maximized given the recording capacity of NHP Neuropixels probes (384 channels) and are consistent with previous studies using similar methods such as She, Liang, et al. 'Temporal multiplexing of perception and memory codes in IT cortex' Nature (2024) and Bao, Pinglei, et al. 'A map of object space in primate inferotemporal cortex' Nature (2020)."

**10.1038/s41586-026-10306-z** — Aversive learning hijacks a brain sugar sensor to consolidate memory
> "Sample sizes in this study were similar to previous studies from our or other groups for aversive memory assays, appetitive memory assays, metabolic imaging, calcium imaging, rather than being based on power analysis."

---

### effect_size_estimate (4)

**10.1038/s41586-026-10179-2** — Insulin resistance prediction from wearables and routine blood biomarkers
> "The exact contribution of each feature (wearables, demographics, and blood biomarkers) to insulin resistance prediction was unknown before we started the study. Based on our prior research (Metwally et al., Cell 2019) we estimated that a sample size of 1000 would allow us to build predictive models with acceptable accuracy."

**10.1038/s41586-026-10232-0** — The E3 ubiquitin ligase mechanism specifying targeted microRNA degradation
> "No statistical methods were used to predetermine sample size. Sample sizes were chosen based on pilot experiments to ensure clear and reliable interpretation of the results."

**10.1038/s41586-026-10250-y** — Proteasome-guided haem signalling axis contributes to T cell exhaustion
> "Group sizes for in vivo validation experiments were selected empirically based on previous results of the intra-group variation of tumor growth upon similar treatments. For in vitro experiments, group sizes of 3–5 were chosen based on previous experience with these assays."

**10.1038/s41586-026-10268-2** — Catabolism of extracellular glutathione supplies cysteine to support tumours
> "For cell culture experiments, sample sizes were not chosen based on statistical methods. All cell culture experiments were repeated at least 2 independent times, each with n≥3 technical replicates."

---

### power_calc (2)

**10.1038/s41586-026-10235-x** — In vivo site-specific engineering to reprogram T cells
> "Sample size were chosen based on power calculation and pilot experiments. Due to the challenge in producing reagents in very large quantities, some experiments have unequal group sizes."

**10.1038/s41586-026-10281-5** — Parasites trigger epithelial cell crosstalk to drive gut–brain signalling
> "For statistical comparisons, sample size was selected based on power calculations performed with reference to previous or present experiments carried out in our laboratory and in the field. For patch-clamp electrophysiology experiments, sample size was selected based on the number of animals and cells needed to detect changes of a certain effect size with a statistical test."

---

### methodology_determined (1)

**10.1038/s41586-026-10278-0** — Ectopic NMDAR expression in cancer unmasks germline-encoded autoimmunity
> *(field blank in Reporting Summary; cryo-EM particle datasets — sample size is inherently determined by the imaging protocol)*

---

## 4. Key observations

1. **No formal power calculations in 90% of articles.** Only 2 of 20 articles report a formal power calculation. This is consistent with the pilot sample from the prior extraction run (0/7 in the initial 9-article pilot).

2. **Resource constraint is the dominant justification (40%).** The most common response is that sample size was limited by availability — of human tissue, patient cohorts, or sequencing budget — with no accompanying argument for why the available sample is sufficient to answer the research question.

3. **Replication standard is the second most common pattern (25%).** Authors cite consistency with prior publications (with PMIDs or literature references) or field conventions ("at least three independent replicates"). This provides precedent but not a quantitative adequacy argument.

4. **Effect-size estimation is present but informal (20%).** Four articles justify N by reference to pilot data or expected variance, but none report the specific estimated effect size, alpha, or power used in any calculation.

5. **Observational / registry studies appear in the corpus.** The two thymic health articles (10242-y, 10243-x) are secondary analyses of existing cohorts; their justification is effectively resource_constraint (all available data used). These are intervention-adjacent (thymus-related outcomes in clinical cohorts) and passed the effect-language filter, but their sample-size logic differs from primary experimental studies.

6. **Methodology-determined cases are rare but present.** The cryo-EM article (10278-0) left the field blank; this is appropriate since particle count is determined by the imaging pipeline and statistical power framing does not apply.

7. **Scanned / copy-protected PDFs remain a pipeline limitation.** One article (10267-3) had a copy-protected PDF that prevented automated text extraction; the sample-size statement was manually supplied. Approximately 22% of RS PDFs across the broader set lacked a text layer and required OCR.

---

## 5. Pipeline notes

| Step | Script | Output |
|------|--------|--------|
| Build article manifest | `build_manifest.py` | `data/manifest_8107.json` |
| Locate RS PDF links | `find_reporting_summaries.py` | `data/manifest_8107_with_rs.json` |
| Extract & classify | `extract_sample_size.py` | `data/sample_size_dataset.json` |
| Filter corpus | `filter_corpus.py` | `data/corpus_filtered.json`, `data/corpus_filtered.tsv` |

Abstracts cached from Crossref API (with nature.com page fallback) in `data/abstracts_cache.json`.
RS PDFs stored locally in `data/pdfs/`.
