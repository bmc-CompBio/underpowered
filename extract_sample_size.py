"""
Step 4 + 5: Download Reporting Summary PDFs and extract the sample-size field.

The Reporting Summary PDF has this structure in the Statistics section:
  Q: "Describe how sample size was determined..."
  A: [free-text author response]

Extraction strategy:
  1. Download the PDF from static-content.springer.com
  2. Extract all text with pdfplumber
  3. Locate the sample-size question by proximity search
  4. Extract the text that follows it (until the next question)
  5. Classify the answer into one of 7 categories

Classification categories:
  power_calc           - formal a priori power calculation
  effect_size_estimate - quantitative estimate from pilot/literature, no formal calc
  replication_standard - appeal to field convention / replication of prior study
  resource_constraint  - sample size limited by availability / cost
  no_justification     - n stated but no reasoning given
  na_or_blank          - field empty, N/A, or not applicable
  ambiguous            - text present but insufficient to classify
"""

import argparse, json, re, time
from pathlib import Path
import requests
import pdfplumber

# OCR fallback for scanned PDFs (imported lazily so script still works without them)
def _ocr_pdf(pdf_path: Path) -> str | None:
    try:
        from pdf2image import convert_from_path
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"
        images = convert_from_path(str(pdf_path), dpi=200)
        pages = [pytesseract.image_to_string(img) for img in images]
        return "\n".join(pages)
    except ImportError:
        return None
    except Exception as e:
        print(f"    [OCR error] {e}")
        return None

DATA = Path("data")
PDFS = Path("data/pdfs")
PDFS.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    ),
}

# ------------------------------------------------------------------
# PDF download
# ------------------------------------------------------------------

def download_pdf(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"    [cached] {dest.name}")
        return True
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if resp.status_code == 200 and b"%PDF" in resp.content[:10]:
            dest.write_bytes(resp.content)
            print(f"    [downloaded {len(resp.content)//1024} kB] {dest.name}")
            return True
        else:
            print(f"    [FAIL HTTP {resp.status_code}] {url[:80]}")
            return False
    except Exception as e:
        print(f"    [ERROR] {e}")
        return False

# ------------------------------------------------------------------
# PDF text extraction and field parsing
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# RS PDF structure (Nature Portfolio, April 2023 template)
# ------------------------------------------------------------------
# The Reporting Summary has three possible study-design sections:
#   "Life sciences study design"
#   "Behavioural & social sciences study design"
#   "Ecological, evolutionary & environmental sciences study design"
#
# In each, the sample-size field is a fixed label followed by author text:
#   "Sample size  <author answer>"
#   (or "Sampling strategy  <answer>" in the ecological form)
#
# The next field label ends the answer.

# Patterns that mark the START of a study-design section
STUDY_DESIGN_SECTION_RE = re.compile(
    r"(Life\s+sciences\s+study\s+design|"
    r"Behavioural\s+&\s+social\s+sciences\s+study\s+design|"
    r"Ecological,\s+evolutionary\s+&\s+environmental\s+sciences\s+study\s+design)",
    re.I,
)

# The sample-size field label within the study design section
SAMPLE_SIZE_LABEL_RE = re.compile(
    r"\bSample\s+size\b",
    re.I,
)

# Labels that mark the NEXT field (i.e., end of sample-size answer)
NEXT_FIELD_LABEL_RE = re.compile(
    r"\n(Data\s+exclusions?|Replication|Randomization|Blinding|"
    r"Reporting\s+for\s+specific|Materials\s+&|Field-specific|"
    r"Sampling\s+strategy|Data\s+collection|Timing|Research\s+sample)",
    re.I,
)

def extract_text_from_pdf(pdf_path: Path) -> str | None:
    try:
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
        return "\n".join(pages)
    except Exception as e:
        print(f"    [PDF parse error] {e}")
        return None

