"""
Orchestrate the full pipeline for issues 8096–8106.
Issue 8107 is already complete; this script skips it.

Steps per issue:
  1. find_reporting_summaries.py --issue N   (fetch RS PDF links, ~30–40 s per issue)
  2. extract_sample_size.py --issue N        (download + classify PDFs)

Run:
  python run_multi_issue.py
  python run_multi_issue.py --start 8100     # resume from a specific issue
  python run_multi_issue.py --issues 8096 8097 8098   # specific issues only
"""

import argparse, subprocess, sys, time
from pathlib import Path

DATA = Path("data")

ISSUES_NEW = list(range(8096, 8107))  # 8096..8106; 8107 already done


def run(cmd: list[str], label: str):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"[ERROR] {label} exited with code {result.returncode}")
        sys.exit(result.returncode)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=None,
                        help="Resume from this issue number (skip earlier ones)")
    parser.add_argument("--issues", type=int, nargs="+", default=None,
                        help="Process only these specific issue numbers")
    args = parser.parse_args()

    issues = args.issues or ISSUES_NEW
    if args.start:
        issues = [i for i in issues if i >= args.start]

    print(f"Processing {len(issues)} issue(s): {issues}")

    for issue in issues:
        manifest_path = DATA / f"manifest_{issue}.json"
        if not manifest_path.exists():
            print(f"\n[!] manifest_{issue}.json not found — run build_manifest_multi.py first")
            sys.exit(1)

        rs_done = DATA / f"manifest_{issue}_with_rs.json"
        if rs_done.exists():
            print(f"\n[Issue {issue}] RS manifest already exists — skipping find_reporting_summaries")
        else:
            run(
                [sys.executable, "find_reporting_summaries.py", "--issue", str(issue)],
                f"Issue {issue} — find_reporting_summaries"
            )
            time.sleep(2)  # brief pause between issues

        dataset_done = DATA / f"dataset_{issue}.json"
        if dataset_done.exists():
            # Re-run anyway to pick up any new classifications or low-confidence re-extractions
            print(f"\n[Issue {issue}] dataset_{issue}.json exists — re-running extract to check for updates")

        run(
            [sys.executable, "extract_sample_size.py", "--issue", str(issue)],
            f"Issue {issue} — extract_sample_size"
        )

    print(f"\n{'='*60}")
    print(f"  All {len(issues)} issues processed.")
    print(f"  Run merge_datasets.py next, then filter_corpus.py --dataset data/multi_issue_dataset.json")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
