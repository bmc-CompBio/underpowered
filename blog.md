# 89% of Experimental Life-Science Papers in Three Months of Nature Used Hypothesis Testing Without Justifying Sample Sizes

*A small automated audit of Nature's own accountability mechanism*

---

Statistical hypothesis testing is the primary tool by which experimental life-science research claims to distinguish signal from noise. Its validity rests on a simple precondition: the study must have been designed with enough statistical power to detect the effect in question. Without that, a p-value is not a measure of evidence — it is a roll of a biased die whose bias nobody bothered to calculate. The consequences are well-documented: inflated effect sizes, irreproducible findings, wasted resources, and, in translational research, failed clinical trials predicated on effects that were never as large as the underpowered discovery study suggested.

This is not a niche methodological concern. It is arguably the central validity problem of experimental biology. And yet it persists, visibly, in the pages of the highest-impact journals.

In 2023, Nature Portfolio updated its Reporting Summary — the structured disclosure form authors must complete alongside every research paper. One of the questions asks authors to explain how they determined their sample size.

It is, in principle, a powerful accountability tool. Unlike a methods section buried on page 12, the Reporting Summary is a structured form with dedicated fields. If you want to know how a study justified its n, you don't have to read the paper. You just open the PDF.

I wondered: what do three months of Nature life-science papers actually say when you ask them that question?

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

This is not surprising. Similar audits going back to Button et al. (2013) have repeatedly found low power calculation rates in biomedical research. But those were retrospective reviews of published literature. Here, I am reading the authors' own prospective disclosures, in a mandatory structured form, in what is widely considered the world's most prestigious scientific journal.

---

## Finding 2: 100% of experimental papers without a power calculation used hypothesis testing anyway

Having established that 89% of articles lacked a formal power calculation, I downloaded the full-text PDFs and scanned for null-hypothesis statistical testing (NHST): p-values, t-tests, ANOVAs, Mann-Whitney tests, confidence intervals, FDR correction, and so on.

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

## Discussion

### This is a systemic norm, not a handful of bad actors

This is not a claim that Nature papers are fraudulent, that the findings are wrong, or that the researchers involved are bad scientists. Most of these are excellent papers from accomplished groups. The statistical practices documented here are entirely normal — they are what the field does, what reviewers expect, and what editors accept.

That is precisely the problem.

Nature's Reporting Summary was introduced partly to make these practices visible. It worked — I could run this audit automatically because the data are right there in a structured field. The uncomfortable finding is what that visibility reveals.

### The deeper problem: NHST is the wrong tool for most of what basic life-science research actually does

There is a more fundamental issue that the power-calculation debate tends to obscure.

Most experimental life-science research published in Nature is not, in any strict sense, confirmatory. It is exploratory. A researcher identifies a gene, a pathway, a cell type, a behaviour — something previously unknown or poorly characterised — and asks: what does it do? What happens if I knock it out, overexpress it, perturb it? The experimental system is novel. The effect sizes are unknown. There is no prior quantitative hypothesis to power against, because the experiment is designed to *discover* the hypothesis, not test a pre-specified one.

Null-hypothesis significance testing was developed for a different context entirely: confirmatory trials with a pre-specified primary endpoint, a pre-registered hypothesis, and a sample size calculated to achieve a defined probability of detecting a clinically meaningful effect. It is a tool for controlled decision-making under uncertainty — pharmaceutical trials, agricultural yield experiments, quality control. Transplanted into exploratory biological research, it does something quite different: it converts the noise of any sufficiently small-n experiment into an apparent signal, selects for results that clear an arbitrary threshold, and then presents those results as if the threshold meant something.

The field has largely adopted the language and ritual of confirmatory testing — p-values, significance thresholds, rejection of null hypotheses — while conducting research that is structurally exploratory. The result is a systematic mismatch between the epistemological claims being made ("we demonstrate that X causes Y") and the evidential basis for making them.

### What worries me most

The data presented here would be less troubling if researchers understood this mismatch and communicated their findings accordingly — as preliminary observations, as hypothesis-generating results requiring replication and follow-up. What I suspect, and what the ubiquity of these practices suggests, is something different: that many researchers genuinely believe that a p-value below 0.05, obtained from an experiment with three biological replicates chosen because that is what the field does, constitutes robust evidence for their conclusion.

This belief is not irrational given how the field trains its members, how reviewers respond to manuscripts, and how journals structure their requirements. It is the natural product of a culture in which statistical testing is performed as a ritual of legitimacy rather than as a tool of inference. The ritual is so deeply embedded that questioning it can seem like questioning science itself.

But the consequences are real. The replication crisis in psychology has been extensively documented; the equivalent crisis in cell and molecular biology is quieter but arguably more serious, because the experiments are more expensive, the model systems more complex, and the translational stakes higher. Treatments that failed in clinical trials because the target biology was established by underpowered mouse experiments are not an abstract possibility. They are a recurring pattern.

None of this is fixed by requiring a power calculation box to be checked on a Reporting Summary form. The fix requires a genuine shift in how the field reasons about evidence — distinguishing exploratory from confirmatory work, reporting effect sizes with uncertainty rather than binary significance calls, and being honest about what a single small experiment in a single model system can and cannot establish.

That shift is possible. Several journals and funders are already pushing in this direction. But it requires acknowledging, first, that there is a problem — which the data above make difficult to deny.

---

## What would better look like?

Three things, none of them radical:

1. **Require power calculations, not just a disclosure field.** If the answer to "how did you determine your sample size?" is "we used the same n as previous studies," the reviewer should ask: and how was *that* n determined?

2. **Treat non-significant results as inconclusive by default** unless accompanied by a prospective power calculation or an equivalence test with prespecified margins. The rhetorical move of "we found no significant difference, therefore there is no difference" should not pass peer review unchallenged.

3. **Separate the inference from the test.** Reporting p-values alongside effect sizes and confidence intervals shifts the focus from binary significance to magnitude of evidence. Many journals now require this; Nature's own statistical guidelines recommend it. The gap between the guidelines and the papers documented here suggests the recommendation alone is not sufficient.

---

## Code and data

The full pipeline — Crossref query, PDF download, Reporting Summary extraction, classification, full-text analysis — is available at https://github.com/bmc-CompBio/underpowered. The classified dataset is in `data/multi_issue_dataset_filtered.json`. You can rerun the entire analysis or extend it to additional issues with a single script call.

I intend to extend this to a full year of Nature and potentially additional journals. If you have thoughts or want to collaborate, get in touch.

---

*Tobias Straub. Pilot study: 83 experimental papers, Nature issues 8096–8107 (January–March 2026). Full methods in the repository.*