def find_sample_size_field(text: str) -> dict:
    """
    Locate the sample-size answer in the RS PDF text.

    Strategy:
      1. Find the study-design section (Life sciences / Behavioural / Ecological).
      2. Within that section, find the 'Sample size' field label.
      3. Extract text from after the label until the next field label.

    Returns dict with 'question_found', 'raw_answer', 'form_type', 'context'.
    """
    if not text:
        return {"question_found": False, "raw_answer": None, "form_type": None, "context": None}

    # Normalise no-space text (font-encoding artefact: "Samplesize" → "Sample size")
    # Detect by checking word-boundary density
    words = text.split()
    avg_len = sum(len(w) for w in words) / max(len(words), 1)
    if avg_len > 15:  # typical prose has avg ~5; no-space text has avg >15
        # Insert spaces before capital letters and known field names
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        text = re.sub(r"(Sample)(size)", r"\1 \2", text, flags=re.I)
        text = re.sub(r"(Data)(exclusions?)", r"\1 \2", text, flags=re.I)
        text = re.sub(r"(study)(design)", r"\1 \2", text, flags=re.I)
        text = re.sub(r"(sciences?)(study)", r"\1 \2", text, flags=re.I)

    # Step 1: locate the study-design section
    m_section = STUDY_DESIGN_SECTION_RE.search(text)
    # Fallback for compact/no-space font encoding
    if not m_section:
        m_section = re.search(
            r"(Life.{0,5}sciences.{0,5}study.{0,5}design|"
            r"Behavioural.{0,10}social.{0,10}sciences.{0,10}study.{0,5}design|"
            r"Ecological.{0,40}study.{0,5}design)",
            text, re.I,
        )
    if not m_section:
        section_text = text
        form_type = "unknown"
    else:
        form_type = m_section.group(1)
        section_text = text[m_section.start():]

    # Step 2: find "Sample size" label within the section
    # For ecological/evolutionary forms, fall back to "Sampling strategy"
    m_label = SAMPLE_SIZE_LABEL_RE.search(section_text)
    if not m_label:
        # Try compact encoding: "Samplesize" or "Sample size" with loose spacing
        m_label = re.search(r"\bSample.{0,2}size\b", section_text, re.I)
    if not m_label:
        # Try "Sampling strategy" for ecological/evolutionary forms
        m_label = re.search(r"\bSampling.{0,2}strategy\b", section_text, re.I)
    if not m_label:
        return {"question_found": False, "raw_answer": None, "form_type": form_type, "context": None}

    answer_start = m_label.end()
    # The answer follows immediately (possibly after a space / newline)
    answer_chunk = section_text[answer_start : answer_start + 1200].lstrip()

    # Step 3: trim at the next field label
    m_next = NEXT_FIELD_LABEL_RE.search(answer_chunk)
    if m_next:
        answer_chunk = answer_chunk[: m_next.start()]

    # Clean up whitespace
    raw = re.sub(r"\s+", " ", answer_chunk).strip()

    # Reject answers that are just the next field label, or that begin with
    # exclusion criteria (Data exclusions OCR ordering artefact)
    if re.match(r"^(data\s+exclusions?|replication|randomization|blinding)", raw, re.I):
        raw = None
    # Reject if answer looks like it describes exclusion criteria rather than sample size
    if raw and re.match(r"^For\s+associations\s+in\s+the\s+\w+\s+\w+\s+\w+\s+data\s+set,\s+individuals\s+were\s+excluded", raw, re.I):
        raw = None

    if not raw or len(raw) < 5:
        # Widen context to 600 chars so methodology signals (cryo-EM in nearby fields) are visible
        return {
            "question_found": True,
            "raw_answer": None,
            "form_type": form_type,
            "context": section_text[m_label.start() : m_label.start()+600],
        }

    return {
        "question_found": True,
        "raw_answer": raw,
        "form_type": form_type,
        "context": section_text[m_label.start() : m_label.start()+200],
    }

# ------------------------------------------------------------------
# Classification
# ------------------------------------------------------------------

