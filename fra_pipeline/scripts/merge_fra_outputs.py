#!/usr/bin/env python3
"""
Merge FRA / Baseline Outputs

Consolidates per-batch CSV files produced by SLURM array tasks into a single
combined file.  Also performs global duplicate detection across all batches
using the assignment_hash column (written by run_baseline_simple.py).

Usage:
    # Merge baseline batch CSVs (baseline_ensemble_*_*.csv)
    python merge_fra_outputs.py \
        --fra-dir outputs/ \
        --output-file outputs/analysis/baseline_ensemble_combined.csv \
        --pattern "baseline_ensemble_*.csv"

    # Merge FRA per-plan CSVs (fra_results_*.csv)
    python merge_fra_outputs.py \
        --fra-dir outputs/fra \
        --output-file outputs/analysis/fra_ensemble_combined.csv \
        --pattern "fra_results_*.csv"

    # Merge per-batch plan-stats CSVs
    python merge_fra_outputs.py \
        --fra-dir outputs/analysis \
        --output-file outputs/analysis/fra_plan_stats_combined.csv \
        --pattern "fra_plan_stats_*.csv"
"""

import argparse
import os
from pathlib import Path
from io_utils import atomic_write_dataframe_csv

import pandas as pd


def collect_csvs(folder: Path, pattern: str = "*.csv") -> list:
    return sorted(folder.glob(pattern))


def merge_csvs(csv_files: list) -> pd.DataFrame:
    if not csv_files:
        raise FileNotFoundError(f"No CSV files matched in {csv_files}")

    frames = []
    for f in csv_files:
        print(f"[INFO] Reading {f}")
        frames.append(pd.read_csv(f))

    return pd.concat(frames, ignore_index=True)


def report_global_duplicates(merged: pd.DataFrame) -> dict:
    """
    Detect cross-batch duplicates using the assignment_hash column if present.

    Within-batch duplicates are already tracked per chain in run_baseline_simple.py.
    This function finds duplicates that appear in *different* batches — these are
    the ones the per-batch seen_hashes set cannot catch.

    Returns a dict with duplicate statistics (safe to embed in a manifest/report).
    """
    if "assignment_hash" not in merged.columns:
        print("[INFO] No 'assignment_hash' column found — skipping global duplicate check.")
        print("       Global duplicate detection requires run_baseline_simple.py ≥ v2.")
        return {"global_duplicate_check": "skipped", "reason": "no assignment_hash column"}

    total = len(merged)
    dup_mask = merged.duplicated(subset=["assignment_hash"], keep="first")
    dup_count = dup_mask.sum()
    dup_rate  = dup_count / total if total else 0.0

    dup_plan_ids = (
        merged.loc[dup_mask, "plan_id"].tolist()
        if "plan_id" in merged.columns else []
    )

    print(f"\n[GLOBAL DEDUP] Total plans:     {total:,}")
    print(f"[GLOBAL DEDUP] Unique plans:    {total - dup_count:,}")
    print(f"[GLOBAL DEDUP] Duplicate plans: {dup_count:,}  ({dup_rate:.4%})")
    if dup_plan_ids:
        sample = dup_plan_ids[:10]
        print(f"[GLOBAL DEDUP] Duplicate plan_ids (first 10): {sample}")

    return {
        "total_plans":        total,
        "unique_plans":       total - dup_count,
        "duplicate_count":    dup_count,
        "duplicate_rate":     round(dup_rate, 6),
        "duplicate_plan_ids": dup_plan_ids,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Merge per-batch CSV outputs and run global duplicate detection"
    )
    parser.add_argument("--fra-dir", required=True,
                        help="Directory containing the per-batch CSV files")
    parser.add_argument("--output-file", required=True,
                        help="Path for the merged output CSV")
    parser.add_argument("--pattern", default="*.csv",
                        help="Glob pattern for input files (default: *.csv)")
    parser.add_argument("--drop-global-dupes", action="store_true",
                        help="Drop cross-batch duplicate rows before writing output")
    args = parser.parse_args()

    fra_dir     = Path(args.fra_dir)
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    csv_files = collect_csvs(fra_dir, args.pattern)
    print(f"[INFO] Found {len(csv_files)} CSV files matching '{args.pattern}' in {fra_dir}")
    if not csv_files:
        raise SystemExit("[ERROR] No files found — check --fra-dir and --pattern")

    merged = merge_csvs(csv_files)
    print(f"[INFO] Merged rows before dedup: {len(merged):,}")

    dedup_stats = report_global_duplicates(merged)

    if args.drop_global_dupes and "assignment_hash" in merged.columns:
        before = len(merged)
        merged = merged.drop_duplicates(subset=["assignment_hash"], keep="first")
        print(f"[INFO] Dropped {before - len(merged):,} cross-batch duplicate rows.")

    # Atomic write via shared helper (unique temp path + fsync)
    atomic_write_dataframe_csv(output_file, merged)

    print(f"[INFO] Final merged rows: {len(merged):,}")
    print(f"[INFO] Output written to: {output_file}")

    # Print final dedup summary
    if isinstance(dedup_stats.get("duplicate_count"), int):
        d = dedup_stats
        print(f"\n{'='*50}")
        print(f"GLOBAL DUPLICATE SUMMARY")
        print(f"  Total plans:     {d['total_plans']:,}")
        print(f"  Unique plans:    {d['unique_plans']:,}")
        print(f"  Duplicates:      {d['duplicate_count']:,}  ({d['duplicate_rate']:.4%})")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
