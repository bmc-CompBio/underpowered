# Every Experimental Paper in Three Months of Nature Used Hypothesis Testing Without Justifying Sample Sizes

*A small automated audit of Nature's own accountability mechanism*

---

In 2023, Nature Portfolio updated its Reporting Summary — the structured disclosure form authors must complete alongside every research paper. One of the questions asks authors to explain how they determined their sample size.

It is, in principle, a powerful accountability tool. Unlike a methods section buried on page 12, the Reporting Summary is a structured form with dedicated fields. If you want to know how a study justified its n, you don't have to read the paper. You just open the PDF.

I wondered: what do three months of Nature actually say when you ask them that question?

---

## What I did

I built an automated pipeline that downloads Nature Reporting Summary PDFs and extracts the sample-size field for every experimental life-science paper published across 12 consecutive issues (January to March 2026, issues 8096–8107). Articles using purely structural, observational, or ecological study designs — where the conventional NHST sample-size logic doesn't apply — were excluded. This left **83 experimental articles**.

I then classified the sample-size justification in each Reporting Summary into one of seven categories, resolved ambiguous cases by manual review, and verified the full dataset by hand. The pipeline and raw data are publicly available.

---

## Finding 1: 11% had a power calculation

A formal a priori power calculation — specifying α, β, and an expected effect size before data collection — appeared in **9 of 83 articles (11%)**.

The remaining 89% broke down as follows:

| Justification | n | % |
|---|---|---|
| "We used the same n as previous studies in the field" | 27 | 33% |
| "We used as many samples as we could get" | 23 | 28% |
| "Based on pilot data / literature estimates" (no formal calc) | 13 | 16% |
| Field empty or N/A | 6 | 7% |
| Technique-determined (stereology, cryo-EM, etc.) — legitimate | 3 | 4% |
| n stated with no explanation whatsoever | 2 | 2% |

The two most common justifications — convention-copying and resource-limitation — are not sample-size *determinations*. They are descriptions of how many samples happened to be available or how many the field traditionally uses. Neither tells you whether the study had adequate power to detect the effect it was looking for.

This is not surprising. Similar audits going back to Button et al. (2013) have repeatedly found low power calculation rates in biomedical research. But those were retrospective reviews of published literature. Here, we are reading the authors' own prospective disclosures, in a mandatory structured form, in what is widely considered the world's most prestigious scientific journal.

---

## Finding 2: 100% of experimental papers without a power calculation used hypothesis testing anyway

Having established that 89% of articles lacked a formal power calculation, we downloaded the full-text PDFs and scanned for null-hypothesis statistical testing (NHST): p-values, t-tests, ANOVAs, Mann-Whitney tests, confidence intervals, FDR correction, and so on.

Among the 69 experimental papers that lacked a power calculation and were not technique-determined:

**69 out of 69 used NHST to draw conclusions.**

Every single one.

This is the core of the problem. A power calculation and a significance test are two sides of the same coin. The power calculation asks: *given the effect I expect, how many samples do I need to reliably detect it?* The significance test then asks: *did I detect it?* Running only the second half — declaring p < 0.05 as confirmation — without having established whether the study was adequately powered is a bit like setting off on a road trip without checking whether you have enough fuel, then declaring you arrived safely because the car didn't stop.

In underpowered studies, the false negative rate is unknown. Worse: published findings tend to be those that cleared the significance threshold, creating a selection effect toward inflated effect sizes. The field of reproducibility research has shown this repeatedly. Yet the practice continues, because NHST is familiar, journals accept it, and nobody required a power calculation beforehand.

---

## Finding 3: 15% used non-significant results as positive evidence

Perhaps the most troubling finding is a specific form of statistical misuse that only makes sense in the context of underpowered studies.

In **11 of 71 articles (15%)**, a non-significant result was used as a positive argument — as evidence that a treatment had no effect, that two groups were equivalent, or that a hypothesis could be ruled out. Representative examples:

- "no significant effect on 2A protein or CVB3 RNA levels, *suggesting that* viral protein functions independently of…"
- "was *not significantly different* from the homozygous suppressor mutations" [used to argue functional equivalence]
- "no significant correlation with MI… *these patterns are consistent with*…"
- "pairwise comparisons are non significant" [cited as a substantive finding about microbial transmission]

The logical problem here is well-established: absence of evidence is not evidence of absence, particularly when you never established how much power you had to detect the effect. If your study was designed to have 40% power to detect the relevant effect size — a common situation, per Button et al. — then a non-significant result means almost nothing. You'd miss a real effect 60% of the time. But the paper treats p > 0.05 as confirmation that nothing is there.

---

## What this is not

This is not a claim that Nature papers are fraudulent, that the findings are wrong, or that the researchers involved are bad scientists. Most of these are excellent papers from accomplished groups. The statistical practices documented here are entirely normal — they are what the field does, what reviewers expect, and what editors accept.

That is precisely the problem. This is not a handful of bad actors. It is a systemic norm.

Nature's Reporting Summary was introduced partly to make these practices visible. It worked — we could run this audit automatically because the data are right there in a structured field. The uncomfortable finding is what that visibility reveals.

---

## What would better look like?

Three things, none of them radical:

1. **Require power calculations, not just a disclosure field.** If the answer to "how did you determine your sample size?" is "we used the same n as previous studies," the reviewer should ask: and how was *that* n determined?

2. **Treat non-significant results as inconclusive by default** unless accompanied by a prospective power calculation or an equivalence test with prespecified margins. The rhetorical move of "we found no significant difference, therefore there is no difference" should not pass peer review unchallenged.

3. **Separate the inference from the test.** Reporting p-values alongside effect sizes and confidence intervals shifts the focus from binary significance to magnitude of evidence. Many journals now require this; Nature's own statistical guidelines recommend it. The gap between the guidelines and the papers documented here suggests the recommendation alone is not sufficient.

---

## Code and data

The full pipeline — Crossref query, PDF download, Reporting Summary extraction, classification, full-text analysis — is available at [GitHub link]. The classified dataset is in `data/multi_issue_dataset_filtered.json`. You can rerun the entire analysis or extend it to additional issues with a single script call.

I intend to extend this to a full year of Nature and potentially additional journals. If you have thoughts or want to collaborate, get in touch.

---

*Tobias Straub. Pilot study: 83 experimental papers, Nature issues 8096–8107 (January–March 2026). Full methods in the repository.*