CATEGORY_RULES = [
    ("na_or_blank", re.compile(
        r"^(n/?a|not\s+applicable|na|none|n/a|not\s+relevant|no\s+statistical)$",
        re.I,
    )),
    ("power_calc", re.compile(
        # Require affirmative power calc — not a negation like "no power analysis was used"
        r"(?<!no\s)(?<!not\s)(?<!without\s)(?<!no\s)(power\s+anal\w*\s+(was\s+)?perform|"
        r"power\s+calc|g\*power|g-power|"
        r"power\s+of\s+0\.\d|type\s+[i1]\s+error|type\s+[ii2]\s+error|"
        r"\d+\s*%\s*power|\bpow\s*=|"
        r"(performed|conducted|ran|used)\s+a\s+power|"
        r"a\s+priori\s+power|sample\s+size\s+(was\s+)?calculat)",
        re.I,
    )),
    ("effect_size_estimate", re.compile(
        r"based\s+on\s+(previous|prior|pilot|preliminary|our\s+(earlier|prior|previous)|earlier)\s+\w+(search|earch|study|experiment|data|result)|"
        r"based\s+on\s+our\s+prior\s+research|"
        r"based\s+(off|on)\s+(previous|prior|pilot|preliminary)\s+(studies|experiments|results|work|research|data)|"
        r"based\s+(our\s+\w+\s+\w+\s+)?on\s+(a\s+combination\s+of\s+)?previous\s+(experience|work)|"
        r"based\s+on\s+our\s+(experience|knowledge)\s+with\s+(variability|the|these|similar)|"
        r"previous\s+experience\s+with\s+(these|similar|comparable|the)|"
        r"(because|since)\s+(pilot|preliminary)\s+stud|"
        r"pilot\s+stud(y|ies)\s+(demonstrated|showed|indicated|revealed|suggest)|"
        r"effect\s+size|cohen'?s|pearson'?s\s+r|variance\s+from|"
        r"standard\s+deviation\s+from|literature\s+(value|report|suggest)|"
        r"estimate[d]?\s+(from|based)|calculated\s+from\s+(prior|previous|pilot)|"
        r"selected\s+empirically\s+based\s+on\s+previous|"
        r"intra-group\s+variation|group\s+sizes.*selected.*empirically|"
        r"repeated\s+at\s+least\s+\d+\s+times\s+to\s+ensure",
        re.I,
    )),
    ("replication_standard", re.compile(
        r"similar\s+to\s+(previous|prior|published|earlier|past)|"
        r"consistent\s+with\s+(previous|prior|published|standard|convention)|"
        r"as\s+(previously|prior)\s+(reported|described|used|performed|published)|"
        r"standard\s+(in\s+the\s+field|practice|protocol)|established\s+practices?\s+in\s+the\s+field|"
        r"commonly\s+(used|accepted\s+standards?)|typically\s+used|routinely\s+used|"
        r"(replicate|replicated)\s+(previous|prior|published)|"
        r"n\s*=\s*\d+\s+(is|are|were)\s+(standard|typical|conventional)|"
        r"PMID\s*:\s*\d{5,}|"
        r"at\s+least\s+(\d+|two|three|four|five|six)\s+to\s+ensure\s+(minimal|adequate|sufficient)\s+statistical|"
        r"(minimum|at\s+least)\s+(of\s+)?(\d+|two|three|four|five|six)\s+(or\s+more\s+)?(independent\s+)?(biological\s+)?(replicates?|samples?|independent)|"
        r"minimal\s+(number|amount)\s+(needed|required)\s+(to|for)\s+(perform|conduct|calculate)\s+statistical|"
        r"to\s+ensure\s+(minimal|adequate|sufficient)\s+statistical|"
        r"prior\s+literature\s+\(doi|"
        r"based\s+on\s+(those|sizes|numbers)\s+(used|published)\s+in\s+(previous|prior|published|comparable)|"
        r"based\s+on\s+comparable\s+(experiments?|studies)\s+(previously|prior)\s+(published|used)|"
        r"(study|experiment)\s+sizes?\s+were\s+based\s+on\s+comparable|"
        r"multiple\s+(different\s+)?technical\s+repeat",
        re.I,
    )),
    ("resource_constraint", re.compile(
        # Also catches "all individuals/samples which/that were sampled"
        r"all\s+(individuals?|specimens?|samples?|cases?|subjects?)\s+(which|that|who)\s+"
        r"(possess|had|provid|contain|were\s+available)|"
        r"based\s+on\s+all\s+available\s+data\s+from|"
        r"not\s+determined\s+by\s+calculation\s+as\s+this\s+was\s+not\s+a\s+prospective",
        re.I,
    )),
    ("resource_constraint", re.compile(
        r"(limited|constrained|determined)\s+by\s+(the\s+)?(availab|budget|cost|number|supply)|"
        r"all\s+available\s+(animals|mice|patients|samples|subjects|donors)|"
        r"maximum\s+(number|available|possible)|cohort\s+size|registry|"
        r"practical\s+(constraint|limitation)|feasibility|"
        r"(could|were|was)\s+not\s+(perform|possible|done)\s+a?\s+power|"
        r"availability\s+of\s+(the\s+)?(\w+\s+)?(samples|animals|data|patients|adequate)|"
        r"(sequencing\s+cost|budget\s+constraint|sample\s+availab)|"
        r"based\s+on\s+available\s+(\w+\s+)?(data|samples|material)|"
        r"restricted\s+by|constrained\s+by|"
        r"maximum\s+possible\s+based\s+on|"
        r"chosen\s+based\s+on\s+(the\s+)?available|"
        r"limited\s+by\s+donor|donor\s+participation|sample\s+availability|"
        r"able\s+to\s+(collect|process|obtain|dissect|examine|produce|generat)|"
        r"vast\s+majority\s+of\s+(the\s+)?(participants|subjects|patients|samples)|"
        r"(maximize|maximise)\s+(the\s+)?sample\s+size",
        re.I,
    )),
    ("methodology_determined", re.compile(
        # Sample size is inherently defined by the measurement technique or study design.
        # Signals: stereology (with or without spaces), cryo-EM, single-molecule,
        # serial crystallography (TR-SFX / SFX), and data-quality thresholds (CC-half).
        r"unbiased.{0,3}stereolog|systematic.{0,3}random.{0,3}sampl|"
        r"isotropic.{0,3}uniform.{0,3}random|cavalieri|optical.{0,3}fractionator|"
        r"cryo.?em|cryo.?et|cryo.?electron|"
        r"tr.?sfx|serial\s+(femtosecond|crystallog)|sfx\s+experiment|"
        r"cc.?half\s+(criterion|threshold|cutoff|value)|"
        r"dataset\s+size\s+is\s+primarily|"
        r"individual\s+molecules?\s+.{0,30}(technique|imag|fret|observed)|"
        r"(number\s+of\s+(particles?|micrographs?|molecules?))\s+(is\s+)?(primarily\s+)?determin",
        re.I,
    )),
    ("no_justification", re.compile(
        r"^n\s*=\s*\d|"
        r"sample\s+sizes?\s+(are|were|is)\s+(n\s*=|\d)|"
        r"^\d+\s+(animals|mice|rats|subjects|patients|samples|individuals)",
        re.I,
    )),
]

