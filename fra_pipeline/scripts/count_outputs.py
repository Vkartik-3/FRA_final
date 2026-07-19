#!/usr/bin/env python3
"""
Count and Validate Pipeline Outputs

Prints:
  - Number of plan_N.json files in the plan_assignments directory
  - Number of fra_results_N.csv files in the fra directory
  - Row counts for combined baseline and FRA CSVs
  - Global duplicate summary from chain_diagnostics (if present)
  - Missing plan IDs (gaps in the expected range)

Usage:
    python count_outputs.py                              # uses defaults
    python count_outputs.py \
        --plans-dir outputs/plan_assignments \
        --fra-dir   outputs/fra \
        --baseline-csv outputs/analysis/baseline_ensemble_combined.csv \
        --fra-csv      outputs/analysis/fra_ensemble_combined.csv \
        --expected  10000
"""

import argparse
import json
from pathlib import Path

import pandas as pd


def count_outputs(plans_dir: Path, fra_dir: Path,
                  baseline_csv: Path, fra_csv: Path,
                  expected: int) -> dict:

    print("=" * 60)
    print("OUTPUT COUNT VALIDATION")
    print("=" * 60)

    results = {}

    # ── Plan JSON files ───────────────────────────────────────────────────────
    plan_files = sorted(plans_dir.glob("plan_*.json"))
    plan_ids   = []
    for f in plan_files:
        try:
            plan_ids.append(int(f.stem.split("_")[1]))
        except (IndexError, ValueError):
            pass

    plan_ids.sort()
    n_plans = len(plan_ids)
    print(f"\n[PLAN JSON FILES]  {plans_dir}")
    print(f"  Found: {n_plans:,}  plan_N.json files")
    if expected and n_plans < expected:
        print(f"  ⚠  Expected {expected:,}, missing {expected - n_plans:,} plans")

    if plan_ids:
        full_range   = set(range(plan_ids[0], plan_ids[-1] + 1))
        missing_ids  = sorted(full_range - set(plan_ids))
        print(f"  Range: {plan_ids[0]} – {plan_ids[-1]}")
        if missing_ids:
            print(f"  ⚠  Missing plan IDs ({len(missing_ids)}): {missing_ids[:20]}"
                  + (" ..." if len(missing_ids) > 20 else ""))
        else:
            print(f"  ✓  No gaps in plan ID sequence")
    results["plan_json_count"] = n_plans

    # ── FRA result CSV files ──────────────────────────────────────────────────
    fra_files = sorted(fra_dir.glob("fra_results_*.csv"))
    fra_ids   = []
    for f in fra_files:
        try:
            fra_ids.append(int(f.stem.split("_")[-1]))
        except (IndexError, ValueError):
            pass

    fra_ids.sort()
    n_fra = len(fra_ids)
    print(f"\n[FRA RESULT FILES]  {fra_dir}")
    print(f"  Found: {n_fra:,}  fra_results_N.csv files")
    if plan_ids and fra_ids:
        plan_set = set(plan_ids)
        fra_set  = set(fra_ids)
        not_in_fra = sorted(plan_set - fra_set)
        if not_in_fra:
            print(f"  ⚠  {len(not_in_fra)} plans have no FRA result: "
                  f"{not_in_fra[:20]}" + (" ..." if len(not_in_fra) > 20 else ""))
        else:
            print(f"  ✓  All {n_fra} plan JSONs have a corresponding FRA result")
    results["fra_csv_count"] = n_fra

    # ── Combined baseline CSV ─────────────────────────────────────────────────
    print(f"\n[BASELINE COMBINED CSV]  {baseline_csv}")
    if baseline_csv.exists():
        df = pd.read_csv(baseline_csv)
        n_rows = len(df)
        dups   = df.duplicated(subset=["assignment_hash"]).sum() \
                 if "assignment_hash" in df.columns else "n/a (no hash col)"
        print(f"  Rows:       {n_rows:,}")
        print(f"  Columns:    {list(df.columns)}")
        print(f"  Duplicates: {dups}")
        if "dem_seats" in df.columns:
            print(f"  Dem seats:  mean={df['dem_seats'].mean():.3f}  "
                  f"std={df['dem_seats'].std():.3f}  "
                  f"range=[{int(df['dem_seats'].min())},{int(df['dem_seats'].max())}]")
        results["baseline_rows"] = n_rows
    else:
        print(f"  ⚠  File not found — run fra_analysis_job.sbatch first")
        results["baseline_rows"] = None

    # ── Combined FRA CSV ──────────────────────────────────────────────────────
    print(f"\n[FRA COMBINED CSV]  {fra_csv}")
    if fra_csv.exists():
        df = pd.read_csv(fra_csv)
        n_rows = len(df)
        print(f"  Rows:       {n_rows:,}")
        print(f"  Columns:    {list(df.columns)}")
        if "dem_seats" in df.columns:
            print(f"  Dem seats:  mean={df['dem_seats'].mean():.3f}  "
                  f"std={df['dem_seats'].std():.3f}  "
                  f"range=[{int(df['dem_seats'].min())},{int(df['dem_seats'].max())}]")
        results["fra_combined_rows"] = n_rows
    else:
        print(f"  ⚠  File not found — run fra_analysis_job.sbatch first")
        results["fra_combined_rows"] = None

    # ── Chain diagnostics (global duplicate summary) ──────────────────────────
    combined_diag = baseline_csv.parent / "chain_diagnostics_combined.json"
    if combined_diag.exists():
        batches = json.load(open(combined_diag))
        total_plans = sum(d.get("num_plans", 0) for d in batches)
        total_dupes = sum(d.get("duplicate_count", 0) for d in batches)
        dup_rate    = total_dupes / total_plans if total_plans else 0
        print(f"\n[CHAIN DIAGNOSTICS]  {len(batches)} batches")
        print(f"  Total plans:            {total_plans:,}")
        print(f"  Within-batch dupes:     {total_dupes:,}  ({dup_rate:.4%})")
        results["chain_diagnostic_batches"] = len(batches)
        results["within_batch_duplicates"]  = total_dupes

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  plan_N.json files:   {results.get('plan_json_count', '?'):>8,}")
    print(f"  fra_results_N.csv:   {results.get('fra_csv_count', '?'):>8,}")
    print(f"  baseline CSV rows:   {results.get('baseline_rows', 'not found'):>8}")
    print(f"  FRA combined rows:   {results.get('fra_combined_rows', 'not found'):>8}")
    print("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="Count and validate pipeline outputs")
    parser.add_argument("--plans-dir",    type=str, default=None)
    parser.add_argument("--fra-dir",      type=str, default=None)
    parser.add_argument("--baseline-csv", type=str, default=None)
    parser.add_argument("--fra-csv",      type=str, default=None)
    parser.add_argument("--expected",     type=int, default=10000,
                        help="Expected number of plans (default 10000)")
    args = parser.parse_args()

    base_dir = Path(__file__).parent.parent

    plans_dir    = Path(args.plans_dir)    if args.plans_dir    else base_dir / "outputs" / "plan_assignments"
    fra_dir      = Path(args.fra_dir)      if args.fra_dir      else base_dir / "outputs" / "fra"
    baseline_csv = Path(args.baseline_csv) if args.baseline_csv else base_dir / "outputs" / "analysis" / "baseline_ensemble_combined.csv"
    fra_csv      = Path(args.fra_csv)      if args.fra_csv      else base_dir / "outputs" / "analysis" / "fra_ensemble_combined.csv"

    count_outputs(plans_dir, fra_dir, baseline_csv, fra_csv, args.expected)


if __name__ == "__main__":
    main()
