#!/usr/bin/env python3
"""
Rerun Failed FRA Plans

Reads fra_failed_plans.csv (written by fra_gluing_algorithm.py) and re-processes
only the plans that previously failed.  Useful when a subset of plans fails due
to transient geometry or adjacency issues.

Usage:
    python rerun_failed_plans.py \
        --failed-csv outputs/analysis/fra_failed_plans.csv \
        --input      outputs/plan_assignments \
        --output     outputs/fra

    # Or specify a manual range instead of reading the CSV:
    python rerun_failed_plans.py \
        --start 42 --end 42 \
        --input outputs/plan_assignments \
        --output outputs/fra
"""

import argparse
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Make the shared library importable when run directly from the scripts/ dir
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from fra_gluing_algorithm import (
    load_shapefile,
    build_precinct_adjacency,
    process_single_plan,
)

try:
    import db as _db
except ImportError:
    _db = None


def collect_failed_ids(failed_csv: Path) -> list:
    """Return sorted list of plan IDs from fra_failed_plans.csv."""
    df = pd.read_csv(failed_csv)
    if "plan_id" not in df.columns:
        raise ValueError(f"'plan_id' column not found in {failed_csv}")
    return sorted(df["plan_id"].dropna().astype(int).tolist())


def main():
    parser = argparse.ArgumentParser(
        description="Re-process plans listed in fra_failed_plans.csv"
    )
    parser.add_argument(
        "--failed-csv", type=str, default=None,
        help="Path to fra_failed_plans.csv produced by fra_gluing_algorithm.py"
    )
    parser.add_argument(
        "--start", type=int, default=None,
        help="First plan ID to rerun (fallback if --failed-csv not given)"
    )
    parser.add_argument(
        "--end", type=int, default=None,
        help="Last plan ID to rerun (fallback if --failed-csv not given)"
    )
    parser.add_argument(
        "--input", type=str, required=True,
        help="Directory containing plan_N.json files"
    )
    parser.add_argument(
        "--output", type=str, required=True,
        help="Directory to write fra_results_N.csv and superdistrict_assignment_N.json"
    )
    parser.add_argument(
        "--use-db", action="store_true",
        help="Use PostgreSQL FOR UPDATE SKIP LOCKED to safely claim failed plans "
             "across concurrent SLURM workers.  Requires FRA_DB_DSN to be set."
    )
    args = parser.parse_args()

    # ── Determine which plan IDs to rerun ─────────────────────────────────────
    if args.use_db:
        # DB path: each worker atomically claims one plan at a time.
        # Multiple concurrent SLURM tasks can run this path without any
        # double-processing — FOR UPDATE SKIP LOCKED guarantees exactly-once
        # claiming even with N workers hitting the same failed-plans pool.
        if _db is None:
            print("[ERROR] --use-db requires the db module (psycopg2 not installed?)")
            sys.exit(1)
        if not _db._enabled():
            print("[ERROR] --use-db requires FRA_DB_DSN to be set")
            sys.exit(1)

        plan_dir   = Path(args.input)
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)

        script_dir = Path(__file__).parent
        base_dir   = script_dir.parent
        shp_path   = base_dir / "new_data" / "nc_2024_with_population.shp"
        if not shp_path.exists():
            print(f"[ERROR] Shapefile not found: {shp_path}")
            sys.exit(1)

        gdf          = load_shapefile(str(shp_path))
        precinct_adj = build_precinct_adjacency(gdf)
        target_sizes  = [5, 5, 4]
        num_districts = 14

        succeeded    = []
        still_failing = []
        claimed_count = 0

        print("[INFO] DB mode: claiming failed plans via FOR UPDATE SKIP LOCKED")
        while True:
            plan_num = _db.claim_next_failed_plan()
            if plan_num is None:
                break   # no more failed plans in the pool
            claimed_count += 1
            print(f"\n[RERUN] Plan {plan_num} ...", end=" ", flush=True)
            try:
                result = process_single_plan(
                    plan_num, gdf, precinct_adj, base_dir,
                    target_sizes, num_districts, verbose=False,
                    plan_dir_override=str(plan_dir),
                    output_dir_override=str(output_dir),
                )
                succeeded.append(plan_num)
                _db.mark_done(
                    plan_num,
                    dem_seats=result["dem_seats"],
                    rep_seats=result["rep_seats"],
                    attempts_used=result.get("attempts_used"),
                )
                print(f"✓  Dem {result['dem_seats']} / Rep {result['rep_seats']}")
            except Exception as e:
                still_failing.append((plan_num, str(e)))
                _db.mark_failed(plan_num, str(e), type(e).__name__)
                print(f"✗  {e}")

        print(f"\n{'='*60}")
        print(f"DB RERUN COMPLETE")
        print(f"  Plans claimed:   {claimed_count}")
        print(f"  Now succeeded:   {len(succeeded)}")
        print(f"  Still failing:   {len(still_failing)}")
        if still_failing:
            for pid, err in still_failing:
                print(f"  Plan {pid}: {err}")
            sys.exit(1)
        return

    # ── CSV / range path (original behaviour, unchanged) ─────────────────────
    if args.failed_csv:
        failed_csv = Path(args.failed_csv)
        if not failed_csv.exists():
            print(f"[ERROR] --failed-csv not found: {failed_csv}")
            sys.exit(1)
        plan_ids = collect_failed_ids(failed_csv)
        print(f"[INFO] Read {len(plan_ids)} failed plan IDs from {failed_csv}")
    elif args.start is not None and args.end is not None:
        plan_ids = list(range(args.start, args.end + 1))
        print(f"[INFO] Manual range: plans {args.start}–{args.end} "
              f"({len(plan_ids)} plans)")
    else:
        print("[ERROR] Provide --use-db, --failed-csv, or both --start and --end")
        sys.exit(1)

    if not plan_ids:
        print("[INFO] No plan IDs to rerun. Exiting.")
        return

    plan_dir   = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading plan JSONs from: {plan_dir}")
    print(f"[INFO] Writing FRA outputs to:  {output_dir}")
    print(f"[INFO] Plans to rerun: {plan_ids}")

    # ── Load shared data once ─────────────────────────────────────────────────
    script_dir = Path(__file__).parent
    base_dir   = script_dir.parent
    shp_path   = base_dir / "new_data" / "nc_2024_with_population.shp"

    if not shp_path.exists():
        print(f"[ERROR] Shapefile not found: {shp_path}")
        sys.exit(1)

    gdf          = load_shapefile(str(shp_path))
    precinct_adj = build_precinct_adjacency(gdf)

    target_sizes  = [5, 5, 4]
    num_districts = 14

    # ── Rerun each failed plan ────────────────────────────────────────────────
    succeeded = []
    still_failing = []

    for plan_num in plan_ids:
        print(f"\n[RERUN] Plan {plan_num} ...", end=" ", flush=True)
        try:
            result = process_single_plan(
                plan_num,
                gdf,
                precinct_adj,
                base_dir,
                target_sizes,
                num_districts,
                verbose=False,
                plan_dir_override=str(plan_dir),
                output_dir_override=str(output_dir),
            )
            succeeded.append(plan_num)
            print(f"✓  Dem {result['dem_seats']} / Rep {result['rep_seats']}  "
                  f"(attempts: {result.get('attempts_used', '?')})")
        except Exception as e:
            still_failing.append((plan_num, str(e)))
            print(f"✗  {e}")

    # ── Report ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"RERUN COMPLETE")
    print(f"  Attempted:      {len(plan_ids)}")
    print(f"  Now succeeded:  {len(succeeded)}")
    print(f"  Still failing:  {len(still_failing)}")

    if still_failing:
        print(f"\nStill-failing plan IDs: {[pf[0] for pf in still_failing]}")
        for pid, err in still_failing:
            print(f"  Plan {pid}: {err}")
        sys.exit(1)   # non-zero exit so SLURM/CI can detect residual failures


if __name__ == "__main__":
    main()