_METHODOLOGY_RE = re.compile(
    # Stereology — with and without spaces (no-space font encoding)
    r"unbiased.{0,3}stereolog|systematic.{0,3}random.{0,3}sampl|"
    r"isotropic.{0,3}uniform.{0,3}random|cavalieri|optical.{0,3}fractionator|"
    # cryo-EM / structural biology
    r"cryo.?em|cryo.?et|cryo.?electron|"
    # serial crystallography
    r"tr.?sfx|serial\s+(femtosecond|crystallog)|sfx\s+experiment|"
    r"cc.?half\s+(criterion|threshold|cutoff|value)|"
    r"dataset\s+size\s+is\s+primarily|"
    r"(number\s+of\s+(particles?|micrographs?|molecules?))\s+(is\s+)?(primarily\s+)?determin|"
    # single-molecule
    r"individual\s+molecules?\s+.{0,30}(technique|imag|fret|observed)",
    re.I,
)

def classify_statement(raw_answer: str | None, context: str | None = None) -> str:
    # Blank field: check if context indicates a methodology-determined study
    if not raw_answer:
        if context and _METHODOLOGY_RE.search(context):
            return "methodology_determined"
        return "na_or_blank"
    txt = raw_answer.strip()
    if len(txt) < 10:
        return "na_or_blank"
    for category, pattern in CATEGORY_RULES:
        if pattern.search(txt):
            return category
    return "ambiguous"

# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", type=int, default=8107)
    args = parser.parse_args()
    issue = args.issue

    manifest = json.loads((DATA / f"manifest_{issue}_with_rs.json").read_text())
    articles = manifest["articles"]

    life_with_rs = [
        a for a in articles
        if a.get("subject_classification") == "life_science"
        and a.get("reporting_summary_url")
        and "static-content.springer.com" in str(a.get("reporting_summary_url", ""))
    ]
    print(f"Life-science articles with direct RS PDF URL: {len(life_with_rs)}")
    print(f"Running full extraction on all {len(life_with_rs)}...\n")

    # Load any prior results to allow resuming.
    # For issue 8107, also try the legacy filename as fallback.
    prior_path = DATA / f"dataset_{issue}.json"
    if not prior_path.exists() and issue == 8107:
        prior_path = DATA / "sample_size_dataset.json"
    prior_results = {}
    if prior_path.exists():
        prior_data = json.loads(prior_path.read_text())
        for rec in prior_data.get("records", []):
            conf = rec.get("extraction_confidence")
            cat = rec.get("sample_size_category")
            # Re-process: low/medium confidence, any remaining ambiguous,
            # and records missing rs_form_type (added in a later schema revision)
            if (conf not in (None, "failed", "needs_ocr", "low", "medium")
                    and cat != "ambiguous"
                    and rec.get("rs_form_type") is not None):
                prior_results[rec["doi"]] = rec
        print(f"Resuming: {len(prior_results)} already extracted from prior run\n")

    results = []
    for i, art in enumerate(life_with_rs):
        # Use cached result if available and not a scanned PDF
        if art["doi"] in prior_results:
            print(f"[{i+1:2d}/{len(life_with_rs)}] [cached] {art['doi']}")
            results.append({**art, **prior_results[art["doi"]]})
            continue
        doi = art["doi"]
        title = (art.get("title") or "")[:65]
        rs_url = art["reporting_summary_url"]
        suffix = doi.split("10.1038/")[-1].replace("/", "_")
        pdf_path = PDFS / f"{suffix}_RS.pdf"

        print(f"[{i+1:2d}/{len(life_with_rs)}] {doi}")
        print(f"       {title}")

        # Download
        ok = download_pdf(rs_url, pdf_path)
        time.sleep(1.1)

        if not ok:
            results.append({**art,
                "pdf_accessible": False, "pdf_searchable": False,
                "needs_ocr": False, "question_found": False,
                "sample_size_raw": None, "sample_size_category": "na_or_blank",
                "extraction_confidence": "failed",
            })
            continue

        # Extract text
        text = extract_text_from_pdf(pdf_path)
        # Treat near-empty extractions (< 100 real chars) as scanned
        if text and len(text.strip()) < 100:
            text = None
        if not text:
            needs_ocr = (pdf_path.stat().st_size > 100_000)
            if needs_ocr:
                print(f"    [scanned PDF — attempting OCR]")
                text = _ocr_pdf(pdf_path)
                if text:
                    print(f"    [OCR succeeded: {len(text)} chars]")
                else:
                    print(f"    [OCR unavailable or failed]")
            if not text:
                results.append({**art,
                    "pdf_accessible": True, "pdf_searchable": False,
                    "needs_ocr": needs_ocr, "question_found": False,
                    "sample_size_raw": None, "sample_size_category": "na_or_blank",
                    "extraction_confidence": "needs_ocr" if needs_ocr else "failed",
                })
                continue

        # Find sample-size field
        field = find_sample_size_field(text)
        raw = field.get("raw_answer")
        category = classify_statement(raw, context=field.get("context"))

        print(f"       Form: {field.get('form_type','?')[:40]} | Q found: {field['question_found']} | category: {category}")
        if raw:
            print(f"       Answer: {raw[:140]}")
        else:
            print(f"       Answer: [empty/not found]")
            if field.get("context"):
                print(f"       Context: {field['context'][:120]}")
        print()

        results.append({**art,
            "pdf_accessible": True,
            "pdf_searchable": bool(text),
            "question_found": field["question_found"],
            "form_type": field.get("form_type"),
            "sample_size_raw": raw,
            "sample_size_category": category,
            "extraction_confidence": (
                "high" if (field["question_found"] and raw and len(raw) > 20)
                else "medium" if field["question_found"]
                else "low"
            ),
        })

    # ------------------------------------------------------------------
    # Summary table
    # ------------------------------------------------------------------
    from collections import Counter
    cats = Counter(r["sample_size_category"] for r in results)
    conf = Counter(r["extraction_confidence"] for r in results)

    print("=" * 60)
    print("EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Articles processed: {len(results)}")
    print(f"PDF accessible:     {sum(1 for r in results if r.get('pdf_accessible'))}")
    print(f"Text extracted:     {sum(1 for r in results if r.get('pdf_searchable'))}")
    print(f"Q found:            {sum(1 for r in results if r.get('question_found'))}")
    print(f"\nCategory distribution: {dict(cats)}")
    print(f"Confidence distribution: {dict(conf)}")
    print()

    print(f"{'DOI':<45} {'Cat':<22} {'Conf':<8} {'Answer (truncated)'}")
    print("-" * 120)
    for r in results:
        doi = r["doi"][:43]
        cat = r["sample_size_category"][:20]
        conf_ = r.get("extraction_confidence", "?")[:6]
        ans = (r.get("sample_size_raw") or "")[:50]
        print(f"{doi:<45} {cat:<22} {conf_:<8} {ans}")

    # ------------------------------------------------------------------
    # Save dataset
    # ------------------------------------------------------------------
    # Build final dataset schema
    dataset = {
        "schema_version": "1.0",
        "corpus_version": manifest.get("corpus_version", f"nature_i{issue}"),
        "source_issue": manifest["source_issue"],
        "total_articles_in_issue": manifest["total_articles"],
        "life_science_candidates": len(
            [a for a in articles if a.get("subject_classification") == "life_science"]
        ),
        "articles_with_rs_url": len(life_with_rs),
        "articles_extracted": len(results),
        "classification_categories": {
            "power_calc": "Formal a priori power calculation (α, β, effect size specified)",
            "effect_size_estimate": "Quantitative estimate from pilot/literature, no formal calc",
            "replication_standard": "Appeal to field convention or replication of prior study",
            "resource_constraint": "Sample size limited by availability, budget, or cohort size",
            "methodology_determined": "Sample size inherently defined by measurement technique or study design (stereology, cryo-EM, single-molecule imaging, complete-specimen census); no separate determination step expected",
            "no_justification": "n stated but no reasoning provided",
            "na_or_blank": "Field empty, N/A, or not applicable",
            "ambiguous": "Text present but insufficient to classify",
        },
        "records": [
            {
                "doi": r["doi"],
                "title": r.get("title"),
                "volume": r.get("volume"),
                "issue": r.get("issue"),
                "published_date": r.get("published_date"),
                "subject_classification": r.get("subject_classification"),
                "reporting_summary_url": r.get("reporting_summary_url"),
                "pdf_accessible": r.get("pdf_accessible"),
                "pdf_searchable": r.get("pdf_searchable"),
                "question_found": r.get("question_found"),
                "rs_form_type": r.get("form_type") or r.get("rs_form_type"),
                "sample_size_raw": r.get("sample_size_raw"),
                "sample_size_category": r.get("sample_size_category"),
                "extraction_confidence": r.get("extraction_confidence"),
            }
            for r in results
        ],
    }

    out_path = DATA / f"dataset_{issue}.json"
    out_path.write_text(json.dumps(dataset, indent=2))
    print(f"\n[OK] Written {out_path}")

    # Also save as TSV for easy inspection
    tsv_path = DATA / f"dataset_{issue}.tsv"
    with open(tsv_path, "w") as f:
        cols = ["doi", "title", "issue", "subject_classification",
                "sample_size_category", "extraction_confidence", "sample_size_raw"]
        f.write("\t".join(cols) + "\n")
        for rec in dataset["records"]:
            row = [str(rec.get(c) or "").replace("\t", " ").replace("\n", " ")[:200]
                   for c in cols]
            f.write("\t".join(row) + "\n")
    print(f"[OK] Written {tsv_path}")

if __name__ == "__main__":
    main()
